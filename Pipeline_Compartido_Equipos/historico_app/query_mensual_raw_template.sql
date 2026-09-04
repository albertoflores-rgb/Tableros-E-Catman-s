-- ============================================================
-- query_mensual_raw_template.sql
-- Variante MENSUAL del historico_app de Abarrotes
-- (tablero_insights_com_abarrotes/historico_app/query_diario_raw_template.sql)
-- para el NEGOCIO COMPLETO: los 6 equipos de E-Catman + Abarrotes + las
-- 5 categorias "huerfanas" (mismo universo de 76 categorias que el
-- tablero "Total Departamentos" -- ver teams_config.all_cat_nbrs_universe()).
--
-- Diferencias contra la version diaria de Abarrotes:
--   1. Grano ANIO x MES x Item (SIN Club) -- ver nota de abajo sobre
--      por que se quito Club de este pull masivo.
--   2. Filtro de categoria parametrizado via @cat_filter (ARRAY<INT64>),
--      igual que query_item_total_template.sql -- UN SOLO archivo para
--      todo el negocio (76 categorias combinadas desde 03-sep-2026),
--      no copias por area (ver teams_config.py y pull_data.py/db.py
--      de esta mini-app).
--   3. Rango de fechas fijo 2025-01-01 -> hoy en UNA sola pasada (no
--      2 pulls separados TY/LY) -- alinear por Anio/Mes calendario es
--      trivial (ambos 2025 y 2026 tienen 12 meses, a diferencia del
--      Day_Offset que hacia falta para alinear rangos parciales por
--      dia). Costo dominado por el rango de fechas escaneado en las
--      tablas base, NO por cuantas categorias trae el filtro (mismo
--      insight que run_query_combined.py) -- combinar 76 categorias en
--      1 query es esencialmente gratis comparado con queries separados.
--   4. Costo/Precio de referencia (Costo_Unit_Snapshot / Precio_Venta_
--      Snapshot) agregado 03-sep-2026 para poder calcular margen
--      comercial en la mini-app -- ver cte_costo_item abajo.
--
-- POR QUE SIN CLUB (a diferencia de la version diaria de Abarrotes):
--   Primer intento SI incluia CLUB_NBR (paridad total con Abarrotes) y
--   casi tumba la maquina -- 66 categorias x 20 meses x ~186 clubs x
--   items produjo un dataframe de varios GB que se acercaba al limite
--   de RAM disponible (validado en vivo 01-sep-2026, se aborto a
--   tiempo). Abarrotes puede darse ese lujo porque son solo 6
--   categorias; aqui son 76 (13x mas). Por eso el nivel Tienda-Item de
--   esta mini-app NO sale de este parquet masivo -- se resuelve con un
--   query EN VIVO, chico y barato (1 solo item a la vez), ver
--   query_item_club_mensual_template.sql.
-- ============================================================

DECLARE date_ini DATE DEFAULT DATE '{DATE_INI}';
DECLARE date_fin DATE DEFAULT DATE '{DATE_FIN}';

WITH

cte_pos_diario AS (
  SELECT
    a.STORE_NBR,
    a.ITEM_NBR,
    d.gregorian_date,
    ( a.SAT_QTY * d.sat_mult + a.SUN_QTY * d.sun_mult
    + a.MON_QTY * d.mon_mult + a.TUE_QTY * d.tue_mult
    + a.WED_QTY * d.wed_mult + a.THU_QTY * d.thu_mult
    + a.FRI_QTY * d.fri_mult )                       AS piezas_dia,
    ( a.SAT_SALES_AMT * d.sat_mult + a.SUN_SALES_AMT * d.sun_mult
    + a.MON_SALES_AMT * d.mon_mult + a.TUE_SALES_AMT * d.tue_mult
    + a.WED_SALES_AMT * d.wed_mult + a.THU_SALES_AMT * d.thu_mult
    + a.FRI_SALES_AMT * d.fri_mult )                 AS pesos_dia
  FROM `wmt-edw-prod.MX_WC_VM.SKU_DLY_POS`        AS a
  INNER JOIN `wmt-edw-prod.MX_WM_VM.CALENDAR_DAY`  AS d ON a.WM_YR_WK = d.wm_yr_wk
  WHERE d.gregorian_date BETWEEN date_ini AND date_fin
),

cte_ventas_fisico_diario AS (
  SELECT
    v.gregorian_date  AS Fecha,
    b.Old_NBR         AS ITEM_NBR,
    SUM(v.piezas_dia) AS Venta_Pzas_Fisico,
    SUM(v.pesos_dia)  AS Venta_Pesos_Fisico
  FROM cte_pos_diario v
  INNER JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC` b ON v.ITEM_NBR = b.ITEM_NBR
  GROUP BY v.gregorian_date, b.Old_NBR
  HAVING SUM(v.piezas_dia) <> 0 OR SUM(v.pesos_dia) <> 0
),

cte_ventas_com_diario AS (
  SELECT
    DATE(s.sales_order_detail_order_created_date)                  AS Fecha,
    SAFE_CAST(s.sales_order_detail_item_id_short AS INT64)          AS ITEM_NBR,
    SUM(s.sales_order_detail_commercial_sale_qty_base)                 AS Venta_Pzas_Com,
    SUM(s.sales_order_detail_net_paid_orders_wo_shipping_amount_1)     AS Venta_Pesos_Com
  FROM `wmt-mx-dl-controlledmgzn-prod.ecom.Sams_Ventas` AS s
  WHERE
    DATE(s.sales_order_detail_order_created_date) BETWEEN date_ini AND date_fin
    AND s.sales_order_detail_commercial_sale_qty_base > 0
    AND s.sales_order_detail_item_id_short IS NOT NULL
  GROUP BY
    DATE(s.sales_order_detail_order_created_date),
    SAFE_CAST(s.sales_order_detail_item_id_short AS INT64)
),

cte_ventas_diaria AS (
  SELECT
    COALESCE(f.Fecha, c.Fecha)         AS Fecha,
    COALESCE(f.ITEM_NBR, c.ITEM_NBR)   AS ITEM_NBR,
    COALESCE(f.Venta_Pzas_Fisico, 0)   AS Venta_Pzas_Fisico,
    COALESCE(f.Venta_Pesos_Fisico, 0)  AS Venta_Pesos_Fisico,
    COALESCE(c.Venta_Pzas_Com, 0)      AS Venta_Pzas_Com,
    COALESCE(c.Venta_Pesos_Com, 0)     AS Venta_Pesos_Com
  FROM cte_ventas_fisico_diario f
  FULL OUTER JOIN cte_ventas_com_diario c
    ON  f.Fecha    = c.Fecha
    AND f.ITEM_NBR = c.ITEM_NBR
),

-- Colapsa diario -> mensual (SIN Club) ANTES de unir con dimensiones.
cte_ventas_mensual AS (
  SELECT
    EXTRACT(YEAR FROM Fecha)   AS Anio,
    EXTRACT(MONTH FROM Fecha)  AS Mes,
    ITEM_NBR,
    SUM(Venta_Pzas_Fisico)     AS Venta_Pzas_Fisico,
    SUM(Venta_Pesos_Fisico)    AS Venta_Pesos_Fisico,
    SUM(Venta_Pzas_Com)        AS Venta_Pzas_Com,
    SUM(Venta_Pesos_Com)       AS Venta_Pesos_Com
  FROM cte_ventas_diaria
  GROUP BY Anio, Mes, ITEM_NBR
),

cte_dim_item AS (
  SELECT DISTINCT
    b.Old_NBR                AS ITEM_NBR,
    b.PRIMARY_DESC            AS ITEM_DESC_1,
    b.CATEGORY_NBR            AS CAT_NBR,
    cat.Categoria             AS CAT_NOMBRE,
    b.SUB_CATEGORY_NBR        AS SUBCAT_NBR,
    cat.Sub_Categoria         AS SUBCAT_NOMBRE
  FROM `wmt-edw-prod.MX_WC_VM.ITEM_DESC` b
  LEFT JOIN `wmt-mx-dl-controlledmgzn-prod.Black_Bird.Catalogo_Cat_Subcat` AS cat
    ON  SAFE_CAST(cat.Categoria_NBR AS INT64) = b.CATEGORY_NBR
    AND SAFE_CAST(cat.Sub_Categoria_Code AS INT64) = b.SUB_CATEGORY_NBR
  WHERE b.TYPE_CODE IN ('22', '20')
),

-- Costo/Precio de referencia (snapshot ACTUAL, no historico -- MDSE_INVENTORY
-- no guarda historia de costo por mes, solo el estado de hoy). Se aplica
-- como constante de referencia a todos los meses del mismo item, igual que
-- ya hacen los tableros de equipo (query_item_total_template.sql, Costo_Unit
-- / Precio_Venta). Query chico y barato -- MDSE_INVENTORY no se filtra por
-- fecha, solo por item/categoria, asi que no escala con el rango de dias.
cte_costo_item AS (
  SELECT
    b.Old_NBR           AS ITEM_NBR,
    AVG(a.UNIT_COST)    AS Costo_Unit_Snapshot,
    AVG(a.UNIT_SELL)    AS Precio_Venta_Snapshot
  FROM `wmt-edw-prod.MX_WC_VM.MDSE_INVENTORY` a
  JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC` b ON a.ITEM_NBR = b.ITEM_NBR
  WHERE b.CATEGORY_NBR IN UNNEST(@cat_filter)
  GROUP BY b.Old_NBR
)

-- ============================================================
-- Consulta final: grano Anio x Mes x Item (SIN Club) + dims + costo/precio.
-- ============================================================
SELECT
  T1.Anio, T1.Mes,
  T2.CAT_NBR, T2.CAT_NOMBRE, T2.SUBCAT_NBR, T2.SUBCAT_NOMBRE,
  T1.ITEM_NBR, T2.ITEM_DESC_1,
  T1.Venta_Pzas_Fisico, T1.Venta_Pesos_Fisico,
  T1.Venta_Pzas_Com, T1.Venta_Pesos_Com,
  T4.Costo_Unit_Snapshot, T4.Precio_Venta_Snapshot
FROM cte_ventas_mensual AS T1
JOIN cte_dim_item AS T2
  ON T1.ITEM_NBR = T2.ITEM_NBR
LEFT JOIN cte_costo_item AS T4
  ON T1.ITEM_NBR = T4.ITEM_NBR
WHERE T2.CAT_NBR IN UNNEST(@cat_filter)

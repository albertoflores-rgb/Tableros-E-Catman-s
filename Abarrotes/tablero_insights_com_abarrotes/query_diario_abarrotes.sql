-- ============================================================
-- query_diario_abarrotes.sql
-- Copia derivada de "SAMS - Venta e Inventarios Ecatman - Diario
-- TY vs LY.sql" (Respaldo_Querys/saved_queries/) para el tab
-- "Histórico Diario" del tablero_insights_com_abarrotes.
--
-- QUÉ CAMBIA vs el original:
--   1) date_ini/date_fin fijos a 2026-01-01 -> ayer (en vez del
--      default de "ultimos 30 dias" del archivo original).
--   2) Filtro de categorias activado: 41,43,46,49,53,68 (mismo
--      set que el resto de tableros de Abarrotes en este proyecto).
--   3) El SELECT final agrega por Fecha x Categoria x Subcategoria
--      x Item -- SIN club/tienda -- porque este tab solo cubre los
--      niveles Categoria/Subcategoria/Item (el nivel Tienda-Item
--      quedo pendiente de decision de arquitectura por su volumen:
--      15.3M filas a grano diario x club x item, medido con
--      bigquery-explorer antes de construir esto). Se quito tambien
--      el bloque de inventario (snapshot puntual, no aporta a una
--      vista de TENDENCIA historica).
--   4) NO se toco el archivo original en Respaldo_Querys -- este es
--      una copia adaptada, mismo patron que query_item_total_abarrotes.sql.
-- ============================================================

DECLARE date_ini DATE DEFAULT DATE '2026-01-01';
DECLARE date_fin DATE DEFAULT DATE_SUB(CURRENT_DATE('America/Mexico_City'), INTERVAL 1 DAY);

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
    v.STORE_NBR       AS CLUB_NBR,
    b.Old_NBR         AS ITEM_NBR,
    SUM(v.piezas_dia) AS Venta_Pzas_Fisico,
    SUM(v.pesos_dia)  AS Venta_Pesos_Fisico
  FROM cte_pos_diario v
  INNER JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC` b ON v.ITEM_NBR = b.ITEM_NBR
  GROUP BY v.gregorian_date, v.STORE_NBR, b.Old_NBR
  HAVING SUM(v.piezas_dia) <> 0 OR SUM(v.pesos_dia) <> 0
),

cte_ventas_com_diario AS (
  SELECT
    DATE(s.sales_order_detail_order_created_date)                  AS Fecha,
    SAFE_CAST(s.sales_order_detail_assigned_store_nbr AS INT64)     AS CLUB_NBR,
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
    SAFE_CAST(s.sales_order_detail_assigned_store_nbr AS INT64),
    SAFE_CAST(s.sales_order_detail_item_id_short AS INT64)
),

cte_ventas_diaria AS (
  SELECT
    COALESCE(f.Fecha, c.Fecha)         AS Fecha,
    COALESCE(f.CLUB_NBR, c.CLUB_NBR)   AS CLUB_NBR,
    COALESCE(f.ITEM_NBR, c.ITEM_NBR)   AS ITEM_NBR,
    COALESCE(f.Venta_Pzas_Fisico, 0)   AS Venta_Pzas_Fisico,
    COALESCE(f.Venta_Pesos_Fisico, 0)  AS Venta_Pesos_Fisico,
    COALESCE(c.Venta_Pzas_Com, 0)      AS Venta_Pzas_Com,
    COALESCE(c.Venta_Pesos_Com, 0)     AS Venta_Pesos_Com
  FROM cte_ventas_fisico_diario f
  FULL OUTER JOIN cte_ventas_com_diario c
    ON  f.Fecha    = c.Fecha
    AND f.CLUB_NBR = c.CLUB_NBR
    AND f.ITEM_NBR = c.ITEM_NBR
),

-- Dimensiones (Cat/Subcat/Item) -- SIN el bloque de inventario, que es
-- un snapshot puntual y no aporta nada a una vista de tendencia historica.
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
)

-- ============================================================
-- Consulta final: agregado Fecha x Categoria x Subcategoria x Item
-- (SIN club/tienda -- eso es el nivel Tienda-Item, pendiente).
-- ============================================================
SELECT
  T1.Fecha,
  T2.CAT_NBR, T2.CAT_NOMBRE, T2.SUBCAT_NBR, T2.SUBCAT_NOMBRE,
  T1.ITEM_NBR, T2.ITEM_DESC_1,
  SUM(T1.Venta_Pzas_Fisico)  AS Venta_Pzas_Fisico,
  SUM(T1.Venta_Pesos_Fisico) AS Venta_Pesos_Fisico,
  SUM(T1.Venta_Pzas_Com)     AS Venta_Pzas_Com,
  SUM(T1.Venta_Pesos_Com)    AS Venta_Pesos_Com
FROM cte_ventas_diaria AS T1
JOIN cte_dim_item AS T2
  ON T1.ITEM_NBR = T2.ITEM_NBR
WHERE T2.CAT_NBR IN (41, 43, 46, 49, 53, 68)
GROUP BY T1.Fecha, T2.CAT_NBR, T2.CAT_NOMBRE, T2.SUBCAT_NBR, T2.SUBCAT_NOMBRE, T1.ITEM_NBR, T2.ITEM_DESC_1
ORDER BY T1.Fecha, T1.ITEM_NBR

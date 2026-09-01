-- ============================================================
-- query_item_total_salud_bienestar.sql
-- Departamento : Salud y Bienestar
-- Owner        : Estef
-- Generado     : 01-sep-2026 -- via catman_equipos/generate_department_queries.py
--
-- NO EDITAR ESTE ARCHIVO A MANO. Se genera automaticamente desde
-- catman_equipos/query_item_total_template.sql + catman_equipos/teams_config.py
-- (fuente de verdad de las categorias). Si necesitas ajustar categorias,
-- edita teams_config.py en el workspace principal y vuelve a correr
-- generate_department_queries.py -- este archivo se pisa con la version
-- correcta cada vez.
--
-- Este es un query LITERAL (categorias ya escritas abajo, sin
-- parametros) para que se pueda copiar y pegar directo en la consola
-- de BigQuery. Es funcionalmente identico al query parametrizado que
-- usa la automatizacion (catman_equipos/query_item_total_template.sql
-- con @cat_filter = [2, 4, 8, 13, 27, 47, 54]).
-- ============================================================

DECLARE fecha_ayer  DATE   DEFAULT DATE_SUB(CURRENT_DATE('America/Mexico_City'), INTERVAL 1 DAY);
DECLARE anio_actual INT64  DEFAULT EXTRACT(YEAR FROM fecha_ayer);
DECLARE anio_pasado INT64  DEFAULT anio_actual - 1;

-- ---- Momento 1: YTD (1-ene -> ayer) ----
DECLARE ytd_ty_ini DATE DEFAULT DATE(anio_actual, 1, 1);
DECLARE ytd_ty_fin DATE DEFAULT fecha_ayer;
DECLARE ytd_ly_ini DATE DEFAULT DATE(anio_pasado, 1, 1);
DECLARE ytd_ly_fin DATE DEFAULT DATE_SUB(fecha_ayer, INTERVAL 1 YEAR);

-- ---- Momento 2: MTD (día 1 del mes -> ayer) ----
DECLARE mtd_ty_ini DATE DEFAULT DATE_TRUNC(fecha_ayer, MONTH);
DECLARE mtd_ty_fin DATE DEFAULT fecha_ayer;
DECLARE mtd_ly_ini DATE DEFAULT DATE_SUB(DATE_TRUNC(fecha_ayer, MONTH), INTERVAL 1 YEAR);
DECLARE mtd_ly_fin DATE DEFAULT DATE_SUB(fecha_ayer, INTERVAL 1 YEAR);

-- ---- Momento 3: Últimos 7 días (ayer-6 -> ayer) ----
DECLARE l7d_ty_ini DATE DEFAULT DATE_SUB(fecha_ayer, INTERVAL 6 DAY);
DECLARE l7d_ty_fin DATE DEFAULT fecha_ayer;
-- LY = mismas fechas, un año atrás (mismo criterio que v3.0)
DECLARE l7d_ly_ini DATE DEFAULT DATE_SUB(l7d_ty_ini, INTERVAL 1 YEAR);
DECLARE l7d_ly_fin DATE DEFAULT DATE_SUB(l7d_ty_fin, INTERVAL 1 YEAR);

-- ---- Momento 4: Evento "A la Mexicana" (9-sep -> 16-sep-2026) ----
-- Igual que en Abarrotes: fechas FIJAS de evento, no rolling. LY =
-- mismas fechas calendario -1 año. Se deja disponible para las 6 areas
-- nuevas por si tambien les interesa medir el impacto del evento, pero
-- NO esta forzado en ninguna vista todavia -- cada area decide si lo
-- usa cuando armemos su pestaña de tablero.
DECLARE amx_ty_ini DATE DEFAULT DATE(2026, 9, 9);
DECLARE amx_ty_fin DATE DEFAULT DATE(2026, 9, 16);
DECLARE amx_ly_ini DATE DEFAULT DATE_SUB(amx_ty_ini, INTERVAL 1 YEAR);
DECLARE amx_ly_fin DATE DEFAULT DATE_SUB(amx_ty_fin, INTERVAL 1 YEAR);

-- Rango global: cubre los 8 sub-rangos de arriba en una sola pasada.
DECLARE date_ini DATE DEFAULT ytd_ly_ini;
DECLARE date_fin DATE DEFAULT fecha_ayer;

WITH

-- ------------------------------------------------------------
-- CTE 1: POS físico diario — idéntico a v3.0.
-- ------------------------------------------------------------
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

-- ------------------------------------------------------------
-- CTE 2: Ventas FÍSICAS agregadas SOLO por Ítem (sin Club) en
--   los 4 momentos TY+LY.
-- ------------------------------------------------------------
cte_ventas_fisico_item AS (
  SELECT
    b.Old_NBR AS ITEM_NBR,

    -- YTD
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN ytd_ty_ini AND ytd_ty_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_YTD,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN ytd_ty_ini AND ytd_ty_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_YTD,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN ytd_ly_ini AND ytd_ly_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_YTDLY,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN ytd_ly_ini AND ytd_ly_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_YTDLY,

    -- MTD
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN mtd_ty_ini AND mtd_ty_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_MTD,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN mtd_ty_ini AND mtd_ty_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_MTD,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN mtd_ly_ini AND mtd_ly_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_MTDLY,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN mtd_ly_ini AND mtd_ly_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_MTDLY,

    -- Ultimos 7 dias
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN l7d_ty_ini AND l7d_ty_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_L7D,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN l7d_ty_ini AND l7d_ty_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_L7D,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN l7d_ly_ini AND l7d_ly_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_L7DLY,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN l7d_ly_ini AND l7d_ly_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_L7DLY,

    -- Evento A la Mexicana (9-16 sep)
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN amx_ty_ini AND amx_ty_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_AMX,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN amx_ty_ini AND amx_ty_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_AMX,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN amx_ly_ini AND amx_ly_fin THEN v.piezas_dia END), 0) AS Piso_Pzas_AMXLY,
    COALESCE(SUM(CASE WHEN v.gregorian_date BETWEEN amx_ly_ini AND amx_ly_fin THEN v.pesos_dia  END), 0) AS Piso_Pesos_AMXLY

  FROM cte_pos_diario v
  INNER JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC` b ON v.ITEM_NBR = b.ITEM_NBR
  GROUP BY b.Old_NBR
),

-- ------------------------------------------------------------
-- CTE 3: .com — filas base acotadas al rango global.
-- ------------------------------------------------------------
cte_com_raw AS (
  SELECT
    DATE(s.sales_order_detail_order_created_date)              AS Fecha,
    SAFE_CAST(s.sales_order_detail_item_id_short AS INT64)      AS ITEM_NBR,
    s.sales_order_detail_commercial_sale_qty_base               AS Piezas,
    s.sales_order_detail_net_paid_orders_wo_shipping_amount_1   AS Pesos,
    s.sales_order_detail_order_nbr                              AS Orden_Nbr,
    s.sales_order_detail_membership_nbr                         AS Membresia_Nbr
  FROM `wmt-mx-dl-controlledmgzn-prod.ecom.Sams_Ventas` AS s
  WHERE
    DATE(s.sales_order_detail_order_created_date) BETWEEN date_ini AND date_fin
    AND s.sales_order_detail_commercial_sale_qty_base > 0        -- excluir devoluciones / reversos
    AND s.sales_order_detail_item_id_short IS NOT NULL           -- excluir ghost records
),

-- ------------------------------------------------------------
-- CTE 4: .com agregado SOLO por Ítem (sin Club) en los 4 momentos.
-- ------------------------------------------------------------
cte_ventas_com_item AS (
  SELECT
    ITEM_NBR,

    -- YTD
    COALESCE(SUM(CASE WHEN Fecha BETWEEN ytd_ty_ini AND ytd_ty_fin THEN Piezas END), 0)              AS Com_Pzas_YTD,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN ytd_ty_ini AND ytd_ty_fin THEN Pesos  END), 0)              AS Com_Pesos_YTD,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN ytd_ty_ini AND ytd_ty_fin THEN Orden_Nbr END)             AS Ordenes_Com_YTD,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN ytd_ty_ini AND ytd_ty_fin THEN Membresia_Nbr END)         AS Numero_Socios_YTD,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN ytd_ly_ini AND ytd_ly_fin THEN Piezas END), 0)              AS Com_Pzas_YTDLY,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN ytd_ly_ini AND ytd_ly_fin THEN Pesos  END), 0)              AS Com_Pesos_YTDLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN ytd_ly_ini AND ytd_ly_fin THEN Orden_Nbr END)             AS Ordenes_Com_YTDLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN ytd_ly_ini AND ytd_ly_fin THEN Membresia_Nbr END)         AS Numero_Socios_YTDLY,

    -- MTD
    COALESCE(SUM(CASE WHEN Fecha BETWEEN mtd_ty_ini AND mtd_ty_fin THEN Piezas END), 0)              AS Com_Pzas_MTD,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN mtd_ty_ini AND mtd_ty_fin THEN Pesos  END), 0)              AS Com_Pesos_MTD,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN mtd_ty_ini AND mtd_ty_fin THEN Orden_Nbr END)             AS Ordenes_Com_MTD,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN mtd_ty_ini AND mtd_ty_fin THEN Membresia_Nbr END)         AS Numero_Socios_MTD,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN mtd_ly_ini AND mtd_ly_fin THEN Piezas END), 0)              AS Com_Pzas_MTDLY,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN mtd_ly_ini AND mtd_ly_fin THEN Pesos  END), 0)              AS Com_Pesos_MTDLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN mtd_ly_ini AND mtd_ly_fin THEN Orden_Nbr END)             AS Ordenes_Com_MTDLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN mtd_ly_ini AND mtd_ly_fin THEN Membresia_Nbr END)         AS Numero_Socios_MTDLY,

    -- Ultimos 7 dias
    COALESCE(SUM(CASE WHEN Fecha BETWEEN l7d_ty_ini AND l7d_ty_fin THEN Piezas END), 0)              AS Com_Pzas_L7D,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN l7d_ty_ini AND l7d_ty_fin THEN Pesos  END), 0)              AS Com_Pesos_L7D,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN l7d_ty_ini AND l7d_ty_fin THEN Orden_Nbr END)             AS Ordenes_Com_L7D,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN l7d_ty_ini AND l7d_ty_fin THEN Membresia_Nbr END)         AS Numero_Socios_L7D,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN l7d_ly_ini AND l7d_ly_fin THEN Piezas END), 0)              AS Com_Pzas_L7DLY,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN l7d_ly_ini AND l7d_ly_fin THEN Pesos  END), 0)              AS Com_Pesos_L7DLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN l7d_ly_ini AND l7d_ly_fin THEN Orden_Nbr END)             AS Ordenes_Com_L7DLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN l7d_ly_ini AND l7d_ly_fin THEN Membresia_Nbr END)         AS Numero_Socios_L7DLY,

    -- Evento A la Mexicana (9-16 sep)
    COALESCE(SUM(CASE WHEN Fecha BETWEEN amx_ty_ini AND amx_ty_fin THEN Piezas END), 0)              AS Com_Pzas_AMX,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN amx_ty_ini AND amx_ty_fin THEN Pesos  END), 0)              AS Com_Pesos_AMX,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN amx_ty_ini AND amx_ty_fin THEN Orden_Nbr END)             AS Ordenes_Com_AMX,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN amx_ty_ini AND amx_ty_fin THEN Membresia_Nbr END)         AS Numero_Socios_AMX,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN amx_ly_ini AND amx_ly_fin THEN Piezas END), 0)              AS Com_Pzas_AMXLY,
    COALESCE(SUM(CASE WHEN Fecha BETWEEN amx_ly_ini AND amx_ly_fin THEN Pesos  END), 0)              AS Com_Pesos_AMXLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN amx_ly_ini AND amx_ly_fin THEN Orden_Nbr END)             AS Ordenes_Com_AMXLY,
    COUNT(DISTINCT CASE WHEN Fecha BETWEEN amx_ly_ini AND amx_ly_fin THEN Membresia_Nbr END)         AS Numero_Socios_AMXLY

  FROM cte_com_raw
  GROUP BY ITEM_NBR
),

-- ------------------------------------------------------------
-- CTE 5: Inventario ÍTEM TOTAL — copiado TAL CUAL de
--   "SAMS - Inventario Total Item.sql" (misma lógica, mismos
--   joins, mismos nombres de columna), solo envuelto en CTE.
-- ------------------------------------------------------------
cte_inventario_item AS (
  SELECT
    -- ── Ítem ────────────────────────────────────────────────
    b.Old_NBR                                               AS Item_Nbr,
    b.UPC                                                   AS UPC,
    b.PRIMARY_DESC                                          AS Item_Desc_1,
    b.SECONDARY_DESC                                        AS Item_Desc_2,
    e.DIRECCION                                             AS Direccion,
    e.DIVISION                                              AS Departamento,
    b.CATEGORY_NBR                                          AS Cat_Nbr,
    e.CATDESC                                               AS Cat_Desc,
    b.SUB_CATEGORY_NBR                                      AS Sub_Cat_Nbr,
    f.Sub_Categoria                                         AS Sub_Cat_Desc,
    f.Cat_SubCat                                            AS Cat_Sub_Cat,
    b.TYPE_CODE                                             AS Tipo,
    b.Status_Code                                           AS Status,
    b.VENDOR_NAME                                           AS Proveedor,
    CAST(b.VENDOR_NBR AS NUMERIC) * 1000
      + CAST(b.VENDOR_NBR_DEPT AS NUMERIC) * 10
      + CAST(b.VENDOR_NBR_SEQ  AS NUMERIC)                 AS Vendor_Nbr,

    -- ── Resurtido ────────────────────────────────────────────
    e.COMPRADOR                                             AS Comrpador,
    e.GERENTE                                               AS Gerente_Resurtido,
    e.RESURTIDOR                                            AS Resurtidor,
    b.EFFECTIVE_DATE                                        AS IED,

    -- ── Inventario (split por tipo de tienda) ────────────────
    COALESCE(SUM(CASE WHEN(g.Tipo_Tienda = "Club") THEN (a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY) END) , 0 ) AS OHQty_Clubes,
    COALESCE(SUM(CASE WHEN(g.Tipo_Tienda = "FC MX") THEN (a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY) END) , 0) AS OHQty_FC_MX,
    COALESCE(SUM(CASE WHEN(g.Tipo_Tienda = "FC MTY") THEN (a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY) END) , 0) AS OHQty_FC_MTY,
    COALESCE(COUNT((CASE WHEN(g.tipo_tienda = "Club") THEN a.club_nbr END)), 0) AS Club_con_Inventario,
    COALESCE(COUNT((CASE WHEN(g.tipo_tienda = "Club" and a.ONSITE_ONHAND_QTY > 0) THEN a.club_nbr END)), 0) AS Club_con_Inventario_Piso,

    -- ── Fechas de vigencia ──────────────────────────────────
    -- Fecha_Inicio/Fecha_Fin NO se incluyen (mismo criterio que
    -- Abarrotes v4.2 -- generaban filas duplicadas por item cuando
    -- distintos clubes tenian fechas de alta/baja distintas).
    CURRENT_DATE('America/Mexico_City')                     AS Fecha_Corte,

    -- ── Valuación ───────────────────────────────────────────
    avg(a.UNIT_COST)                                             AS Costo_Unit,
    avg(a.UNIT_SELL)                                             AS Precio_Venta,
    COALESCE(SUM(CASE WHEN(g.Tipo_Tienda = "Club") THEN ((a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY) * a.UNIT_SELL) END) , 0 ) AS OHQty_Clubes_MXN,
    COALESCE(SUM(CASE WHEN(g.Tipo_Tienda = "FC MX") THEN ((a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY) * a.UNIT_SELL) END) , 0) AS OHMXN_FC_MX,
    COALESCE(SUM(CASE WHEN(g.Tipo_Tienda = "FC MTY") THEN ((a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY) * a.UNIT_SELL) END) , 0) AS OHMXN_FC_MTY,

    -- Semaforo con texto plano (sin emoji, por politica del proyecto).
    CASE
      WHEN sum((a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY)) = 0
                                                  THEN 'OOS'
      WHEN sum((a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY)) BETWEEN 1  AND 5
                                                  THEN 'Crítico (<6)'
      WHEN sum((a.ONSITE_ONHAND_QTY + a.OFFSITE_ONHAND_QTY)) BETWEEN 6  AND 20
                                                  THEN 'Bajo (6-20)'
      ELSE                                             'OK'
    END                                                     AS Semaforo_OH

  FROM `wmt-edw-prod.MX_WC_VM.MDSE_INVENTORY`  AS a
  LEFT JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC`       AS b ON  (a.ITEM_NBR = b.ITEM_NBR)
  LEFT JOIN `wmt-edw-sandbox.Black_Bird.Catalogo_CatID` AS c ON (b.CATEGORY_NBR = c.cat_id)
  LEFT JOIN wmt-edw-prod.MX_WC_VM.STORE_INFO AS d ON (a.CLUB_NBR = d.store_NBR)
  LEFT JOIN `wmt-edw-sandbox.Black_Bird.Catalogo_Cat_Compradores` AS e ON (b.CATEGORY_NBR = e.DEPT_NBR)
  LEFT JOIN `wmt-edw-sandbox.Black_Bird.Catalogo_Cat_Subcat` AS f ON (CONCAT (CAST(b.CATEGORY_NBR AS STRING),"-",CAST(b.Sub_CATEGORY_NBR AS STRING)) = f.Cat_SubCat)
  LEFT JOIN `wmt-edw-sandbox.Black_Bird.Catalogo_Clubes` AS g on (a.club_nbr = g.club_nbr)

  WHERE a.club_nbr not in (5808 , 6269, 6389,7101,7573,7475,8103,8691)
  AND g.tipo_tienda not in("Staff","Ex CA","Cedis Devoluciones","Transpo","WMG","Medimart","Import","Prueba")

  GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19
)

-- ============================================================
-- Consulta final: Inventario ÍTEM TOTAL + Venta Física + Venta
-- .com, con los 4 momentos (YTD/MTD/L7D/AMX) TY+LY y % de crecimiento,
-- TODO agregado a nivel Ítem (sin desglose por Club).
--   T2 (inventario item) es la base → RIGHT JOIN con T1 (físico)
--   T3 (.com) se agrega con LEFT JOIN sobre la misma clave
--   El filtro de categorias es @cat_filter -- ver teams_config.py
-- ============================================================
SELECT
  -- ── Identificadores / dimensiones de Ítem (de T2) ────────
  T2.Item_Nbr, T2.UPC, T2.Item_Desc_1, T2.Item_Desc_2,
  T2.Direccion, T2.Departamento, T2.Cat_Nbr, T2.Cat_Desc,
  T2.Sub_Cat_Nbr, T2.Sub_Cat_Desc, T2.Cat_Sub_Cat,
  T2.Tipo, T2.Status, T2.Proveedor, T2.Vendor_Nbr,
  T2.Comrpador, T2.Gerente_Resurtido, T2.Resurtidor, T2.IED,

  -- ── Inventario ítem total (snapshot actual) ──────────────
  T2.OHQty_Clubes, T2.OHQty_FC_MX, T2.OHQty_FC_MTY,
  T2.Club_con_Inventario, T2.Club_con_Inventario_Piso,
  T2.Fecha_Corte,
  T2.Costo_Unit, T2.Precio_Venta,
  T2.OHQty_Clubes_MXN, T2.OHMXN_FC_MX, T2.OHMXN_FC_MTY,
  T2.Semaforo_OH,

  -- ══ MOMENTO 1: YTD (1-ene -> ayer) ═══════════════════════
  COALESCE(T1.Piso_Pzas_YTD, 0)         AS Piso_Pzas_YTD,
  COALESCE(T1.Piso_Pesos_YTD, 0)        AS Piso_Pesos_YTD,
  COALESCE(T3.Com_Pzas_YTD, 0)          AS Com_Pzas_YTD,
  COALESCE(T3.Com_Pesos_YTD, 0)         AS Com_Pesos_YTD,
  COALESCE(T3.Ordenes_Com_YTD, 0)       AS Ordenes_Com_YTD,
  COALESCE(T3.Numero_Socios_YTD, 0)     AS Numero_Socios_YTD,
  (COALESCE(T1.Piso_Pzas_YTD,0)  + COALESCE(T3.Com_Pzas_YTD,0))   AS Total_Pzas_YTD,
  (COALESCE(T1.Piso_Pesos_YTD,0) + COALESCE(T3.Com_Pesos_YTD,0))  AS Total_Pesos_YTD,

  COALESCE(T1.Piso_Pzas_YTDLY, 0)       AS Piso_Pzas_YTDLY,
  COALESCE(T1.Piso_Pesos_YTDLY, 0)      AS Piso_Pesos_YTDLY,
  COALESCE(T3.Com_Pzas_YTDLY, 0)        AS Com_Pzas_YTDLY,
  COALESCE(T3.Com_Pesos_YTDLY, 0)       AS Com_Pesos_YTDLY,
  COALESCE(T3.Ordenes_Com_YTDLY, 0)     AS Ordenes_Com_YTDLY,
  COALESCE(T3.Numero_Socios_YTDLY, 0)   AS Numero_Socios_YTDLY,
  (COALESCE(T1.Piso_Pzas_YTDLY,0)  + COALESCE(T3.Com_Pzas_YTDLY,0))  AS Total_Pzas_YTDLY,
  (COALESCE(T1.Piso_Pesos_YTDLY,0) + COALESCE(T3.Com_Pesos_YTDLY,0)) AS Total_Pesos_YTDLY,

  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pzas_YTD,0) - COALESCE(T1.Piso_Pzas_YTDLY,0),
    NULLIF(COALESCE(T1.Piso_Pzas_YTDLY,0), 0)
  ) AS Crecimiento_Piso_Pzas_YTD,
  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pesos_YTD,0) - COALESCE(T1.Piso_Pesos_YTDLY,0),
    NULLIF(COALESCE(T1.Piso_Pesos_YTDLY,0), 0)
  ) AS Crecimiento_Piso_Pesos_YTD,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pzas_YTD,0) - COALESCE(T3.Com_Pzas_YTDLY,0),
    NULLIF(COALESCE(T3.Com_Pzas_YTDLY,0), 0)
  ) AS Crecimiento_Com_Pzas_YTD,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pesos_YTD,0) - COALESCE(T3.Com_Pesos_YTDLY,0),
    NULLIF(COALESCE(T3.Com_Pesos_YTDLY,0), 0)
  ) AS Crecimiento_Com_Pesos_YTD,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pzas_YTD,0) + COALESCE(T3.Com_Pzas_YTD,0)) - (COALESCE(T1.Piso_Pzas_YTDLY,0) + COALESCE(T3.Com_Pzas_YTDLY,0)),
    NULLIF(COALESCE(T1.Piso_Pzas_YTDLY,0) + COALESCE(T3.Com_Pzas_YTDLY,0), 0)
  ) AS Crecimiento_Pzas_YTD,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pesos_YTD,0) + COALESCE(T3.Com_Pesos_YTD,0)) - (COALESCE(T1.Piso_Pesos_YTDLY,0) + COALESCE(T3.Com_Pesos_YTDLY,0)),
    NULLIF(COALESCE(T1.Piso_Pesos_YTDLY,0) + COALESCE(T3.Com_Pesos_YTDLY,0), 0)
  ) AS Crecimiento_Pesos_YTD,

  -- ══ MOMENTO 2: MTD (día 1 del mes -> ayer) ═══════════════
  COALESCE(T1.Piso_Pzas_MTD, 0)         AS Piso_Pzas_MTD,
  COALESCE(T1.Piso_Pesos_MTD, 0)        AS Piso_Pesos_MTD,
  COALESCE(T3.Com_Pzas_MTD, 0)          AS Com_Pzas_MTD,
  COALESCE(T3.Com_Pesos_MTD, 0)         AS Com_Pesos_MTD,
  COALESCE(T3.Ordenes_Com_MTD, 0)       AS Ordenes_Com_MTD,
  COALESCE(T3.Numero_Socios_MTD, 0)     AS Numero_Socios_MTD,
  (COALESCE(T1.Piso_Pzas_MTD,0)  + COALESCE(T3.Com_Pzas_MTD,0))   AS Total_Pzas_MTD,
  (COALESCE(T1.Piso_Pesos_MTD,0) + COALESCE(T3.Com_Pesos_MTD,0))  AS Total_Pesos_MTD,

  COALESCE(T1.Piso_Pzas_MTDLY, 0)       AS Piso_Pzas_MTDLY,
  COALESCE(T1.Piso_Pesos_MTDLY, 0)      AS Piso_Pesos_MTDLY,
  COALESCE(T3.Com_Pzas_MTDLY, 0)        AS Com_Pzas_MTDLY,
  COALESCE(T3.Com_Pesos_MTDLY, 0)       AS Com_Pesos_MTDLY,
  COALESCE(T3.Ordenes_Com_MTDLY, 0)     AS Ordenes_Com_MTDLY,
  COALESCE(T3.Numero_Socios_MTDLY, 0)   AS Numero_Socios_MTDLY,
  (COALESCE(T1.Piso_Pzas_MTDLY,0)  + COALESCE(T3.Com_Pzas_MTDLY,0))  AS Total_Pzas_MTDLY,
  (COALESCE(T1.Piso_Pesos_MTDLY,0) + COALESCE(T3.Com_Pesos_MTDLY,0)) AS Total_Pesos_MTDLY,

  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pzas_MTD,0) - COALESCE(T1.Piso_Pzas_MTDLY,0),
    NULLIF(COALESCE(T1.Piso_Pzas_MTDLY,0), 0)
  ) AS Crecimiento_Piso_Pzas_MTD,
  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pesos_MTD,0) - COALESCE(T1.Piso_Pesos_MTDLY,0),
    NULLIF(COALESCE(T1.Piso_Pesos_MTDLY,0), 0)
  ) AS Crecimiento_Piso_Pesos_MTD,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pzas_MTD,0) - COALESCE(T3.Com_Pzas_MTDLY,0),
    NULLIF(COALESCE(T3.Com_Pzas_MTDLY,0), 0)
  ) AS Crecimiento_Com_Pzas_MTD,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pesos_MTD,0) - COALESCE(T3.Com_Pesos_MTDLY,0),
    NULLIF(COALESCE(T3.Com_Pesos_MTDLY,0), 0)
  ) AS Crecimiento_Com_Pesos_MTD,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pzas_MTD,0) + COALESCE(T3.Com_Pzas_MTD,0)) - (COALESCE(T1.Piso_Pzas_MTDLY,0) + COALESCE(T3.Com_Pzas_MTDLY,0)),
    NULLIF(COALESCE(T1.Piso_Pzas_MTDLY,0) + COALESCE(T3.Com_Pzas_MTDLY,0), 0)
  ) AS Crecimiento_Pzas_MTD,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pesos_MTD,0) + COALESCE(T3.Com_Pesos_MTD,0)) - (COALESCE(T1.Piso_Pesos_MTDLY,0) + COALESCE(T3.Com_Pesos_MTDLY,0)),
    NULLIF(COALESCE(T1.Piso_Pesos_MTDLY,0) + COALESCE(T3.Com_Pesos_MTDLY,0), 0)
  ) AS Crecimiento_Pesos_MTD,

  -- ══ MOMENTO 3: Últimos 7 días (ayer-6 -> ayer) ═══════════
  COALESCE(T1.Piso_Pzas_L7D, 0)         AS Piso_Pzas_L7D,
  COALESCE(T1.Piso_Pesos_L7D, 0)        AS Piso_Pesos_L7D,
  COALESCE(T3.Com_Pzas_L7D, 0)          AS Com_Pzas_L7D,
  COALESCE(T3.Com_Pesos_L7D, 0)         AS Com_Pesos_L7D,
  COALESCE(T3.Ordenes_Com_L7D, 0)       AS Ordenes_Com_L7D,
  COALESCE(T3.Numero_Socios_L7D, 0)     AS Numero_Socios_L7D,
  (COALESCE(T1.Piso_Pzas_L7D,0)  + COALESCE(T3.Com_Pzas_L7D,0))   AS Total_Pzas_L7D,
  (COALESCE(T1.Piso_Pesos_L7D,0) + COALESCE(T3.Com_Pesos_L7D,0))  AS Total_Pesos_L7D,

  COALESCE(T1.Piso_Pzas_L7DLY, 0)       AS Piso_Pzas_L7DLY,
  COALESCE(T1.Piso_Pesos_L7DLY, 0)      AS Piso_Pesos_L7DLY,
  COALESCE(T3.Com_Pzas_L7DLY, 0)        AS Com_Pzas_L7DLY,
  COALESCE(T3.Com_Pesos_L7DLY, 0)       AS Com_Pesos_L7DLY,
  COALESCE(T3.Ordenes_Com_L7DLY, 0)     AS Ordenes_Com_L7DLY,
  COALESCE(T3.Numero_Socios_L7DLY, 0)   AS Numero_Socios_L7DLY,
  (COALESCE(T1.Piso_Pzas_L7DLY,0)  + COALESCE(T3.Com_Pzas_L7DLY,0))  AS Total_Pzas_L7DLY,
  (COALESCE(T1.Piso_Pesos_L7DLY,0) + COALESCE(T3.Com_Pesos_L7DLY,0)) AS Total_Pesos_L7DLY,

  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pzas_L7D,0) - COALESCE(T1.Piso_Pzas_L7DLY,0),
    NULLIF(COALESCE(T1.Piso_Pzas_L7DLY,0), 0)
  ) AS Crecimiento_Piso_Pzas_L7D,
  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pesos_L7D,0) - COALESCE(T1.Piso_Pesos_L7DLY,0),
    NULLIF(COALESCE(T1.Piso_Pesos_L7DLY,0), 0)
  ) AS Crecimiento_Piso_Pesos_L7D,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pzas_L7D,0) - COALESCE(T3.Com_Pzas_L7DLY,0),
    NULLIF(COALESCE(T3.Com_Pzas_L7DLY,0), 0)
  ) AS Crecimiento_Com_Pzas_L7D,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pesos_L7D,0) - COALESCE(T3.Com_Pesos_L7DLY,0),
    NULLIF(COALESCE(T3.Com_Pesos_L7DLY,0), 0)
  ) AS Crecimiento_Com_Pesos_L7D,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pzas_L7D,0) + COALESCE(T3.Com_Pzas_L7D,0)) - (COALESCE(T1.Piso_Pzas_L7DLY,0) + COALESCE(T3.Com_Pzas_L7DLY,0)),
    NULLIF(COALESCE(T1.Piso_Pzas_L7DLY,0) + COALESCE(T3.Com_Pzas_L7DLY,0), 0)
  ) AS Crecimiento_Pzas_L7D,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pesos_L7D,0) + COALESCE(T3.Com_Pesos_L7D,0)) - (COALESCE(T1.Piso_Pesos_L7DLY,0) + COALESCE(T3.Com_Pesos_L7DLY,0)),
    NULLIF(COALESCE(T1.Piso_Pesos_L7DLY,0) + COALESCE(T3.Com_Pesos_L7DLY,0), 0)
  ) AS Crecimiento_Pesos_L7D,

  -- ══ MOMENTO 4: Evento "A la Mexicana" (9-16 sep) ═════════════
  COALESCE(T1.Piso_Pzas_AMX, 0)         AS Piso_Pzas_AMX,
  COALESCE(T1.Piso_Pesos_AMX, 0)        AS Piso_Pesos_AMX,
  COALESCE(T3.Com_Pzas_AMX, 0)          AS Com_Pzas_AMX,
  COALESCE(T3.Com_Pesos_AMX, 0)         AS Com_Pesos_AMX,
  COALESCE(T3.Ordenes_Com_AMX, 0)       AS Ordenes_Com_AMX,
  COALESCE(T3.Numero_Socios_AMX, 0)     AS Numero_Socios_AMX,
  (COALESCE(T1.Piso_Pzas_AMX,0)  + COALESCE(T3.Com_Pzas_AMX,0))   AS Total_Pzas_AMX,
  (COALESCE(T1.Piso_Pesos_AMX,0) + COALESCE(T3.Com_Pesos_AMX,0))  AS Total_Pesos_AMX,

  COALESCE(T1.Piso_Pzas_AMXLY, 0)       AS Piso_Pzas_AMXLY,
  COALESCE(T1.Piso_Pesos_AMXLY, 0)      AS Piso_Pesos_AMXLY,
  COALESCE(T3.Com_Pzas_AMXLY, 0)        AS Com_Pzas_AMXLY,
  COALESCE(T3.Com_Pesos_AMXLY, 0)       AS Com_Pesos_AMXLY,
  COALESCE(T3.Ordenes_Com_AMXLY, 0)     AS Ordenes_Com_AMXLY,
  COALESCE(T3.Numero_Socios_AMXLY, 0)   AS Numero_Socios_AMXLY,
  (COALESCE(T1.Piso_Pzas_AMXLY,0)  + COALESCE(T3.Com_Pzas_AMXLY,0))  AS Total_Pzas_AMXLY,
  (COALESCE(T1.Piso_Pesos_AMXLY,0) + COALESCE(T3.Com_Pesos_AMXLY,0)) AS Total_Pesos_AMXLY,

  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pzas_AMX,0) - COALESCE(T1.Piso_Pzas_AMXLY,0),
    NULLIF(COALESCE(T1.Piso_Pzas_AMXLY,0), 0)
  ) AS Crecimiento_Piso_Pzas_AMX,
  SAFE_DIVIDE(
    COALESCE(T1.Piso_Pesos_AMX,0) - COALESCE(T1.Piso_Pesos_AMXLY,0),
    NULLIF(COALESCE(T1.Piso_Pesos_AMXLY,0), 0)
  ) AS Crecimiento_Piso_Pesos_AMX,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pzas_AMX,0) - COALESCE(T3.Com_Pzas_AMXLY,0),
    NULLIF(COALESCE(T3.Com_Pzas_AMXLY,0), 0)
  ) AS Crecimiento_Com_Pzas_AMX,
  SAFE_DIVIDE(
    COALESCE(T3.Com_Pesos_AMX,0) - COALESCE(T3.Com_Pesos_AMXLY,0),
    NULLIF(COALESCE(T3.Com_Pesos_AMXLY,0), 0)
  ) AS Crecimiento_Com_Pesos_AMX,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pzas_AMX,0) + COALESCE(T3.Com_Pzas_AMX,0)) - (COALESCE(T1.Piso_Pzas_AMXLY,0) + COALESCE(T3.Com_Pzas_AMXLY,0)),
    NULLIF(COALESCE(T1.Piso_Pzas_AMXLY,0) + COALESCE(T3.Com_Pzas_AMXLY,0), 0)
  ) AS Crecimiento_Pzas_AMX,
  SAFE_DIVIDE(
    (COALESCE(T1.Piso_Pesos_AMX,0) + COALESCE(T3.Com_Pesos_AMX,0)) - (COALESCE(T1.Piso_Pesos_AMXLY,0) + COALESCE(T3.Com_Pesos_AMXLY,0)),
    NULLIF(COALESCE(T1.Piso_Pesos_AMXLY,0) + COALESCE(T3.Com_Pesos_AMXLY,0), 0)
  ) AS Crecimiento_Pesos_AMX

FROM cte_ventas_fisico_item AS T1
RIGHT JOIN cte_inventario_item AS T2
  ON  T1.ITEM_NBR = T2.Item_Nbr
LEFT JOIN cte_ventas_com_item AS T3
  ON  T2.Item_Nbr = T3.ITEM_NBR

-- Filtro de categorias: Salud y Bienestar (Estef) -- version LITERAL,
-- generada desde teams_config.py. Para ajustar: edita teams_config.py
-- y vuelve a correr generate_department_queries.py (no editar aqui).
WHERE T2.Cat_Nbr IN (2, 4, 8, 13, 27, 47, 54)

ORDER BY T2.OHQty_Clubes DESC

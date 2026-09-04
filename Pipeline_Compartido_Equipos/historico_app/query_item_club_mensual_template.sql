-- ============================================================
-- query_item_club_mensual_template.sql
-- Query EN VIVO (no pre-pulled) para el nivel Tienda-Item de la
-- mini-app -- se corre 1 sola vez por click del usuario, filtrado a
-- UN SOLO item ({ITEM_NBR}), asi que es chico y barato aunque escanee
-- el mismo rango de fechas que el pull masivo. Grano: Anio x Mes x
-- Club, para ese item.
-- ============================================================

DECLARE date_ini DATE DEFAULT DATE '{DATE_INI}';
DECLARE date_fin DATE DEFAULT DATE '{DATE_FIN}';
DECLARE p_item_nbr INT64 DEFAULT {ITEM_NBR};

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
  INNER JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC`     AS b ON a.ITEM_NBR = b.ITEM_NBR
  WHERE d.gregorian_date BETWEEN date_ini AND date_fin
    AND b.Old_NBR = p_item_nbr
),

cte_ventas_fisico_mensual AS (
  SELECT
    EXTRACT(YEAR FROM gregorian_date)  AS Anio,
    EXTRACT(MONTH FROM gregorian_date) AS Mes,
    STORE_NBR                          AS CLUB_NBR,
    SUM(piezas_dia)                    AS Venta_Pzas_Fisico,
    SUM(pesos_dia)                     AS Venta_Pesos_Fisico
  FROM cte_pos_diario
  GROUP BY Anio, Mes, CLUB_NBR
  HAVING SUM(piezas_dia) <> 0 OR SUM(pesos_dia) <> 0
),

cte_ventas_com_mensual AS (
  SELECT
    EXTRACT(YEAR FROM DATE(s.sales_order_detail_order_created_date))  AS Anio,
    EXTRACT(MONTH FROM DATE(s.sales_order_detail_order_created_date)) AS Mes,
    SAFE_CAST(s.sales_order_detail_assigned_store_nbr AS INT64)       AS CLUB_NBR,
    SUM(s.sales_order_detail_commercial_sale_qty_base)                 AS Venta_Pzas_Com,
    SUM(s.sales_order_detail_net_paid_orders_wo_shipping_amount_1)     AS Venta_Pesos_Com
  FROM `wmt-mx-dl-controlledmgzn-prod.ecom.Sams_Ventas` AS s
  WHERE
    DATE(s.sales_order_detail_order_created_date) BETWEEN date_ini AND date_fin
    AND s.sales_order_detail_commercial_sale_qty_base > 0
    AND SAFE_CAST(s.sales_order_detail_item_id_short AS INT64) = p_item_nbr
  GROUP BY Anio, Mes, CLUB_NBR
),

cte_dim_club AS (
  SELECT CLUB_NBR, CLUB_NAME
  FROM `wmt-intl-cons-mx-users.adhoc_users.SAMS_MERCH_MX_CLUBES_INFO`
)

SELECT
  COALESCE(f.Anio, c.Anio)           AS Anio,
  COALESCE(f.Mes, c.Mes)             AS Mes,
  COALESCE(f.CLUB_NBR, c.CLUB_NBR)   AS CLUB_NBR,
  d.CLUB_NAME,
  COALESCE(f.Venta_Pzas_Fisico, 0)   AS Venta_Pzas_Fisico,
  COALESCE(f.Venta_Pesos_Fisico, 0)  AS Venta_Pesos_Fisico,
  COALESCE(c.Venta_Pzas_Com, 0)      AS Venta_Pzas_Com,
  COALESCE(c.Venta_Pesos_Com, 0)     AS Venta_Pesos_Com
FROM cte_ventas_fisico_mensual f
FULL OUTER JOIN cte_ventas_com_mensual c
  ON  f.Anio = c.Anio AND f.Mes = c.Mes AND f.CLUB_NBR = c.CLUB_NBR
LEFT JOIN cte_dim_club d
  ON  COALESCE(f.CLUB_NBR, c.CLUB_NBR) = d.CLUB_NBR

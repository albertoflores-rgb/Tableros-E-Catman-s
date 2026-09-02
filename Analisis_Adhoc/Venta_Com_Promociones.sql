-- ============================================================
-- Venta_Com_Promociones.sql
-- Canal   : Sam's Club MX .com — Todos los Clubs (176, agregado)
-- Área    : E-Catman
-- Versión : 2.1 | 02-sep-2026
-- Base    : "SAMS - Venta e Inventarios Ecatman - Diario TY vs LY.sql"
--           (mismas tablas/CTE de venta .com; SIN piso ni inventario
--           a proposito, esto es solo venta .com).
--
-- v2.1: se agregó `Numero_Socios_Com` (COUNT DISTINCT de membresía)
--   junto al conteo de órdenes -- mismo caveat de doble conteo que
--   Piezas/Pesos/Órdenes: un socio que compró con 2+ promos a la vez
--   se cuenta en cada fila de promo, no sumar entre filas para sacar
--   "socios totales" (ver nota en el SELECT final).
--
-- QUÉ CAMBIÓ vs v1.0 (respaldo: Venta_Com_Promociones_v1_RAW.sql):
--   v1.0 usaba el campo `sales_order_detail_order_promotion_discount_desc`
--   TAL CUAL viene en la tabla, agrupado por Club+Item+Promo. Al
--   validar cardinalidad antes de correr en serio, se encontró que:
--     1) Ese campo NO es una sola promoción -- es una CONCATENACIÓN
--        con "/" de TODAS las promociones que aplicaron a esa línea
--        de orden (ej. "Descuento 2.3/ROLLBACK" = las dos aplicaron
--        juntas), con el texto LITERAL "null" (minúsculas) o
--        "NULL VALUE" como relleno cuando no aplicó promo en esa
--        posición. Por eso el campo crudo tenía 14,607 valores
--        "distintos" -- son combinaciones, no promociones reales.
--     2) Agrupar el campo crudo por Club+Item+Promo generaba ~33.3
--        millones de filas de salida (¡incluso limpiando null!) --
--        imposible de manejar en Excel/CSV normal, y fue lo que dejó
--        el primer intento de correrlo colgado >20 min sin terminar
--        de bajar el resultado por REST.
--   v2.0 usa SPLIT(...,'/') + UNNEST para separar cada promoción
--   ATÓMICA en su propia fila, descarta los placeholders "null"/
--   "NULL VALUE", y quita el desglose por CLUB (se agrega a total
--   de los 176 clubs) para que el grano final (Fecha+Item+Promo) dé
--   un tamaño manejable (~4M filas en 2025+2026 YTD, confirmado con
--   COUNT(DISTINCT) antes de correr el query completo).
--   Con esto: 837 promociones atómicas reales (ROLLBACK, Descuento
--   2.3, "Ahorra 15% con Cupón <MES><pct>", "Agrega N y paga M",
--   "NxM$", "Envío Gratis Socios Plus", etc.) en vez de 14,607
--   combinaciones sin sentido.
--
-- OJO -- doble conteo esperado: si una línea de orden tuvo 2+ promos
--   aplicadas a la vez, esa venta se cuenta UNA VEZ POR CADA promo
--   (mismo criterio que "aproximado" usado para Socios .com en el
--   pipeline de equipos -- sumar Venta_Pesos_Com de todas las filas
--   de este archivo SIEMPRE va a dar MÁS que la venta .com real total,
--   porque las ventas con promos combinadas se reparten en varias
--   filas). Para el total real sin doble conteo, usa el query base
--   original (sin desglose de promo) o COUNT(DISTINCT order_nbr).
--
-- Rango: 1-ene-2025 -> ayer (2025 completo + 2026 YTD, grano diario
--   -- filtra/pivotea por año tú mismo en BQ/Excel/Power BI).
-- ============================================================

DECLARE date_ini DATE DEFAULT DATE(2025, 1, 1);
DECLARE date_fin DATE DEFAULT DATE_SUB(CURRENT_DATE('America/Mexico_City'), INTERVAL 1 DAY);

WITH cte_com_promo_split AS (
  SELECT
    DATE(s.sales_order_detail_order_created_date)                  AS Fecha,
    SAFE_CAST(s.sales_order_detail_item_id_short AS INT64)          AS ITEM_NBR,
    TRIM(promo_token)                                               AS Promocion_Desc,
    s.sales_order_detail_commercial_sale_qty_base                   AS Piezas,
    s.sales_order_detail_net_paid_orders_wo_shipping_amount_1       AS Pesos,
    s.sales_order_detail_order_nbr                                  AS Orden_Nbr,
    s.sales_order_detail_membership_nbr                             AS Membresia_Nbr
  FROM `wmt-mx-dl-controlledmgzn-prod.ecom.Sams_Ventas` AS s,
    UNNEST(SPLIT(s.sales_order_detail_order_promotion_discount_desc, '/')) AS promo_token
  WHERE
    DATE(s.sales_order_detail_order_created_date) BETWEEN date_ini AND date_fin
    AND s.sales_order_detail_commercial_sale_qty_base > 0        -- excluir devoluciones / reversos
    AND s.sales_order_detail_item_id_short IS NOT NULL           -- excluir ghost records
    AND LOWER(TRIM(promo_token)) NOT IN ('null', 'null value', '')  -- descarta placeholders
)

SELECT
  p.Fecha,
  p.ITEM_NBR,
  b.PRIMARY_DESC     AS ITEM_DESC_1,
  b.SECONDARY_DESC   AS ITEM_DESC_2,
  b.CATEGORY_NBR     AS CAT_NBR,
  p.Promocion_Desc,
  SUM(p.Piezas)                        AS Venta_Pzas_Com,
  SUM(p.Pesos)                         AS Venta_Pesos_Com,
  COUNT(DISTINCT p.Orden_Nbr)          AS Ordenes_Com,
  -- Socios (membresías) ÚNICAS con venta de ESTA promo en ESTE ítem/día.
  -- OJO mismo caveat que Piezas/Pesos: si un socio compró el mismo
  -- ítem el mismo día con 2+ promos combinadas, se cuenta en cada fila
  -- de promo por separado -- no sumar esta columna entre filas para
  -- sacar "socios totales", solo sirve por fila/agrupación individual.
  COUNT(DISTINCT p.Membresia_Nbr)      AS Numero_Socios_Com

FROM cte_com_promo_split AS p
LEFT JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC` AS b
  ON p.ITEM_NBR = b.Old_NBR

GROUP BY
  p.Fecha, p.ITEM_NBR, ITEM_DESC_1, ITEM_DESC_2, CAT_NBR, p.Promocion_Desc

-- ── Filtros opcionales ────────────────────────────────────
--WHERE b.CATEGORY_NBR IN (41, 43, 46, 49, 53, 68)  -- Abarrotes, por ejemplo
--AND p.Promocion_Desc = 'ROLLBACK'

ORDER BY p.Fecha DESC, p.ITEM_NBR

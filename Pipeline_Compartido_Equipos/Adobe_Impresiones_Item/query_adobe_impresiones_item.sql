-- ============================================================
-- query_adobe_impresiones_item.sql
-- Version productiva (para el tablero standalone) del query de
-- investigacion "SAMS - Adobe Impresiones Item (Investigacion) v2.sql"
-- (Respaldo_Querys/saved_queries/) -- MISMA logica validada, sin
-- cambios de negocio, solo se parametrizo la fecha (antes era un
-- DECLARE hardcodeado) para poder correrla desde Python con
-- @fecha_reporte.
--
-- Costo real validado (02-sep-2026): ~11 GB/dia (NO los ~50GB/dia
-- que se temia en v1 -- ver el .sql de investigacion para el detalle
-- completo del descubrimiento).
--
-- Fuente: wmt-intl-cons-mc-mx-prod...sams_mx_csd_adobe_event
-- (VIEW sobre tabla externa ORC particionada por `ds`).
-- "Impresion" = proxy validado con datos reales: cada segmento de
-- producto (eVar168) dentro de un hit con chnl_txt IN
-- ('searchResults', 'browseResults'). NO existe un evento oficial
-- documentado en Confluence para esto -- pendiente con Adobe Admin
-- (Claudia Ornelas / Eduardo Visoso, Datamesh).
-- ============================================================

WITH base AS (
  SELECT
    ds,
    prod_lst_txt
  FROM `wmt-intl-cons-mc-mx-prod.mx_csd_secured_dl_tables.sams_mx_csd_adobe_event`
  WHERE op_cmpny_cd = 'SAMS-MX'
    AND ds = @fecha_reporte                              -- filtro de particion, OBLIGATORIO
    AND chnl_txt IN ('searchResults', 'browseResults')   -- proxy real de "impresion"
    AND prod_lst_txt IS NOT NULL
),
segmentos AS (
  SELECT
    ds,
    REGEXP_EXTRACT(segment, r'eVar168=([^|;,]+)') AS Item_Nbr
  FROM base, UNNEST(SPLIT(prod_lst_txt, ',')) AS segment
  WHERE segment != ''
)
SELECT
  ds        AS Fecha,
  Item_Nbr,
  COUNT(*)  AS Ocurrencias
FROM segmentos
WHERE Item_Nbr IS NOT NULL
GROUP BY Fecha, Item_Nbr
ORDER BY Fecha, Ocurrencias DESC;

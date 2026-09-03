# Total_Departamentos — Tablero consolidado "todos los deptos"

Tablero flat HTML (Tailwind + Chart.js, sin servidor) con el query
`SAMS - Venta e Inventarios Ecatman - YTD MTD 7Dias TY vs LY (Item
Total).sql` corrido **sin filtro de categoría** — los 8 departamentos
de E-Catman en un solo dataset, para revisión del líder.

## Contenido

- `tablero_total_departamentos.html` — el tablero (KPIs, gráficas por
  departamento, top 20 items, insights, botón de descarga).
- `raw_bq_item_total_todos_deptos.csv` — 232,716 filas / 122 columnas,
  el dataset completo. **SÍ está versionado en git** (excepción
  explícita en `.gitignore` — ver ahí el por qué).

## Costo real de esta corrida (IMPORTANTE, léelo antes de repetir esto)

El query completo (venta física + .com + inventario + Impresiones
Adobe, sin filtro de categoría) escaneó **~3.8 TB reales** en su
corrida correcta y completa — dominado casi en su totalidad por el
bloque de Impresiones Adobe (`cte_impresiones_raw`), que lee una tabla
externa ORC sin partición útil para el filtro de canal (`chnl_txt`).
El bloque de venta/inventario es fijo en ~19GB sin importar el rango.

**Nota de transparencia sobre la sesión completa:** al construir este
tablero se detectó — vía `INFORMATION_SCHEMA.JOBS_BY_USER` — que la
sesión del día sumó **~8 TB** de bytes billed en total, no solo los
~3.8 TB de la corrida final. Esto pasó porque:

1. El primer intento de traer los resultados chocó con un límite de
   `max_results=10000` de la herramienta usada, así que el CSV inicial
   quedó truncado (solo 10,000 de 232,765 filas).
2. Para resolverlo se investigó la tabla temporal de resultados ya
   materializada por BigQuery (`_anon...` dataset, vive ~24h), pero en
   el camino se corrieron **dos variantes casi idénticas** del query
   completo (~3.8 TB cada una) antes de confirmar cuál tenía el schema
   completo (122 columnas: TY + LY + Crecimiento + Impresiones) vs
   la incompleta (66 columnas, sin LY ni Crecimiento).
3. El CSV final que queda en este repo viene de la tabla **completa y
   correcta** (`anon2c34b009...`), leída directamente desde un venv
   local con `google-cloud-bigquery` — esa lectura final costó solo
   ~254 MB (tabla ya materializada, no las fuentes), no otro TB.

**Lección para la próxima vez que se corra esto:** si se necesita
"todos los departamentos" de nuevo, correrlo UNA sola vez, confirmar
el schema completo ANTES de dar por buena la corrida, y usar
`to_dataframe()` de `google-cloud-bigquery` directo (sin límites de
paginación de 10,000 filas) para bajar el resultado sin necesidad de
tablas temporales de respaldo.

## Recomendación si esto se vuelve recurrente

Si el líder pide refrescar este tablero periódicamente (semanal,
mensual), **no volver a correr `cte_impresiones_raw` contra la tabla
fuente de Adobe cada vez** — migrar ese bloque a un histórico
incremental local (mismo patrón que
`Abarrotes/tablero_insights_com_abarrotes/historico_app/`), guardando
solo el día más reciente cada corrida en vez de re-escanear el YTD
completo. Sin eso, cada refresh de este tablero cuesta ~3.8 TB.

## Cómo se generó (para reproducir)

```bash
# 1. Correr el query completo (~3.8 TB, un solo intento, confirmar
#    schema antes de dar por bueno el resultado)
# 2. Bajar resultado con google-cloud-bigquery + to_dataframe(),
#    sin límites de paginación
# 3. Guardar CSV con encoding utf-8-sig
# 4. El HTML lee el CSV solo como link de descarga directa
#    (<a href="raw_bq_item_total_todos_deptos.csv" download>) --
#    los KPIs/gráficas/top20 están pre-calculados y embebidos como
#    JSON estático en el propio HTML (no se re-procesan 232K filas
#    en el navegador).
```

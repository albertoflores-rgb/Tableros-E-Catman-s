# Tablero de Insights .com Abarrotes — MTD + Tendencia 7D

Tablero de 5 pestañas para presentar resultados a subdirectores
comerciales. Enfoque `.com`, con Piso/Brick visible como referencia.

## Pestañas

1. **Resumen y Accionables** — KPIs, gráficas MTD/L7D por categoría,
   tarjetas de categoría **clickeables** (al dar click despliegan el
   detalle completo de items "Impulsar .com" y "Replicar éxito" de esa
   categoría, no solo el top 3 curado de las tablas globales),
   recomendaciones ejecutivas.
2. **Explorador BQ** — las 5,885 filas del query Item Total, 100%
   navegable del lado del cliente: filtro por cada campo descriptivo
   (categoría, subcategoría, proveedor, tipo, status, semáforo de
   inventario) + búsqueda libre + orden ascendente/descendente en
   cualquier columna numérica. Incluye 36 columnas: identificadores,
   inventario (piezas totales, valor $, tiendas con inventario,
   precio), y **piezas + pesos de Piso y .com en YTD, MTD y L7D**, con
   su % de crecimiento y el **% Share .com vs Brick** calculado en los
   3 momentos (`Share_Com_YTD/MTD/L7D` = .com $ / (.com $ + Piso $)).
   También trae `Top_L7D_Cat`: el ranking del item dentro de su
   categoría por venta `.com` de los últimos 7 días (1 = el más
   vendido de la categoría en .com esta semana).
3. **Promos Vigentes + Mapeo en Sitio** — las 126 promos vigentes con
   **las mismas métricas del Explorador BQ** (YTD/MTD/L7D piezas+$,
   inventario, tiendas con inventario, share .com vs brick, Top L7D en
   categoría) más los datos propios de la promo (descripción, %
   ahorro, vigencia) y el cruce contra un mapeo real de los carruseles
   de `sams.com.mx` (Home, LP Despensa, LP Socio de Negocio) hecho con
   Playwright (agente `qa-kitten`). Marca qué % de las promos vigentes
   NO tiene ninguna exposición en esos carruseles — oportunidad directa
   de exhibición digital.
4. **Septiembre: FCST y Riesgo** — compara el FCST .com de septiembre
   (`FCST Septiembre 2026.xlsx`, $448.9M) contra el comparable de LY que
   trae el mismo archivo, deriva el % de crecimiento YoY que el FCST
   exige por categoría, y lo contrasta contra el crecimiento MTD/L7D
   real que ya tenemos. Si la tendencia L7D se mantiene plana, el
   estimado sale en ~$430.3M ($18.5M / -4.1% por debajo del target),
   con el riesgo concentrado en Aceites/Granos & Aderezos y Pastas y
   Condimentos. Tres tablas de accionables cruzando las subcategorías
   de Fiestas Patrias del reporte de boosteos de búsqueda interna
   (`reporte_internal_search_boosteos.html`) contra el catálogo:
   *Apagar Incendios* (alto volumen en Piso cayendo fuerte en .com),
   *Doblar la Apuesta* (momentum sostenido, listos para boost de
   búsqueda) y *Blanco Total* (demanda física real, cero promo vigente).
5. **Histórico Diario 2026** — grafico de linea interactivo (Chart.js)
   con venta diaria del 2026-01-01 al dia de ayer, 3 niveles de
   agregacion seleccionables: Categoria (6), Subcategoria (65) e Item
   (1,160 -- buscador por nombre/numero). Toggle de metrica (Pesos $ /
   Piezas) y canal (Fisico+.com / Solo Fisico / Solo .com), tabla
   resumen con el total del periodo por entidad seleccionada. **Nivel
   Tienda-Item NO incluido todavia** -- a ese grano (Fecha x Club x
   Item) el dataset real son 15.3M filas (medido con bigquery-explorer
   antes de construir nada), demasiado para un HTML estatico; pendiente
   de decidir con Alberto si se resuelve con una mini-app FastAPI+DuckDB
   local o se limita a un Top-N de clubs por item.
   Fuente: `query_diario_abarrotes.sql` (copia adaptada de "SAMS - Venta
   e Inventarios Ecatman - Diario TY vs LY.sql", agregado en BigQuery a
   Fecha x Cat x Subcat x Item -- sin club -- para bajar de 15.3M a
   ~219K filas). Pipeline **manual**, fuera del `PIPELINE_STEPS` de la
   rutina automatizada de las 8:30 AM (`rutinas/W4_Tablero_Insights_Com_Abarrotes/config.py`)
   -- correr `run_query_diario.py` + `finalize_historico.py` a mano
   cuando se quiera refrescar.

## Fuentes de datos

1. **BigQuery** — `query_item_total_abarrotes.sql` (copia de
   `Respaldo_Querys/saved_queries/SAMS - Venta e Inventarios Ecatman -
   YTD MTD 7Dias TY vs LY (Item Total).sql` con el filtro de categorías
   Abarrotes activado). Proyecto: `wmt-intl-cons-mx-users`.
2. **Promos vigentes** — hoja `Histórico` de
   `Histórico Abarrotes 27 ago.xlsx` (OneDrive, Promos Activas/Agosto).
3. **Parrilla 10+1** — hojas semanales de `Parrilla-10+1 Agosto.xlsx`.
4. **Carruseles del sitio** — `site_carousel_items.json`, capturado con
   el agente `qa-kitten` (Playwright) visitando Home, LP Despensa y LP
   Socio de Negocio de sams.com.mx el 30-ago-2026. El sitio no expone
   SKU en el HTML, así que el cruce contra las promos vigentes
   (`match_site.py`) es **matching de texto por tokens** (normaliza
   acentos/mayúsculas, separa dígitos de letras, ignora stopwords) con
   umbral score>=0.6 y overlap>=2 tokens — es una aproximación
   direccional, no un match exacto por SKU. El disclaimer completo
   queda visible en la pestaña 3 del tablero.

## Pipeline (correr en este orden)

```
run_query.py           -> raw_bq_item_total.csv     (venv W3_Abarrotes_Cats: bigquery+pandas)
extract_promos.py       -> promos_historico_abarrotes.csv
extract_parrilla.py     -> parrilla_agosto_abarrotes.csv
build_merge.py           -> cat_agg.csv, accionables_items.csv, merged_full.csv (incluye Top_L7D_Cat, Share_Com_*, Inv_*_Total)
match_site.py            -> site_mapping.csv        (cruce promos vigentes x site_carousel_items.json)
finalize_data.py         -> dashboard_data.json      (pestaña 1)
finalize_explorer.py     -> explorer_data.json       (pestaña 2)
finalize_promos.py       -> promos_data.json         (pestaña 3)
finalize_sept.py         -> sept_data.json           (pestaña 4 -- lee FCST Septiembre 2026.xlsx + cat_agg.csv + merged_full.csv + reporte_internal_search_boosteos.html)
build_dashboard.py       -> tablero_insights_com_abarrotes.html (ensambla tpl_shell.html + tpl_tab{1,2,3,4}.html/js)
```

`site_carousel_items.json` es un snapshot manual del contenido real de
los carruseles (no se regenera solo) — si quieres refrescar el mapeo de
sitio, vuelve a invocar al agente `qa-kitten` con las 3 URLs y
reemplaza ese archivo antes de correr `match_site.py`.

## Definición de "Accionable"

Un item es **accionable** si está en la parrilla de agosto **y** tiene
una promo vigente. Dentro de los accionables se clasifica:

- **Impulsar .com**: crecimiento .com MTD <= -10% pese a promo activa.
- **Riesgo de quiebre**: semáforo de inventario crítico/OOS con venta
  .com activa.
- **Replicar éxito**: crecimiento .com MTD >= +20%.
- **Monitorear**: el resto.

## Regenerar el tablero

Si cambian las fuentes, correr los 9 scripts en orden y volver a abrir
el HTML — no hay build step ni dependencias de Node, es HTML estático
con CDN de Tailwind/Chart.js. Los archivos `tpl_*.html`/`tpl_*.js` son
las plantillas editables de cada pestaña; `build_dashboard.py` solo
las ensambla con los 3 JSON de datos.

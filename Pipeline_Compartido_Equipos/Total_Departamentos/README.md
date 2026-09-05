# Total_Departamentos — Tablero consolidado "Total Departamentos"

Tablero HTML (Tailwind + Chart.js) con el universo COMPLETO de
categorias de E-Catman: los 6 equipos + Abarrotes + 5 categorias
"huerfanas" (76 categorias en total, ver `teams_config.py` ->
`EXTRA_TEAMS['total_departamentos']`). Reemplaza (03-sep-2026) la
version anterior estatica/hardcodeada -- ver seccion "Historia" abajo.

## Contenido

- `tablero_insights_com_total_departamentos.html` — el tablero, generado
  100% por el pipeline generico compartido (`../pipeline/`), MISMAS 3
  pestanas que los 6 tableros de equipo (Resumen, Explorador BQ,
  Septiembre FCST -- esta ultima se omite con un aviso claro porque la
  vista consolidada no tiene una sola hoja de FCST propia, ver
  `pipeline/finalize_sept.py`).
- `raw_bq_item_total_total_departamentos.csv` — 154,815 filas, el
  dataset completo (via Git LFS, ver `.gitattributes`).
- `tablero_total_departamentos_v1_revision.html` — el tablero **V1
  legado** (ad-hoc, 02-sep-2026, publicado en Puppy Pages con el slug
  `tablero-total-departamentos`, SIN "-insights-com-"). Se agrego aqui
  (04-sep-2026) para tener "insights" (la version real, de arriba) y
  "revision" (esta, el legado con Impresiones Adobe YTD completas) en
  la MISMA pestana/carpeta de GitHub, uno al lado del otro. Su CSV
  companion (`raw_bq_item_total_todos_deptos.csv`, 232,716 filas, 122
  columnas, via Git LFS) sigue viviendo en este folder tambien -- ver
  `tablero_total_departamentos_v1/README.md` en el workspace principal
  para el detalle completo de por que existe por separado y como se
  recupero su CSV sin volver a pagar el costo de ~3.8 TB.

## Como se genera (03-sep-2026 en adelante -- pipeline real, no ad-hoc)

```bash
cd Pipeline_Compartido_Equipos
python run_query_combined.py            # 1 sola pasada BQ, universo completo (76 cats), ~16-18GB
python split_by_team.py                 # separa CSVs por equipo + total_departamentos (gratis, local)
python validate_integrity.py            # chequeo no bloqueante: venta .com de ayer vs promedio 7 dias
python build_total_departamentos.py     # corre pipeline/run_team_pipeline.py total_departamentos
```

O con la rutina consolidada (ver `rutinas/W6_Tableros_Ecatman_Consolidado/`
en el workspace principal, `main.py` hace los 4 pasos + los 6 equipos
en un solo comando).

## Costo real (comparado con el intento anterior)

**Antes (02-sep-2026, ad-hoc, sin filtro de categoria):** el query
completo (venta + inventario + Impresiones Adobe) escaneaba ~3.8 TB
por corrida, dominado por el bloque de Impresiones Adobe.

**Ahora (03-sep-2026, pipeline real):** se reutiliza EXACTAMENTE el
mismo query combinado que ya corre para los 6 equipos
(`query_item_total_template.sql`, SIN el bloque de Impresiones Adobe),
solo que con el filtro `@cat_filter` extendido a las 76 categorias del
universo completo en vez de 66. Confirmado con `bq --dry_run`: el costo
es **IDENTICO** (~16-18 GB) sin importar si el filtro trae 66 o 76
categorias -- el costo lo domina el escaneo completo de las tablas
base, no el tamano del filtro. Corrida real del 03-sep-2026: **16.26 GB
billed** para los 7 tableros (6 equipos + Total Departamentos) en una
sola pasada.

**Ahorro: de ~3.8 TB por refresh a ~16-18 GB compartidos con los otros
6 tableros (esencialmente gratis, ya se estaba pagando ese query de
todos modos).**

## Por que ya no tiene boton de descarga de CSV embebido

La version anterior (ad-hoc) incrustaba los KPIs/graficas como JSON
estatico y ofrecia el CSV como descarga directa porque no habia
pipeline real detras. La version actual usa el mismo patron que los 6
tableros de equipo: el Explorador BQ (pestana 2) trae el detalle a
nivel item embebido y filtrable en el propio HTML (154,815 items) --
no hace falta un boton de descarga aparte. Si se necesita el CSV crudo
completo, sigue versionado en este folder via Git LFS.

## Alcance NO incluido en v1 (a proposito)

- **DSV** (Inventario_DSV/DSV_Proveedor/DSV_Costo): solo aplica a
  Tecnologia/Seasonal/Apparel (ver `merge_dsv.py`) -- no se corre para
  esta vista consolidada. Los items de esos 3 equipos SI aparecen aqui,
  pero sin las columnas DSV.
- **Pestana 3 (Septiembre FCST)**: se omite con un aviso claro -- no
  existe una sola meta de FCST unificada para "todos los departamentos".
  Ver el FCST por equipo en su tablero individual.

## Historia (contexto, no reproducir la version vieja)

La primera version de este tablero (02-sep-2026) se genero con un
query ad-hoc SIN filtro de categoria (para traer "todo" sin tener que
enumerar categorias) que por accidente arrastro el bloque completo de
Impresiones Adobe (`cte_impresiones_raw`), disparando el costo a ~3.8
TB por corrida y ~8 TB en la sesion completa (incluyendo dos intentos
fallidos por un limite de paginacion). Ver git log de este archivo
para el detalle completo de esa lección. La version actual (03-sep-2026)
corrige esto usando el query PARAMETRIZADO ya optimizado del pipeline
compartido (sin Impresiones Adobe) con un filtro de 76 categorias en
vez de "sin filtro".

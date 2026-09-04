# Tablero Adobe Impresiones por Item (standalone)

Revive el hallazgo unico del extinto "Total Departamentos V1" (la
version ad-hoc del 02-sep-2026 que se descarto por costar ~3.8 TB por
corrida) como su **propio tablero independiente**, sin tocar el
tablero actual de Total Departamentos (que sigue sin Impresiones
Adobe, a proposito, por costo -- ver `catman_equipos/README.md` y
`DASHBOARD_TRACKER.md` seccion 12).

## Que muestra

Impresiones/ocurrencias en sitio (search + browse) por Item_Nbr,
proxy validado con datos reales de Adobe Analytics (`chnl_txt IN
('searchResults','browseResults')`, item extraido de `eVar168`).
Enriquecido con descripcion/squad/categoria/marca del catalogo local
(`catalogo_slim.csv`) para que la tabla sea legible.

**No es un evento oficial documentado de Adobe** -- es un proxy
validado con datos (ver query de investigacion), pendiente de
confirmar el nombre oficial con Adobe Admin (Claudia Ornelas / Eduardo
Visoso, Datamesh).

## Archivos

| Archivo | Que hace |
|---|---|
| `query_adobe_impresiones_item.sql` | Version parametrizada (`@fecha_reporte`) del query de investigacion validado -- misma logica, sin cambios de negocio |
| `run_query.py` | Corre el query para UNA fecha fija (ver docstring: NO se autodetecta el dia mas reciente, se intento y colgo la corrida -- ver por que dentro del script) y guarda `raw_adobe_impresiones_item.csv` |
| `build_dashboard.py` | Enriquece con el catalogo y genera `tablero_adobe_impresiones_item.html` (Tailwind + Chart.js, sin servidor, con boton de descarga de CSV client-side) |

## Costo real (dia 2026-09-02, corrida de validacion 04-sep-2026)

- **15.65 GB facturados** (el estimado de la investigacion v2 era
  ~11 GB -- la diferencia probablemente por datos que siguieron
  llegando/backfill de esa particion entre el 02-sep y el 04-sep).
- 12,342 items distintos con >=1 impresion, 15,899,518 ocurrencias
  totales, 85.7% de match contra el catalogo local.

## Como correrlo de nuevo (otro dia)

```
cd tablero_adobe_impresiones_item
.venv\Scripts\python.exe run_query.py 2026-09-10   # la fecha que quieras
.venv\Scripts\python.exe build_dashboard.py
```

**Antes de correr un rango de varios dias:** el costo escala
linealmente (~11-16 GB POR DIA) -- un YTD completo costaria varios TB,
ver la nota de "siguiente paso recomendado" en
`Respaldo_Querys/saved_queries/SAMS - Adobe Impresiones Item
(Investigacion) v2.sql`. Confirmar con Alberto antes de automatizar
esto en una rutina diaria.

## Publicacion

Separado del tablero "Total Departamentos" (`tablero-insights-com-total-departamentos`,
que sigue sin esta data a proposito). Este vive en su propio slug:
`tablero-adobe-impresiones-item`.

## Estado

INVESTIGACION / snapshot manual -- no esta en Task Scheduler, no se
refresca solo. Correr `run_query.py` + `build_dashboard.py` a mano
cuando se quiera un dia nuevo.

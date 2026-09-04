# Mini-app: Historico Mensual 2025 (completo) + YTD 2026 -- TODO EL NEGOCIO

Variante del `historico_app` de Abarrotes
(`tablero_insights_com_abarrotes/historico_app/`) para el **negocio
completo**: los 6 equipos de E-Catman (Perecederos, Impulso, Seasonal,
Apparel, Tecnología, Salud y Bienestar) + Abarrotes + 5 categorías
"huérfanas" (76 categorías en total, mismo universo que el tablero
"Total Departamentos"), con **un solo ambiente compartido** (selector
de área/equipo dentro de la página, no N apps separadas) y **una
variante pedida por Alberto**: en vez de esconder el valor de 2025 y
solo mostrar el % de crecimiento (como hace el tab estático de
Abarrotes), aquí se ve la **línea completa de 2025 (12 meses)**
superpuesta con el **YTD real de 2026** -- para tener perspectiva de
la tendencia/estacionalidad del año pasado mes a mes.

**Actualizado 03-sep-2026:** se expandió de 72 -> 76 categorías (ya
cubre el negocio 100%, no solo 6 equipos + Abarrotes) y se agregó una
**Tabla de Datos** con métricas de negocio a corte mensual (precio
promedio, costo promedio, margen comercial $/%, CR YoY, tendencia MoM,
share .com/piso) con YTD 2026 + LY 2025 completo lado a lado para el
comparable -- ver sección "Tabla de Datos" más abajo.

## Diferencias vs. el historico_app de Abarrotes (diario)

| | Abarrotes (diario) | Esta mini-app (mensual) |
|---|---|---|
| Grano (pull masivo) | Fecha x Club x Ítem | **Mes** x Ítem (**sin Club** -- ver nota abajo) |
| Nivel Tienda-Ítem | Sale del mismo parquet masivo | **Consulta en vivo** a BigQuery, 1 ítem a la vez |
| Cobertura | TY 2026 (Ene-hoy) vs LY 2025 mismo rango | **2025 completo (12 meses)** + YTD 2026 |
| Valor de 2025 | Oculto (solo se usa para calcular %) | **Visible** -- línea propia en la gráfica |
| Áreas | Solo Abarrotes | Todo el negocio: 6 equipos + Abarrotes + huérfanas, selector en la página |
| Categorías | 6 (hardcoded) | 76 combinadas, filtradas por área vía `teams_config.py` |
| Niveles | Categoría / Subcategoría / Ítem / Tienda-Ítem | Los mismos 4 niveles |
| Métricas de negocio (precio/costo/margen) | No | **Sí** -- pestaña "Tabla de Datos" (ver abajo) |

### Por qué el nivel Tienda-Ítem es distinto (lección aprendida en vivo)

El primer intento SÍ metía Club en el pull masivo (paridad total con
Abarrotes). Al correrlo con las categorías combinadas x 20 meses, el
dataframe creció a varios GB y **casi agota la RAM disponible de la
máquina** (validado en vivo 01-sep-2026 -- se abortó a tiempo antes de
un crash). Abarrotes puede darse ese lujo con Club incluido porque son
solo 6 categorías; aquí son 76 (13x más). La solución: el pull masivo
se quedó SIN Club (Mes x Ítem nomás, mucho más chico), y el nivel
Tienda-Ítem se resuelve con un **query en vivo a BigQuery** (1 solo
ítem a la vez, `query_item_club_mensual_template.sql`) cuando el
usuario lo pide -- tarda unos segundos (no es instantáneo como los
otros 3 niveles) pero nunca vuelve a arriesgar la RAM local.

## Por qué un solo ambiente (no N mini-apps)

Mismo principio DRY que `catman_equipos/pipeline/`: la lógica de
agregación/series/métricas es idéntica para todas las áreas, lo único
que cambia es qué categorías filtra. Un query combinado (`@cat_filter`
con las 76 categorías) + un selector de área en el frontend evita
mantener N copias de `app.py`/`db.py` casi idénticas.

## Negocio completo: 76 categorías (expandido 03-sep-2026)

A petición de Alberto ("integra todo el negocio"), esta mini-app ya no
se limita a los 6 equipos + Abarrotes (72 categorías) -- ahora cubre
las **76 categorías** completas (6 equipos + Abarrotes + 5 huérfanas:
45 Tabaco, 62 Azúcar, 70 Libros, 73 Bulk Deli, 88 Joyería), el mismo
universo que ya usa el tablero estático "Total Departamentos".

- **Dónde vive la lista de categorías:** `teams_config.all_cat_nbrs_universe()`
  (ya existía desde la Fase 2 del tablero "Total Departamentos" -- no
  se duplicó, se reusó tal cual).
- **Nueva área en el selector:** `AREAS["todo_el_negocio"]` en `db.py`
  -- aparece PRIMERO en el dropdown (es la vista por default más
  completa) y usa las 76 categorías. Las 7 áreas anteriores (6 equipos
  + Abarrotes) se conservan tal cual para poder seguir viendo cada una
  por separado.
- **Por qué NO se agregó a `teams_config.TEAMS`/`EXTRA_TEAMS`:** esos
  dos dicts alimentan `run_team_pipeline.py --all` / el `main.py` de
  las rutinas W5/W6 (los tableros estáticos diarios) -- no queremos que
  esta mini-app de PRUEBA afecte esa producción por accidente.

## Tabla de Datos: métricas de negocio a corte mensual (nuevo 03-sep-2026)

Botón "Tabla de Datos" junto a "Gráfica" -- construida **a nivel
general de cada ítem/entidad** (agregando todos los clubs, igual que
el resto de esta mini-app, NO desglosado por club). Para la entidad
elegida (categoría, subcategoría o ítem -- no aplica a Tienda-Ítem, ahí
no hay costo/precio a ese grano), muestra 12 filas (Ene..Dic) con LY
2025 completo y TY 2026 (hasta el mes actual) lado a lado para el
comparable, más un resumen YTD 2026 / Total 2025:

| Métrica | Cómo se calcula |
|---|---|
| Precio Promedio | Venta $ del mes / piezas del mes (real, varía mes a mes) |
| Costo Promedio | Snapshot de HOY de `MDSE_INVENTORY` (`UNIT_COST`), ponderado por volumen de piezas del periodo -- **constante** en todos los meses del mismo ítem (no hay histórico de costo por mes en la fuente) |
| Margen Comercial $ | Precio Promedio − Costo Promedio |
| Margen Comercial % | Margen $ / Precio Promedio |
| CR YoY | % crecimiento del mes vs. el mismo mes del año anterior |
| Tendencia MoM | % cambio vs. el mes anterior, encadenado (Dic-2025 → Ene-2026 funciona igual que cualquier otro mes) |
| Share .com / Piso (brick) | % de la venta $ del mes que vino de .com vs. física |

**Limitación conocida (documentada a propósito, no es un bug):** el
Costo Promedio es un snapshot de HOY, no tiene historia mensual real
-- se aplica como referencia constante. A nivel Ítem el margen es
razonable (ítems similares en costo/precio). A nivel Categoría/
Subcategoría el margen puede verse raro (incluso negativo) porque
mezcla el precio promedio ponderado de TODOS los ítems de la categoría
contra su costo promedio ponderado -- ítems muy distintos entre sí
pueden generar un "margen ciego" que no representa ningún ítem real.
Para lectura de margen confiable, usar nivel **Ítem**.

## Dependencias

Todas viven en `requirements.txt` y se instalan solas al correr
`INICIAR_MINI_APP.bat` (via `uv pip install -r requirements.txt`) --
no hace falta instalarlas a mano:

| Paquete | Para que se usa |
|---|---|
| `fastapi` | Servidor web de la mini-app (endpoints `/api/*`) |
| `uvicorn` | Corre el servidor FastAPI (`uvicorn app:app --port 8421`) |
| `duckdb` | Motor de consultas SQL en memoria sobre el `.parquet` local -- responde los 4 niveles (Categoria/Subcategoria/Item) sin volver a tocar BigQuery |
| `pandas` | Manipulacion de datos en `pull_data.py`/`db.py` |
| `google-cloud-bigquery` | Cliente para el pull inicial de datos (`pull_data.py`) contra `wmt-intl-cons-mx-users` |
| `google-cloud-bigquery-storage` | Acelera la descarga de BigQuery 5-10x (sin el, cae al REST endpoint, mucho mas lento) -- ver seccion "Refrescar los datos" |
| `db-dtypes` | Tipos de columna que BigQuery devuelve (fechas/decimales) legibles por pandas |
| `pyarrow` | Lectura/escritura del `.parquet` (formato de `historico_mensual_combined.parquet`) |

Requisitos fuera de Python (el `.bat` los valida y avisa si faltan):

- **`uv`** en el PATH (instalado junto con Code Puppy) -- crea el venv
  dedicado de esta mini-app e instala lo de arriba.
- **VPN de Walmart o Eagle WiFi** -- el indice de pip
  (`pypi.ci.artifacts.walmart.com`) solo responde con eso conectado.
- **`gcloud` autenticado** contra `wmt-intl-cons-mx-users` -- solo
  hace falta para el pull inicial (`pull_data.py`) y para el nivel
  Tienda-Item (consulta en vivo); el resto de la app corre 100% local
  contra el `.parquet` sin volver a tocar BigQuery.

## Cómo correrla

Doble-click a `INICIAR_MINI_APP.bat` (crea su propio venv, instala
dependencias, descarga datos si hace falta, y abre el navegador solo
en http://127.0.0.1:8421). Elige tu área en el selector de la parte de
arriba de la página (Todo el Negocio por default).

Manual, paso a paso:
```
cd catman_equipos\historico_app
uv venv
uv pip install -r requirements.txt --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
.venv\Scripts\python.exe pull_data.py
.venv\Scripts\python.exe -m uvicorn app:app --port 8421
```

## Refrescar los datos

```
.venv\Scripts\python.exe pull_data.py
```
(borra primero `historico_mensual_combined.parquet` si ya existe --
el script no sobreescribe por accidente, hay que borrarlo a mano para
forzar un refresh).

Corre `query_mensual_raw_template.sql` **una sola vez** (2025-01-01 ->
ayer, las 76 categorías del negocio completo combinadas vía
`@cat_filter`, más el join de costo/precio snapshot contra
`MDSE_INVENTORY`) y guarda `historico_mensual_combined.parquet`.

**Costo BigQuery real de la corrida del 03-sep-2026 (76 categorías):**
12.76 GB facturados (dry-run previo estimó 15.6 GB) -- 349,601 filas,
37,426 ítems distintos, 76 categorías con venta real, 21 meses. Mismo
insight de siempre: el costo lo domina el rango de fechas escaneado en
las tablas base (`SKU_DLY_POS`, `Sams_Ventas`), NO cuántas categorías
trae el filtro ni si el resultado incluye Club o no. El join de
costo/precio contra `MDSE_INVENTORY` es marginal (snapshot, no escala
con fechas). No es gratis -- no lo corras por rutina automática sin
pensarlo. **Requiere el paquete `google-cloud-bigquery-storage`** (ya
en `requirements.txt`) -- sin él, la descarga cae al REST endpoint y
puede tardar 5-10x más.

Cada click en el nivel **Tienda-Ítem** dispara un query real y chico a
BigQuery (1 solo ítem, no todo el catálogo) -- tarda unos segundos, no
es instantáneo como los otros 3 niveles. Costo marginal por click,
pero sigue siendo BigQuery real, no gratis. La Tabla de Datos NO
dispara BigQuery -- se calcula 100% del parquet local.

## Estado: PRUEBA, no producción

- No hay tarea de Windows Task Scheduler apuntando a esta carpeta.
- No está enlazada al pipeline de `catman_equipos/pipeline/` (los
  tableros estáticos con FCST de septiembre) ni a
  `rutinas/W5_Tableros_Equipos_Ecatman/` / `rutinas/W6_.../` -- son
  cosas independientes.
- `historico_mensual_combined.parquet` es un snapshot -- correr
  `pull_data.py` de nuevo (tras borrar el archivo) para refrescar.
- Publicar en Puppy Pages no aplica aquí (Puppy Pages es para HTML
  estático, esto es una app con servidor vivo -- cada quien la corre
  en su máquina con `INICIAR_MINI_APP.bat`).
- Antes de volver a correr `pull_data.py`, verifica que no haya un
  servidor de esta misma app ya corriendo (bloquea `.venv\Scripts\
  python.exe` en Windows y falla `uv venv --clear`) -- cierra la
  ventana de `INICIAR_MINI_APP.bat` o mata el proceso primero.

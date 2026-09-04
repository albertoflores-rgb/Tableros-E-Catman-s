# Pipeline Compartido -- 6 Tableros E-Catman por Equipo

Motor **genérico y parametrizado** (DRY) que genera el tablero Insights
.com de los 6 equipos de Mercancías Generales / Consumibles / Fresh:

| team_key | Carpeta en este repo | Owner | Categorías |
|---|---|---|---|
| `perecederos` | `../Congelados y deli/` | Pacheco | 42,44,38,56,72,77,76,39,57,59,91,79 |
| `impulso` | `../Impulso/` | Kevin | 1,19,28,40,48,52,55,58 |
| `seasonal` | `../Temporada/` | Nat/Dani | 7,9,10,69,12,11,16,14,18,17,51,78,85,83,92,50,94 |
| `apparel` | `../Ropa/` | Dani | 21,22,23,26,33,34,36,63,66,67 |
| `tecnologia` | `../Tecnologia/` | Valeria | 3,5,6,15,29,31,32,60,61,71,81,98 |
| `salud_bienestar` | `../Salud y Bienestar/` | Estef | 2,4,8,13,27,47,54 |

Por qué existe esto en vez de 6 copias casi-idénticas (como el tablero
de Abarrotes, que SÍ vive standalone dentro de su propia carpeta): la
lógica de merge/KPIs/movers/FCST es idéntica para los 6 equipos, lo
único que cambia es el nombre del área, el owner, y qué categorías
trae — eso vive en un solo lugar (`teams_config.py`).

## Cómo correrlo EN TU PROPIA PC (self-service, 02-sep-2026)

Cada owner de equipo puede correr esto en su propia máquina, sin
depender de Alberto. Esto es lo que necesitas de verdad, en orden:

### 1. Instalar dependencias (una sola vez)

```bash
cd Pipeline_Compartido_Equipos
uv venv
uv pip install pandas google-cloud-bigquery db-dtypes openpyxl google-cloud-bigquery-storage --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
```
`google-cloud-bigquery-storage` es opcional pero recomendado -- sin él,
la librería usa el endpoint REST (más lento, pero funciona igual).
`openpyxl` hay que instalarlo aunque no tengas el archivo de FCST (ver
punto 4) -- el import truena si falta el paquete, aunque el archivo no
se use.

### 2. Acceso a BigQuery -- con TU PROPIA cuenta de Walmart

```bash
gcloud auth application-default login
```
Y pide (si no los tienes ya) estos AD groups -- son los que de verdad
leen las tablas que usa esta query (confirmado contra el ACL real de
BigQuery, no adivinado):

| Necesitas leer | AD Group a pedir |
|---|---|
| `SKU_DLY_POS` y `MDSE_INVENTORY` (venta física + inventario) | `gcp-prod-mx-sams-reader@walmart.com` |
| `Sams_Ventas` (venta .com) | No tiene AD group abierto en el ACL -- pide acceso directo a `ricardo.bocardo0@walmart.com` (owner del dataset) o abre un ticket ServiceNow "Dataset Access Request" para `wmt-mx-dl-controlledmgzn-prod` / dataset `ecom` |

### 3. Correr el pipeline

```bash
# 1. Una sola consulta a BigQuery para los 6 equipos (barato: ~18-19GB
#    en vez de ~116GB si se corriera 1 query por equipo -- OJO: esto
#    cuesta LO MISMO sin importar si filtras a tu equipo o traes los 6,
#    porque BigQuery cobra por bytes leidos de las tablas base, no por
#    filas que sobreviven al filtro de categoria. Si varios owners la
#    corren cada quien por su lado el mismo dia, es esa misma cuenta de
#    GB repetida por cada quien -- coordina con Alberto si te preocupa
#    el costo/tiempo compartido de BQ).
python run_query_combined.py
python split_by_team.py

# 2. Pipeline de TU equipo (o --all para los 6)
cd pipeline
python run_team_pipeline.py <tu_team_key>
python run_team_pipeline.py --all
```

Cada corrida hace: `build_merge.py` → (`merge_dsv.py` solo en
Tecnologia/Seasonal/Apparel) → `finalize_data.py` → `finalize_sept.py`
→ `finalize_explorer.py` → `build_dashboard.py`. El HTML final queda en
la carpeta del equipo correspondiente (ver tabla arriba), NO aquí.

### 4. Sobre la pestaña 3 (FCST Septiembre)

Esa pestaña lee un Excel que hoy vive en el OneDrive **personal** de
Alberto (`FCST SEPT 2026 VF Curvas.xlsx`) -- todavía no es una fuente
compartida del equipo. Si corres el pipeline sin acceso a ese archivo,
**no truena** -- `finalize_sept.py` lo detecta, se salta esa pestaña
con un aviso claro ("FCST de Septiembre no disponible en este equipo")
y las pestañas 1 (Resumen, ventas + inventario) y 2 (Explorador BQ) se
generan normal, con datos completos. Si tu equipo necesita esa pestaña
funcionando, pídele a Alberto que comparta el archivo (SharePoint/Teams)
en vez de que viva solo en su OneDrive.

## Contenido de cada tablero (3 pestañas)

1. **Resumen** — KPIs .com vs Piso (YTD/MTD/L7D), insights, movers
   (Top 20 por volumen: Riesgo / Impulsar / Replicar). Sin parrilla ni
   promos todavía (a diferencia de Abarrotes) — se avisa explícito en
   cada tablero.
2. **Explorador BQ** — tabla filtrable a nivel item. En Tecnologia,
   Seasonal y Apparel trae además `Inventario_DSV` / `DSV_Proveedor` /
   `DSV_Costo` (cruce con samsdsv.com vía `Item_Nbr`, cobertura
   2-3.5% del catálogo — DSV es un proveedor específico, no todo el
   inventario).
3. **Septiembre: FCST y Riesgo** — target BP Sept 2026 (.com) vs
   tendencia YTD real, gap $/%, riesgo por categoría. Fuente:
   `FCST SEPT 2026 VF Curvas.xlsx` (hoja por equipo). Incluye
   `FCST VoBo` (forecast oficial del equipo central) como referencia.

Abarrotes usa su **propio** pipeline/archivo (`../Abarrotes/`, con
evento "A la Mexicana" y pestañas de Promos/Histórico) — no se tocó ni
se unificó con este pipeline compartido.

## 7mo tablero: Total Departamentos (03-sep-2026)

Ademas de los 6 equipos, `run_query_combined.py` pide el universo
COMPLETO de categorias (76: los 6 equipos + Abarrotes + 5 huerfanas --
ver `teams_config.py::all_cat_nbrs_universe()`), y `split_by_team.py`
tambien genera `raw_bq_item_total_total_departamentos.csv`. Esto es
**gratis**: confirmado con `bq --dry_run` que 76 categorias cuestan
EXACTAMENTE LO MISMO que 66 (el costo lo domina el escaneo completo de
las tablas base, no el filtro).

Para generar el 7mo tablero (despues de correr run_query_combined.py +
split_by_team.py):
```bash
python build_total_departamentos.py
```
Mismo pipeline generico (`pipeline/run_team_pipeline.py total_departamentos`),
sin DSV y sin pestana 3 (FCST) -- ver `Total_Departamentos/README.md`
para el detalle completo, incluyendo por que esto reemplaza a la
version ad-hoc anterior que costaba ~3.8 TB por corrida.

## Chequeo de integridad (03-sep-2026)

`validate_integrity.py` compara la venta .com de ayer contra el
promedio de los 7 dias anteriores para todo el universo -- alerta (sin
bloquear el pipeline) si cae por debajo de 30%. Barato: `Sams_Ventas`
esta particionada por dia, asi que pedir solo 8 dias es economico sin
importar el tamano del YTD completo. Se corrio para detectar a tiempo
problemas como la latencia de datos de Sept 1-2 (ver kennel/memoria del
repo, diagnostico 03-sep-2026).
```bash
python validate_integrity.py                 # universo completo, umbral 30%
python validate_integrity.py --umbral 0.20    # umbral custom
python validate_integrity.py --cats 41,43,46  # solo ciertas categorias
```

## Mini-app interactiva: Historico Mensual, Todo el Negocio (03-sep-2026)

`historico_app/` es una app FastAPI + DuckDB **separada e independiente**
de los 7 tableros HTML estaticos de arriba -- no reemplaza nada, es un
complemento interactivo (filtros, drill-down por Categoria/Subcategoria/
Item/Tienda-Item, y una Tabla de Datos con metricas mensuales YTD 2026
vs LY 2025) para cuando un tablero estatico no alcanza. Cubre las 76
categorias del negocio completo (mismo universo que Total_Departamentos).

Correr:
```bash
cd Pipeline_Compartido_Equipos/historico_app
.\INICIAR_MINI_APP.bat
```
Abre http://127.0.0.1:8421 -- ver `historico_app/README.md` para el
detalle completo (arquitectura, por que Tienda-Item usa query en vivo,
costo real de BQ del ultimo refresh, como refrescar los datos, etc.).
El repo incluye un snapshot de datos (`historico_mensual_combined.parquet`,
~9 MB) para poder correrla de inmediato sin esperar un pull de BigQuery
-- refrescalo con `pull_data.py` cuando necesites datos mas recientes.

## No versionado (`.gitignore`)

`*.csv` y `*.json` (cachés/intermedios regenerables) y `__pycache__/`.
El HTML final SÍ se versiona (va dentro de la carpeta de cada equipo).

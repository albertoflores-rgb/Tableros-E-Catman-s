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

## Cómo correrlo

Requiere `uv` + acceso a BigQuery (`gcloud auth application-default
login`) + Python con `pandas`, `google-cloud-bigquery`, `openpyxl`.

```bash
# 1. Una sola consulta a BigQuery para los 6 equipos (barato: ~19.3GB
#    en vez de ~116GB si se corriera 1 query por equipo)
python run_query_combined.py
python split_by_team.py

# 2. Pipeline por equipo (o --all para los 6)
cd pipeline
python run_team_pipeline.py <team_key>
python run_team_pipeline.py --all
```

Cada corrida hace: `build_merge.py` → (`merge_dsv.py` solo en
Tecnologia/Seasonal/Apparel) → `finalize_data.py` → `finalize_sept.py`
→ `finalize_explorer.py` → `build_dashboard.py`. El HTML final queda en
la carpeta del equipo correspondiente (ver tabla arriba), NO aquí.

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

## No versionado (`.gitignore`)

`*.csv` y `*.json` (cachés/intermedios regenerables) y `__pycache__/`.
El HTML final SÍ se versiona (va dentro de la carpeta de cada equipo).

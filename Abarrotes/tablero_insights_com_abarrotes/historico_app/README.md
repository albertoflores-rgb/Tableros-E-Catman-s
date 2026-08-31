# Mini-app: Histórico Diario 2026 vs 2025 (Abarrotes)

Prueba de arquitectura FastAPI + DuckDB para el nivel **Tienda-Ítem**
que no cupo en el tab estático de `tablero_insights_com_abarrotes.html`
(15.3M filas a grano Fecha x Club x Ítem — medido con bigquery-explorer
antes de construir nada, ver conversación del 2026-08-31).

## Qué resuelve que el tab estático no podía

| | Tab estático (tab 5) | Esta mini-app |
|---|---|---|
| Categoría / Subcategoría / Item | Sí, JSON embebido | Sí, vía DuckDB |
| Tienda-Ítem (club x item) | No cabía (15.3M filas) | Sí — DuckDB agrega al vuelo |
| Crecimiento TY vs LY | No (solo 2026) | Sí, en los 4 niveles |
| Cómo se abre | Doble-click al .html | Correr servidor + abrir localhost |

## Cómo correrla

```
cd tablero_insights_com_abarrotes\historico_app
..\..\rutinas\W4_Tablero_Insights_Com_Abarrotes\.venv\Scripts\python.exe -m pip install fastapi uvicorn duckdb --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
..\..\rutinas\W4_Tablero_Insights_Com_Abarrotes\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8420
```

Abrir http://127.0.0.1:8420

## Refrescar los datos

```
..\..\rutinas\W4_Tablero_Insights_Com_Abarrotes\.venv\Scripts\python.exe pull_data.py
```

Corre `query_diario_raw_template.sql` dos veces (2026-01-01→ayer para TY,
2025-01-01→30-ago-2025 para LY, mismo rango de días porque ni 2025 ni
2026 son bisiestos) y guarda `ty.parquet` / `ly.parquet`. `Day_Offset`
(calculado en el propio SQL, días desde el inicio de cada periodo) es lo
que alinea TY[i] con LY[i] sin depender de coincidencia de fecha
calendario exacta.

**Costo BigQuery de un refresh completo:** ~12-13 GB facturados (2
pulls de ~6GB c/u, medido con bigquery-explorer). No es gratis, no
correrlo por rutina automática sin pensarlo.

## Estado: PRUEBA, no producción

- No hay tarea de Windows Task Scheduler apuntando a esta carpeta.
- No está enlazada al pipeline de `rutinas/W4_Tablero_Insights_Com_Abarrotes/`
  (verificar `config.py` de esa rutina si hay duda -- no debe mencionar
  `historico_app`).
- `ty.parquet` / `ly.parquet` son snapshots -- correr `pull_data.py` de
  nuevo para refrescar cuando se necesite.
- Publicar en Puppy Pages no aplica aquí (Puppy Pages es para HTML
  estático, esto es una app con servidor vivo).

# -*- coding: utf-8 -*-
"""Corre query_mensual_raw_template.sql UNA SOLA VEZ para las 76
categorias del NEGOCIO COMPLETO (6 equipos E-Catman + Abarrotes + 5
categorias 'huerfanas' -- mismo universo que el tablero "Total
Departamentos", ver teams_config.all_cat_nbrs_universe()) y guarda el
resultado en un solo Parquet.

Expandido 03-sep-2026 de 72 -> 76 categorias (se agregaron las 5
huerfanas: 45 Tabaco, 62 Azucar, 70 Libros, 73 Bulk Deli, 88 Joyeria)
para que esta mini-app cubra el 100% del negocio, no solo los 6
equipos + Abarrotes -- ver AREAS en db.py, que ahora incluye una
entrada "Todo el Negocio" ademas de las 7 areas individuales.

Tambien se agrego el pull de Costo_Unit_Snapshot / Precio_Venta_
Snapshot (join contra MDSE_INVENTORY) para poder calcular margen
comercial en la tabla de metricas nueva -- ver query_mensual_raw_
template.sql, cte_costo_item.

Grano: Anio x Mes x Item (SIN Club -- ver nota en
query_mensual_raw_template.sql sobre por que se quito: un primer
intento con Club incluido produjo un dataframe de varios GB que casi
agota la RAM disponible, validado en vivo 01-sep-2026).

Por que UNA sola pasada para las 76 categorias (no varios pulls
separados): el filtro de categoria se aplica DESPUES del escaneo
completo de las tablas base (SKU_DLY_POS, Sams_Ventas) -- el costo lo
domina el rango de fechas escaneado, no cuantas categorias trae el
filtro. Ver teams_config.py / run_query_combined.py para el mismo
insight ya aplicado al pipeline de los tableros estaticos.

Costo de BQ (bytes escaneados/facturados) estimado: ~15-16 GB (escala
con los DIAS escaneados -- 2025-01-01 -> hoy -- no con las categorias;
confirmado con `bq --dry_run` en teams_config.py::
all_cat_nbrs_universe()) + un query chico adicional contra
MDSE_INVENTORY para costo/precio (no escala con fechas, es snapshot).
SIN el nivel Club el dataframe resultante es ordenes de magnitud mas
chico que el intento original, pero el costo de BQ es el mismo (el
filtro/agregacion de Club no afecta bytes escaneados). No es gratis --
no lo corras por rutina automatica sin pensarlo. Requiere el paquete
`google-cloud-bigquery-storage` instalado (ya en requirements.txt) --
sin el, `to_dataframe()` cae a REST y puede tardar 5-10x mas.

Uso:
    python pull_data.py
"""
from __future__ import annotations
import sys
from datetime import date, timedelta
from pathlib import Path

from google.cloud import bigquery

APP_DIR = Path(__file__).parent
CATMAN_DIR = APP_DIR.parent
sys.path.insert(0, str(CATMAN_DIR))

from teams_config import all_cat_nbrs_universe  # noqa: E402

PROJECT = "wmt-intl-cons-mx-users"
SQL_PATH = APP_DIR / "query_mensual_raw_template.sql"
OUT_PARQUET = APP_DIR / "historico_mensual_combined.parquet"

DATE_INI = "2025-01-01"
DATE_FIN = (date.today() - timedelta(days=1)).isoformat()  # ayer -- hoy suele venir incompleto


def run() -> None:
    if OUT_PARQUET.exists():
        print(f"{OUT_PARQUET.name} ya existe -- se salta la descarga.")
        print("Borralo si quieres forzar un refresh: borra el archivo y vuelve a correr este script.")
        return

    cats = all_cat_nbrs_universe()
    template = SQL_PATH.read_text(encoding="utf-8")
    sql = template.replace("{DATE_INI}", DATE_INI).replace("{DATE_FIN}", DATE_FIN)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("cat_filter", "INT64", cats),
        ]
    )
    client = bigquery.Client(project=PROJECT)
    print(f"Ejecutando UNA sola pasada mensual para {len(cats)} categorias (NEGOCIO COMPLETO: 6 equipos + Abarrotes + huerfanas)...")
    print(f"Rango: {DATE_INI} -> {DATE_FIN}")
    job = client.query(sql, job_config=job_config, project=PROJECT)
    df = job.to_dataframe()
    bytes_billed = getattr(job, "total_bytes_billed", None)
    if bytes_billed is not None:
        print(f"Bytes facturados por BigQuery: {bytes_billed / (1024**3):.2f} GB")

    print("Filas totales:", len(df))
    print("Items distintos:", df["ITEM_NBR"].nunique())
    print("Categorias distintas:", df["CAT_NBR"].nunique())
    print("Meses distintos:", df[["Anio", "Mes"]].drop_duplicates().shape[0])
    df.to_parquet(OUT_PARQUET, index=False)
    print("Guardado en", OUT_PARQUET)


if __name__ == "__main__":
    run()

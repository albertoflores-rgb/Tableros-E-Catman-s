# -*- coding: utf-8 -*-
"""Corre query_item_total_template.sql UNA SOLA VEZ para la union de
TODAS las categorias de los 6 equipos de E-Catman, en vez de correr
run_query_team.py 6 veces por separado.

Por que importa esto (el problema de costo que detectamos):
  El filtro `Cat_Nbr` se aplica hasta el final del query, DESPUES de
  escanear las tablas base completas (SKU_DLY_POS, Sams_Ventas,
  MDSE_INVENTORY). BigQuery cobra por bytes leidos de las columnas
  referenciadas en esas tablas, NO por filas que sobreviven al WHERE
  -- asi que 6 corridas separadas (una por equipo) pagan el mismo
  escaneo completo 6 VECES (~19.3 GB x 6 = ~116 GB). Corriendo UNA
  vez con la union de categorias y despues separando en Python
  (gratis, pandas local) el costo baja a ~19.3 GB UNA sola vez.

Uso:
    python run_query_combined.py           # jala BQ (1 sola pasada)
    python split_by_team.py                # separa el CSV combinado por equipo
"""
from pathlib import Path

from google.cloud import bigquery

from teams_config import all_cat_nbrs_combined

PROJECT = "wmt-intl-cons-mx-users"
SCRIPT_DIR = Path(__file__).parent
SQL_PATH = SCRIPT_DIR / "query_item_total_template.sql"
OUT_CSV = SCRIPT_DIR / "raw_bq_item_total_catman_combined.csv"


def run() -> None:
    cats = all_cat_nbrs_combined()
    sql = SQL_PATH.read_text(encoding="utf-8")

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("cat_filter", "INT64", cats),
        ]
    )
    client = bigquery.Client(project=PROJECT)
    print(f"Ejecutando UNA sola pasada para {len(cats)} categorias combinadas de los 6 equipos ...")
    print("Categorias:", cats)
    job = client.query(sql, job_config=job_config, project=PROJECT)
    df = job.to_dataframe()

    print("Filas totales:", len(df))
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print("Guardado en", OUT_CSV, "-- ahora corre split_by_team.py para separar por equipo (sin costo BQ adicional).")


if __name__ == "__main__":
    run()

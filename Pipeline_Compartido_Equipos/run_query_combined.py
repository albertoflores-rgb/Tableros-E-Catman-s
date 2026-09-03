# -*- coding: utf-8 -*-
"""Corre query_item_total_template.sql UNA SOLA VEZ para la union de
TODAS las categorias del universo E-Catman completo (6 equipos +
Abarrotes + 5 categorias 'huerfanas'), en vez de correr
run_query_team.py N veces por separado.

Por que importa esto (el problema de costo que detectamos):
  El filtro `Cat_Nbr` se aplica hasta el final del query, DESPUES de
  escanear las tablas base completas (SKU_DLY_POS, Sams_Ventas,
  MDSE_INVENTORY). BigQuery cobra por bytes leidos de las columnas
  referenciadas en esas tablas, NO por filas que sobreviven al WHERE
  -- asi que N corridas separadas (una por equipo) pagan el mismo
  escaneo completo N VECES. Corriendo UNA vez con la union de TODAS
  las categorias y despues separando en Python (gratis, pandas local)
  el costo se queda igual (~18-19 GB) sin importar si el filtro trae
  66 categorias (solo los 6 equipos) o 76 (el universo completo).

  Confirmado con `bq --dry_run` (03-sep-2026, Fase 2 'Total
  Departamentos'): 76 categorias escanean EXACTAMENTE lo mismo que 66
  -- por eso desde esta version se pide siempre el universo completo
  en una sola pasada: alimenta los 6 tableros de equipo Y el 7mo
  tablero 'Total Departamentos' sin pagar un query adicional.

Uso:
    python run_query_combined.py           # jala BQ (1 sola pasada, universo completo)
    python split_by_team.py                # separa el CSV combinado por equipo + total_departamentos
"""
from pathlib import Path

from google.cloud import bigquery

from teams_config import all_cat_nbrs_universe

PROJECT = "wmt-intl-cons-mx-users"
SCRIPT_DIR = Path(__file__).parent
SQL_PATH = SCRIPT_DIR / "query_item_total_template.sql"
OUT_CSV = SCRIPT_DIR / "raw_bq_item_total_catman_combined.csv"


def run() -> None:
    cats = all_cat_nbrs_universe()
    sql = SQL_PATH.read_text(encoding="utf-8")

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("cat_filter", "INT64", cats),
        ]
    )
    client = bigquery.Client(project=PROJECT)
    print(f"Ejecutando UNA sola pasada para {len(cats)} categorias del universo completo (6 equipos + Abarrotes + huerfanas) ...")
    print("Categorias:", cats)
    job = client.query(sql, job_config=job_config, project=PROJECT)
    df = job.to_dataframe()

    print("Filas totales:", len(df))
    bytes_billed = job.total_bytes_billed or 0
    print(f"Bytes billed reales: {bytes_billed:,} ({bytes_billed/1e9:.3f} GB)")
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print("Guardado en", OUT_CSV, "-- ahora corre split_by_team.py para separar por equipo + total_departamentos (sin costo BQ adicional).")


if __name__ == "__main__":
    run()


# -*- coding: utf-8 -*-
"""Ejecuta el query Item Total (filtrado a categorias Abarrotes) y guarda CSV."""
import sys
from google.cloud import bigquery

PROJECT = "wmt-intl-cons-mx-users"
SQL_PATH = "query_item_total_abarrotes.sql"
OUT_CSV = "raw_bq_item_total.csv"

with open(SQL_PATH, "r", encoding="utf-8") as f:
    sql = f.read()

client = bigquery.Client(project=PROJECT)
print("Ejecutando query contra", PROJECT, "...")
job = client.query(sql, project=PROJECT)
df = job.to_dataframe()
print("Filas:", len(df))
print(df.columns.tolist())
df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print("Guardado en", OUT_CSV)

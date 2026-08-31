# -*- coding: utf-8 -*-
"""Corre query_diario_abarrotes.sql contra BigQuery y guarda el resultado
en raw_diario_abarrotes.csv. Grano: Fecha x Categoria x Subcategoria x
Item (SIN club/tienda -- ver header del .sql para el porque).

Requiere el venv de la rutina W4 (bigquery + pandas + db-dtypes) -- no
se creo un venv nuevo para no duplicar dependencias ya declaradas."""
from google.cloud import bigquery
import pandas as pd

PROJECT = "wmt-intl-cons-mx-users"

with open("query_diario_abarrotes.sql", "r", encoding="utf-8") as f:
    query = f.read()

client = bigquery.Client(project=PROJECT)
print("Ejecutando query contra", PROJECT, "...")
df = client.query(query).to_dataframe()

print("Filas:", len(df))
print("Columnas:", list(df.columns))
print("Rango de fechas:", df["Fecha"].min(), "->", df["Fecha"].max())
print("Items distintos:", df["ITEM_NBR"].nunique())
print("Categorias distintas:", df["CAT_NBR"].nunique())
print("Subcategorias distintas:", df["SUBCAT_NBR"].nunique())

df.to_csv("raw_diario_abarrotes.csv", index=False)
print("Guardado en raw_diario_abarrotes.csv")

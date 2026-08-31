# -*- coding: utf-8 -*-
"""Corre query_diario_raw_template.sql dos veces (TY 2026, LY 2025) y
guarda cada resultado en Parquet. Grano: Fecha x Club x Item (completo,
sin colapsar) -- esto es lo que necesita la mini-app para poder mostrar
el nivel Tienda-Item, a diferencia del pull agregado que usa el tab
estatico (finalize_historico.py, en la carpeta padre).

2025 y 2026 son ambos NO bisiestos, asi que el rango Ene1->Ago30 tiene
el mismo numero de dias en los dos anios -- Day_Offset (calculado en el
propio SQL) alinea TY[i] con LY[i] sin ambiguedad.
"""
from google.cloud import bigquery
import pandas as pd

PROJECT = "wmt-intl-cons-mx-users"

PERIODS = {
    "TY": ("2026-01-01", "2026-08-30"),
    "LY": ("2025-01-01", "2025-08-30"),
}

with open("query_diario_raw_template.sql", "r", encoding="utf-8") as f:
    template = f.read()

client = bigquery.Client(project=PROJECT)

import os

for periodo, (date_ini, date_fin) in PERIODS.items():
    out_path = f"{periodo.lower()}.parquet"
    if os.path.exists(out_path):
        print(f"--- {periodo}: {out_path} ya existe, se salta (borralo si quieres forzar un refresh) ---")
        continue
    sql = template.replace("{DATE_INI}", date_ini).replace("{DATE_FIN}", date_fin)
    print(f"--- {periodo}: {date_ini} -> {date_fin} ---")
    df = client.query(sql).to_dataframe()
    df["Periodo"] = periodo
    print("  Filas:", len(df))
    print("  Items distintos:", df["ITEM_NBR"].nunique())
    print("  Clubs distintos:", df["CLUB_NBR"].nunique())
    print("  Dias distintos:", df["Fecha"].nunique())
    df.to_parquet(out_path, index=False)
    print("  Guardado en", out_path)

print("Listo.")

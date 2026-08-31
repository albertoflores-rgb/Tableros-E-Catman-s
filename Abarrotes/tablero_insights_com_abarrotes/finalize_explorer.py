# -*- coding: utf-8 -*-
"""Genera explorer_data.json: dataset completo de items Abarrotes (BQ) en
formato compacto (columnas + filas como arrays) para la pestana de
"Explorador BQ" -- filtros por campo descriptivo + orden por cualquier
columna numerica, todo del lado del cliente (sin backend)."""
import pandas as pd
import json

full = pd.read_csv('merged_full.csv')

COLUMNS = [
    'Item_Nbr', 'Item_Desc_1', 'Cat_Desc', 'Sub_Cat_Desc', 'Proveedor',
    'Tipo', 'Status', 'Semaforo_OH', 'En_Parrilla', 'Promo_Vigente',
    'Top_L7D_Cat',
    'Inv_Pzas_Total', 'Inv_MXN_Total', 'Club_con_Inventario', 'Precio_Venta',
    'Piso_Pzas_YTD', 'Piso_Pesos_YTD', 'Com_Pzas_YTD', 'Com_Pesos_YTD',
    'Crecimiento_Piso_Pesos_YTD', 'Crecimiento_Com_Pesos_YTD', 'Share_Com_YTD',
    'Piso_Pzas_MTD', 'Piso_Pesos_MTD', 'Com_Pzas_MTD', 'Com_Pesos_MTD',
    'Crecimiento_Piso_Pesos_MTD', 'Crecimiento_Com_Pesos_MTD', 'Share_Com_MTD',
    'Piso_Pzas_L7D', 'Piso_Pesos_L7D', 'Com_Pzas_L7D', 'Com_Pesos_L7D',
    'Crecimiento_Piso_Pesos_L7D', 'Crecimiento_Com_Pesos_L7D', 'Share_Com_L7D',
    # LY "crudo" oculto en la UI -- solo se usa para totalizar % de crecimiento
    # de forma exacta (suma TY vs suma LY) en vez de promediar porcentajes.
    'Piso_Pesos_YTDLY', 'Com_Pesos_YTDLY',
    'Piso_Pesos_MTDLY', 'Com_Pesos_MTDLY',
    'Piso_Pesos_L7DLY', 'Com_Pesos_L7DLY',
]

HIDDEN_FIELDS = [
    'Piso_Pesos_YTDLY', 'Com_Pesos_YTDLY',
    'Piso_Pesos_MTDLY', 'Com_Pesos_MTDLY',
    'Piso_Pesos_L7DLY', 'Com_Pesos_L7DLY',
]

# Campos descriptivos (categoricos) que llevaran dropdown de filtro en la UI.
FILTER_FIELDS = ['Cat_Desc', 'Sub_Cat_Desc', 'Proveedor', 'Tipo', 'Status', 'Semaforo_OH']

# Campos numericos ordenables (mayor a menor / menor a mayor).
NUMERIC_FIELDS = [
    'Top_L7D_Cat', 'Inv_Pzas_Total', 'Inv_MXN_Total', 'Club_con_Inventario', 'Precio_Venta',
    'Piso_Pzas_YTD', 'Piso_Pesos_YTD', 'Com_Pzas_YTD', 'Com_Pesos_YTD',
    'Crecimiento_Piso_Pesos_YTD', 'Crecimiento_Com_Pesos_YTD', 'Share_Com_YTD',
    'Piso_Pzas_MTD', 'Piso_Pesos_MTD', 'Com_Pzas_MTD', 'Com_Pesos_MTD',
    'Crecimiento_Piso_Pesos_MTD', 'Crecimiento_Com_Pesos_MTD', 'Share_Com_MTD',
    'Piso_Pzas_L7D', 'Piso_Pesos_L7D', 'Com_Pzas_L7D', 'Com_Pesos_L7D',
    'Crecimiento_Piso_Pesos_L7D', 'Crecimiento_Com_Pesos_L7D', 'Share_Com_L7D',
]


def clean_value(v, col):
    if pd.isna(v):
        return None
    if col in ('En_Parrilla', 'Promo_Vigente'):
        return bool(v)
    if col in NUMERIC_FIELDS or col in HIDDEN_FIELDS:
        return round(float(v), 4)
    return str(v)


rows = []
for _, r in full.iterrows():
    rows.append([clean_value(r[c], c) for c in COLUMNS])

filter_options = {
    f: sorted([v for v in full[f].dropna().unique().tolist()])
    for f in FILTER_FIELDS
}

data = {
    "columns": COLUMNS,
    "filter_fields": FILTER_FIELDS,
    "numeric_fields": NUMERIC_FIELDS,
    "hidden_fields": HIDDEN_FIELDS,
    "filter_options": filter_options,
    "rows": rows,
}

with open('explorer_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print("Filas exportadas:", len(rows))
print("Columnas:", COLUMNS)
import os
print("Tamano JSON (KB):", round(os.path.getsize('explorer_data.json') / 1024, 1))

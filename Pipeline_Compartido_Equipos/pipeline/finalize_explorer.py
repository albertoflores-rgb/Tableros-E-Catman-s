# -*- coding: utf-8 -*-
"""finalize_explorer.py generico -- explorer_data.json (Tab 2) para
cualquier equipo. Uso: python finalize_explorer.py <team_key>
"""
import sys
import pandas as pd
import json

from _common import team_dir, get_team_cfg

team_key = sys.argv[1]
get_team_cfg(team_key)
out_dir = team_dir(team_key)

full = pd.read_csv(out_dir / 'merged_full.csv', low_memory=False)

COLUMNS = [
    'Item_Nbr', 'Item_Nbr_Raw', 'UPC', 'Item_Desc_1', 'Cat_Desc', 'Sub_Cat_Desc', 'Proveedor',
    'Tipo', 'Status', 'Semaforo_OH', 'Top_L7D_Cat',
    'Inv_Pzas_Total', 'Inv_MXN_Total', 'Club_con_Inventario', 'Precio_Venta',
    'Inventario_DSV', 'DSV_Proveedor', 'DSV_Costo',
    'Piso_Pzas_YTD', 'Piso_Pesos_YTD', 'Com_Pzas_YTD', 'Com_Pesos_YTD',
    'Crecimiento_Piso_Pesos_YTD', 'Crecimiento_Com_Pesos_YTD', 'Share_Com_YTD',
    'Piso_Pzas_MTD', 'Piso_Pesos_MTD', 'Com_Pzas_MTD', 'Com_Pesos_MTD',
    'Crecimiento_Piso_Pesos_MTD', 'Crecimiento_Com_Pesos_MTD', 'Share_Com_MTD',
    'Piso_Pzas_L7D', 'Piso_Pesos_L7D', 'Com_Pzas_L7D', 'Com_Pesos_L7D',
    'Crecimiento_Piso_Pesos_L7D', 'Crecimiento_Com_Pesos_L7D', 'Share_Com_L7D',
    'Piso_Pesos_YTDLY', 'Com_Pesos_YTDLY',
    'Piso_Pesos_MTDLY', 'Com_Pesos_MTDLY',
    'Piso_Pesos_L7DLY', 'Com_Pesos_L7DLY',
]
COLUMNS = [c for c in COLUMNS if c in full.columns]  # Item_Nbr_Raw/UPC pueden faltar en pulls viejos

HIDDEN_FIELDS = [c for c in [
    'Item_Nbr_Raw', 'UPC',
    'Piso_Pesos_YTDLY', 'Com_Pesos_YTDLY',
    'Piso_Pesos_MTDLY', 'Com_Pesos_MTDLY',
    'Piso_Pesos_L7DLY', 'Com_Pesos_L7DLY',
] if c in COLUMNS]

FILTER_FIELDS = ['Cat_Desc', 'Sub_Cat_Desc', 'Proveedor', 'Tipo', 'Status', 'Semaforo_OH']

NUMERIC_FIELDS = [c for c in [
    'Top_L7D_Cat', 'Inv_Pzas_Total', 'Inv_MXN_Total', 'Club_con_Inventario', 'Precio_Venta',
    'Inventario_DSV', 'DSV_Costo',
    'Piso_Pzas_YTD', 'Piso_Pesos_YTD', 'Com_Pzas_YTD', 'Com_Pesos_YTD',
    'Crecimiento_Piso_Pesos_YTD', 'Crecimiento_Com_Pesos_YTD', 'Share_Com_YTD',
    'Piso_Pzas_MTD', 'Piso_Pesos_MTD', 'Com_Pzas_MTD', 'Com_Pesos_MTD',
    'Crecimiento_Piso_Pesos_MTD', 'Crecimiento_Com_Pesos_MTD', 'Share_Com_MTD',
    'Piso_Pzas_L7D', 'Piso_Pesos_L7D', 'Com_Pzas_L7D', 'Com_Pesos_L7D',
    'Crecimiento_Piso_Pesos_L7D', 'Crecimiento_Com_Pesos_L7D', 'Share_Com_L7D',
] if c in COLUMNS]


def clean_value(v, col):
    if pd.isna(v):
        return None
    if col in NUMERIC_FIELDS or col in HIDDEN_FIELDS:
        try:
            return round(float(v), 4)
        except (TypeError, ValueError):
            return str(v)
    return str(v)


rows = [[clean_value(r[c], c) for c in COLUMNS] for _, r in full.iterrows()]

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

with open(out_dir / 'explorer_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"[{team_key}] Filas exportadas:", len(rows))

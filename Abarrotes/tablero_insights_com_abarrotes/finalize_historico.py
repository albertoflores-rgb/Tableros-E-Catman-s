# -*- coding: utf-8 -*-
"""Genera historico_data.json: series diarias 2026 YTD para 3 niveles
(Categoria, Subcategoria, Item), a partir de raw_diario_abarrotes.csv
(grano Fecha x Cat x Subcat x Item, ya agregado en BigQuery -- ver
query_diario_abarrotes.sql).

Estructura compartida por los 3 niveles (mismo shape para que el JS del
tab reuse una sola funcion de graficado):
  {
    "dates": ["2026-01-01", ..., "2026-08-30"],          # eje X comun
    "entities": [{"key": "...", "label": "...", ...}],    # para el selector
    "series": { "<key>": {"pzas_fisico": [...], "pesos_fisico": [...],
                           "pzas_com": [...], "pesos_com": [...],
                           "pzas_total": [...], "pesos_total": [...]} }
  }
Cada array de "series" esta alineado POSICIONALMENTE a "dates" (relleno
con 0 en los dias sin venta de esa entidad) -- asi el JS no tiene que
resolver fechas faltantes, solo indexar por posicion.
"""
import pandas as pd
import json

RAW_METRICS = ['Venta_Pzas_Fisico', 'Venta_Pesos_Fisico', 'Venta_Pzas_Com', 'Venta_Pesos_Com']
# OJO: NO se guarda pzas_total/pesos_total -- son fisico+com, se calculan
# en el JS al vuelo (evita duplicar ~33% del JSON con datos derivados).

df = pd.read_csv('raw_diario_abarrotes.csv', parse_dates=['Fecha'])
df['Fecha'] = df['Fecha'].dt.strftime('%Y-%m-%d')

ALL_DATES = sorted(df['Fecha'].unique().tolist())
DATE_IDX = {d: i for i, d in enumerate(ALL_DATES)}
N_DATES = len(ALL_DATES)


def build_level(group_cols, key_col, label_col, meta_cols=None):
    """group_cols: columnas para el GROUP BY (incluye Fecha implicito).
    key_col: cual de group_cols usar como key de 'entities'/'series'.
    label_col: columna a mostrar como nombre legible.
    meta_cols: columnas extra a copiar en cada entidad (ej. Cat_Nbr para
    poder filtrar Subcategoria/Item por categoria en la UI)."""
    meta_cols = meta_cols or []
    agg = (
        df.groupby(['Fecha'] + group_cols, as_index=False)[RAW_METRICS]
        .sum()
    )
    entities = {}
    series = {}
    for _, row in agg.iterrows():
        key = str(row[key_col])
        if key not in series:
            series[key] = {
                'pzas_fisico': [0.0] * N_DATES, 'pesos_fisico': [0.0] * N_DATES,
                'pzas_com': [0.0] * N_DATES, 'pesos_com': [0.0] * N_DATES,
            }
            entities[key] = {
                'key': key,
                'label': str(row[label_col]),
                **{mc.lower(): (None if pd.isna(row[mc]) else row[mc]) for mc in meta_cols},
            }
        idx = DATE_IDX[row['Fecha']]
        series[key]['pzas_fisico'][idx] = round(float(row['Venta_Pzas_Fisico']), 2)
        series[key]['pesos_fisico'][idx] = round(float(row['Venta_Pesos_Fisico']), 2)
        series[key]['pzas_com'][idx] = round(float(row['Venta_Pzas_Com']), 2)
        series[key]['pesos_com'][idx] = round(float(row['Venta_Pesos_Com']), 2)

    # Orden por volumen total de pesos (fisico+com) descendente -- las
    # entidades mas relevantes aparecen primero en cualquier selector.
    def total_pesos(key):
        s = series[key]
        return sum(s['pesos_fisico']) + sum(s['pesos_com'])

    entity_list = sorted(entities.values(), key=lambda e: total_pesos(e['key']), reverse=True)
    return entity_list, series


cat_entities, cat_series = build_level(
    ['CAT_NBR', 'CAT_NOMBRE'], 'CAT_NBR', 'CAT_NOMBRE',
)
subcat_entities, subcat_series = build_level(
    ['SUBCAT_NBR', 'SUBCAT_NOMBRE', 'CAT_NBR', 'CAT_NOMBRE'], 'SUBCAT_NBR', 'SUBCAT_NOMBRE',
    meta_cols=['CAT_NBR', 'CAT_NOMBRE'],
)
item_entities, item_series = build_level(
    ['ITEM_NBR', 'ITEM_DESC_1', 'CAT_NBR', 'CAT_NOMBRE', 'SUBCAT_NBR', 'SUBCAT_NOMBRE'],
    'ITEM_NBR', 'ITEM_DESC_1',
    meta_cols=['CAT_NBR', 'CAT_NOMBRE', 'SUBCAT_NBR', 'SUBCAT_NOMBRE'],
)

data = {
    'dates': ALL_DATES,
    'levels': {
        'categoria': {'entities': cat_entities, 'series': cat_series},
        'subcategoria': {'entities': subcat_entities, 'series': subcat_series},
        'item': {'entities': item_entities, 'series': item_series},
    },
}

with open('historico_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print('Dias:', N_DATES, '(', ALL_DATES[0], '->', ALL_DATES[-1], ')')
print('Categorias:', len(cat_entities))
print('Subcategorias:', len(subcat_entities))
print('Items:', len(item_entities))
import os
print('Tamano JSON (KB):', round(os.path.getsize('historico_data.json') / 1024, 1))

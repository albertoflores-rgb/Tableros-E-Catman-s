# -*- coding: utf-8 -*-
"""Genera sept_data.json para la pestana 4 (FCST Septiembre + Riesgo).

Fuentes:
  - "FCST Septiembre 2026.xlsx" (OneDrive, hoja Abarrotes): target .com por
    categoria (fila 33) y su comparable LY / Sept-2025 (fila 79).
  - cat_agg.csv: crecimiento YoY MTD/L7D real que ya trae el tablero.
  - merged_full.csv: catalogo item-level para armar accionables de septiembre.
  - reporte_internal_search_boosteos.html: terminos de busqueda prioritarios
    ya identificados (varios marcados Fiestas Patrias).
"""
import json
import os
import re
import pandas as pd

# ---------- 1. Leer FCST Septiembre (target .com por categoria + comparable LY) ----------
base = r"C:\Users\a0f07dn\OneDrive - Walmart Inc\W2"
sams_dir = os.path.join(base, [i for i in os.listdir(base) if i.lower().startswith("sam")][0])
fcst_path = os.path.join(sams_dir, "E-Catman", "FCST", "FCST Septiembre 2026.xlsx")

import openpyxl
wb = openpyxl.load_workbook(fcst_path, data_only=True)
ws = wb['Abarrotes']

# Columnas fila 33/79: 4=cat41, 6=cat46, 8=cat49, 10=cat53, 12=cat43, 14=cat68, 16=Total
COL_BY_CAT = {41: 4, 46: 6, 49: 8, 53: 10, 43: 12, 68: 14}
fcst_row = {c: ws.cell(row=33, column=col).value for c, col in COL_BY_CAT.items()}
fcst_total = ws.cell(row=33, column=16).value
ly_row = {c: ws.cell(row=79, column=col + 1).value for c, col in COL_BY_CAT.items()}
ly_total = sum(ly_row.values())

# ---------- 2. Crecimiento real MTD/L7D por categoria (ya calculado en el tablero) ----------
cat_agg = pd.read_csv('cat_agg.csv').set_index('Cat_Nbr')

categorias = []
for cat_nbr, fcst_val in fcst_row.items():
    cat_desc = cat_agg.loc[cat_nbr, 'Cat_Desc']
    ly_val = ly_row[cat_nbr]
    crec_mtd = cat_agg.loc[cat_nbr, 'Crec_Com_MTD']
    crec_l7d = cat_agg.loc[cat_nbr, 'Crec_Com_L7D']
    com_mtd_actual = cat_agg.loc[cat_nbr, 'Com_Pesos_MTD']
    growth_needed = (fcst_val - ly_val) / ly_val
    trend_estimate = ly_val * (1 + crec_l7d)
    gap = trend_estimate - fcst_val
    gap_pct = gap / fcst_val
    if crec_l7d < growth_needed - 0.05:
        risk = 'Alto'
    elif crec_l7d < growth_needed:
        risk = 'Moderado'
    else:
        risk = 'Bajo'
    categorias.append({
        'cat_nbr': int(cat_nbr), 'cat_desc': cat_desc,
        'fcst_sept': round(fcst_val, 2), 'ly_sept': round(ly_val, 2),
        'growth_needed': round(growth_needed, 4),
        'crec_mtd_actual': round(float(crec_mtd), 4), 'crec_l7d_actual': round(float(crec_l7d), 4),
        'com_mtd_actual': round(float(com_mtd_actual), 2),
        'trend_estimate': round(trend_estimate, 2), 'gap': round(gap, 2), 'gap_pct': round(gap_pct, 4),
        'risk': risk,
    })
categorias.sort(key=lambda c: c['fcst_sept'], reverse=True)

trend_total = sum(c['trend_estimate'] for c in categorias)

# Crecimiento MTD/L7D total real de .com Abarrotes -- se lee de dashboard_data.json
# (pestana 1), NUNCA se hardcodea aqui para que no se desactualice con el resto
# del tablero cuando se corre la rutina diaria.
with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    tab1_kpis = json.load(f)['kpis']

kpis = {
    'fcst_total': round(fcst_total, 2), 'ly_total': round(ly_total, 2),
    'growth_needed_total': round((fcst_total - ly_total) / ly_total, 4),
    'crec_mtd_actual_total': tab1_kpis['com_mtd_growth'],
    'crec_l7d_actual_total': tab1_kpis['com_l7d_growth'],
    'trend_total': round(trend_total, 2),
    'gap_total': round(trend_total - fcst_total, 2),
    'gap_pct_total': round((trend_total - fcst_total) / fcst_total, 4),
}

# ---------- 3. Item-level: subcategorias de Fiestas Patrias / boost de busqueda ----------
full = pd.read_csv('merged_full.csv')

TARGET_SUBCATS = {
    ' MAYONESA (INDIVIDUAL)': ('Mayonesa (boost busqueda)', True),
    ' CAFE. SOLUBLE': ('Nescafe/Cafe (boost busqueda)', False),
    ' LACTEOS CULINARIOS': ('Media crema/Carnation/Clavel/Lechera (FP guisos)', True),
    ' MEZCLAS DE ESPECIAS Y SAZONADORES': ('Maggi/Knorr (FP guisos)', True),
    ' SALSAS PARA LA MESA': ('Salsa inglesa (FP)', True),
    ' LECHE. ENTERA': ('Leche entera (boost busqueda)', False),
    ' CEREAL': ('Cereal (FP)', True),
    ' UNTABLES': ('Nutella (boost busqueda)', False),
    ' CAFE. SUSTITUTO DE CREMA': ('Coffee-Mate (boost busqueda)', False),
    ' TOMATE': ('Pure de tomate (FP mole/guisos)', True),
    ' CALDOS. POLLO': ('Caldo de pollo (FP pozole)', True),
    ' SALSAS PARA COCINAR': ('Salsa (FP)', True),
    ' MOLE': ('Mole (FP alta prioridad)', True),
    ' ACEITE (INDIVIDUAL)': ('Aceite (FP)', True),
    ' GALLETAS': ('Galletas/Oreo/Saladitas (boost busqueda)', False),
    ' EDULCORANTES': ('Splenda (boost busqueda)', False),
    ' MODIFICADORES DE LECHE': ('Nesquik (boost busqueda)', False),
}
sub = full[full['Sub_Cat_Desc'].isin(TARGET_SUBCATS.keys())].copy()
sub['Boost_Motivo'] = sub['Sub_Cat_Desc'].map(lambda s: TARGET_SUBCATS[s][0])
sub['Fiestas_Patrias'] = sub['Sub_Cat_Desc'].map(lambda s: TARGET_SUBCATS[s][1])
sub['Share_Com_MTD_calc'] = sub['Com_Pesos_MTD'] / (sub['Com_Pesos_MTD'] + sub['Piso_Pesos_MTD'])


def item_row(r):
    return {
        'item_nbr': int(r['Item_Nbr']), 'item_desc': r['Item_Desc_1'], 'cat_desc': r['Cat_Desc'],
        'sub_cat_desc': r['Sub_Cat_Desc'].strip(), 'boost_motivo': r['Boost_Motivo'],
        'fiestas_patrias': bool(r['Fiestas_Patrias']),
        'piso_mtd': round(float(r['Piso_Pesos_MTD']), 2), 'com_mtd': round(float(r['Com_Pesos_MTD']), 2),
        'share_com_mtd': round(float(r['Share_Com_MTD_calc']), 4),
        'crec_com_mtd': (round(float(r['Crecimiento_Com_Pesos_MTD']), 4) if pd.notna(r['Crecimiento_Com_Pesos_MTD']) else None),
        'crec_com_l7d': (round(float(r['Crecimiento_Com_Pesos_L7D']), 4) if pd.notna(r['Crecimiento_Com_Pesos_L7D']) else None),
        'en_parrilla': bool(r['En_Parrilla']), 'promo_vigente': bool(r['Promo_Vigente']),
        'semaforo': r['Semaforo_OH'],
    }


# Apagar incendios: gran volumen fisico, .com cayendo fuerte en L7D.
apagar = sub[(sub['Piso_Pesos_MTD'] > 5_000_000) & (sub['Crecimiento_Com_Pesos_L7D'] < -0.20)]
apagar = apagar.sort_values('Piso_Pesos_MTD', ascending=False).head(10)

# Doblar apuesta: ya en parrilla+promo, momentum sostenido (MTD y L7D positivos).
doblar = sub[
    sub['En_Parrilla'] & sub['Promo_Vigente']
    & (sub['Crecimiento_Com_Pesos_MTD'] > 0.20) & (sub['Crecimiento_Com_Pesos_L7D'] > 0)
]
doblar = doblar.sort_values('Com_Pesos_MTD', ascending=False).head(12)

# Blanco total: demanda fisica real, sin promo, mix .com por debajo del promedio Abarrotes (~9.8%).
blanco = sub[(sub['Piso_Pesos_MTD'] > 2_000_000) & (~sub['Promo_Vigente']) & (sub['Share_Com_MTD_calc'] < 0.09)]
blanco = blanco.sort_values('Piso_Pesos_MTD', ascending=False).head(12)

items = {
    'apagar_incendios': [item_row(r) for _, r in apagar.iterrows()],
    'doblar_apuesta': [item_row(r) for _, r in doblar.iterrows()],
    'blanco_total': [item_row(r) for _, r in blanco.iterrows()],
}

# ---------- 4. Contexto del reporte de boosteos de busqueda (terminos Fiestas Patrias) ----------
boost_html = open('../reporte_internal_search_boosteos.html', encoding='utf-8').read()
m = re.search(r'const DATA = (\{.*?\});', boost_html, re.DOTALL)
boost_data = json.loads(m.group(1))
sept_kw_ctx = {
    'fiestas_26_top': boost_data['sept_kw'].get('fiestas_26_top', []),
    'fiestas_26_count': boost_data['sept_kw'].get('fiestas_26_count'),
    'climbers': boost_data['sept_kw'].get('climbers', []),
}

# ---------- 5. Insights ejecutivos ----------
def fmt_pct(x):
    sign = '+' if x >= 0 else ''
    return f"{sign}{x*100:.1f}%"


insights_top = [
    f"<strong>[FCST] El objetivo de septiembre es {fmt_pct(kpis['growth_needed_total'])} YoY</strong> vs Sept 2025 "
    f"(${ly_total/1e6:.1f}M &rarr; ${fcst_total/1e6:.1f}M) &mdash; mucho mas modesto que el {fmt_pct(kpis['crec_mtd_actual_total'])} que trajimos en el MTD de agosto, "
    f"pero por encima del {fmt_pct(kpis['crec_l7d_actual_total'])} de la ultima semana.",
    (
        f"<strong>[Riesgo] Si la ultima semana es la nueva normalidad</strong> (no un bache), el estimado de septiembre sale en "
        f"${kpis['trend_total']/1e6:.1f}M &mdash; un faltante de ${abs(kpis['gap_total'])/1e6:.1f}M ({fmt_pct(kpis['gap_pct_total'])}) vs el target."
        if kpis['gap_total'] < 0 else
        f"<strong>[Positivo] Aun con la desaceleracion de la ultima semana</strong>, el estimado de tendencia (${kpis['trend_total']/1e6:.1f}M) ya supera el target."
    ),
    "<strong>[Concentracion] El riesgo esta concentrado en Aceites, Granos & Aderezos y Pastas y Condimentos</strong> "
    "&mdash; ambas categorias vienen desacelerando fuerte en L7D justo cuando el FCST les pide mas crecimiento, no menos.",
    f"<strong>[Accionables] {len(items['apagar_incendios'])} items</strong> con alto volumen en Piso estan cayendo fuerte en .com "
    f"(candidatos a 'apagar incendio' antes de septiembre), <strong>{len(items['doblar_apuesta'])} items</strong> ya tienen momentum "
    f"sostenido para escalar, y <strong>{len(items['blanco_total'])} items</strong> tienen demanda fisica real pero cero promo vigente.",
]

data = {
    'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
    'kpis': kpis,
    'categorias': categorias,
    'items': items,
    'sept_kw_context': sept_kw_ctx,
    'insights_top': insights_top,
}

with open('sept_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('KPIs:', json.dumps(kpis, indent=2, ensure_ascii=False))
print('Categorias:', len(categorias))
print('Items:', {k: len(v) for k, v in items.items()})
print('Guardado sept_data.json')

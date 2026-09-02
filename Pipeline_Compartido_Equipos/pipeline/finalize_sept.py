# -*- coding: utf-8 -*-
"""finalize_sept.py generico -- pestana 3 (Septiembre: FCST y Riesgo)
para cualquier equipo (excepto Abarrotes, que ya tiene su propio
finalize_sept.py leyendo un archivo distinto y mas rico en contenido
especifico: AMX, Fiestas Patrias, accionables item-level).

Fuente: "FCST SEPT 2026 VF Curvas.xlsx" (OneDrive, E-Catman/FCST/) --
1 hoja por equipo con columnas 'sept 2025' (LY), 'BP sept 2026' (target,
SOLO .com, confirmado por Alberto) y 'FCST VoBo' (forecast oficial del
equipo central, se muestra como referencia adicional).

Uso: python finalize_sept.py <team_key>
"""
import sys
import os
import re
import json
import pandas as pd
import openpyxl

from _common import team_dir, get_team_cfg

team_key = sys.argv[1]
cfg = get_team_cfg(team_key)
area = cfg['area']
out_dir = team_dir(team_key)

SHEET_MAP = {
    'perecederos': 'Fresh',
    'salud_bienestar': 'Consumibles',
    'impulso': 'Impulso',
    'seasonal': 'Temporada',
    'apparel': 'Ropa',
    'tecnologia': 'Tecnología',
}
if team_key not in SHEET_MAP:
    raise SystemExit(
        f"[{team_key}] No tiene hoja de FCST mapeada (SHEET_MAP). "
        f"Abarrotes usa su propio finalize_sept.py -- no corre este generico."
    )
sheet_name = SHEET_MAP[team_key]


def norm(s):
    return ' '.join(str(s).lower().split()) if s is not None else ''


# ---------- 1. Leer FCST SEPT 2026 VF Curvas.xlsx ----------
# Este archivo vive HOY en el OneDrive personal de Alberto -- no es una
# fuente compartida del equipo todavia. En cualquier maquina que no sea
# la suya esto va a fallar (OneDrive no existe ahi), y eso NO debe
# tumbar el resto del tablero: Tabs 1 (Resumen ventas+inventario) y 2
# (Explorador BQ) no dependen de este archivo para nada, solo la pestana
# 3 (FCST) se queda sin datos con un aviso claro en vez de reventar.
#
# OJO: NO hardcodear la ruta completa -- la carpeta intermedia se ha
# movido antes (de "OneDrive\W2\Sam's\..." a "OneDrive\Seguros
# 2026\W2\Sam's\..." sin avisar). Se busca el archivo por NOMBRE con
# rglob desde la raiz del OneDrive, asi sobrevive a que Alberto siga
# reorganizando carpetas.
import pathlib
try:
    onedrive_root = pathlib.Path(r"C:\Users\a0f07dn\OneDrive - Walmart Inc")
    fcst_path = next(onedrive_root.rglob("FCST SEPT 2026 VF Curvas.xlsx"))
    wb = openpyxl.load_workbook(fcst_path, data_only=True, read_only=True)
    ws = wb[sheet_name]
except (FileNotFoundError, StopIteration, KeyError) as exc:
    print(
        f"[{team_key}] AVISO: no se encontro el archivo FCST ({exc!r}) -- esta maquina "
        f"probablemente no tiene acceso a esa carpeta de OneDrive. Se omite la pestana 3 "
        f"(FCST); Tabs 1/2 (ventas e inventario) siguen generandose normal, sin este archivo."
    )
    with open(out_dir / 'sept_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'disponible': False,
            'motivo': (
                'Archivo FCST SEPT 2026 VF Curvas.xlsx no encontrado en este equipo -- '
                'vive en el OneDrive de Alberto, todavia no es una fuente compartida.'
            ),
        }, f, ensure_ascii=False, indent=2)
    sys.exit(0)

rows = list(ws.iter_rows(values_only=True))
header = rows[2]  # fila 3 (0-indexed)

ly_idx = next(i for i, h in enumerate(header) if norm(h) == 'sept 2025')
bp_idx = next(
    i for i, h in enumerate(header)
    if norm(h).startswith('bp') and 'sept' in norm(h) and '2026' in norm(h)
)
fcst_vobo_idx = next(
    (i for i, h in enumerate(header) if 'fcst' in norm(h) and 'vobo' in norm(h)),
    None,
)

fcst_by_cat = {}
for row in rows[3:]:
    cat_id = row[1]
    if not isinstance(cat_id, (int, float)) or isinstance(cat_id, bool):
        continue
    cat_id = int(cat_id)
    if cat_id in cfg['cat_nbrs']:
        fcst_by_cat[cat_id] = {
            'ly_sept': row[ly_idx],
            'fcst_sept': row[bp_idx],
            'fcst_vobo': (row[fcst_vobo_idx] if fcst_vobo_idx is not None else None),
        }
wb.close()

missing = set(cfg['cat_nbrs']) - set(fcst_by_cat)
if missing:
    print(f"[{team_key}] AVISO: categorias sin match en hoja '{sheet_name}': {sorted(missing)}")

# ---------- 2. Crecimiento real YTD/MTD/L7D por categoria (igual que Abarrotes) ----------
full = pd.read_csv(out_dir / 'merged_full.csv', low_memory=False)
cat_agg = pd.read_csv(out_dir / 'cat_agg.csv').set_index('Cat_Nbr')
ytd_cat = full.groupby('Cat_Nbr')[['Com_Pesos_YTD', 'Com_Pesos_YTDLY']].sum()

categorias = []
for cat_nbr, vals in fcst_by_cat.items():
    fcst_val, ly_val, fcst_vobo = vals['fcst_sept'], vals['ly_sept'], vals['fcst_vobo']
    if not fcst_val or not ly_val:
        continue
    cat_desc = cat_agg.loc[cat_nbr, 'Cat_Desc'] if cat_nbr in cat_agg.index else f"Cat {cat_nbr}"
    crec_mtd = cat_agg.loc[cat_nbr, 'Crec_Com_MTD'] if cat_nbr in cat_agg.index else None
    crec_l7d = cat_agg.loc[cat_nbr, 'Crec_Com_L7D'] if cat_nbr in cat_agg.index else None
    if cat_nbr in ytd_cat.index:
        crec_ytd = (
            (ytd_cat.loc[cat_nbr, 'Com_Pesos_YTD'] - ytd_cat.loc[cat_nbr, 'Com_Pesos_YTDLY'])
            / ytd_cat.loc[cat_nbr, 'Com_Pesos_YTDLY']
        )
    else:
        crec_ytd = None
    com_mtd_actual = cat_agg.loc[cat_nbr, 'Com_Pesos_MTD'] if cat_nbr in cat_agg.index else None

    growth_needed = (fcst_val - ly_val) / ly_val
    trend_estimate = ly_val * (1 + crec_ytd) if crec_ytd is not None else None
    gap = (trend_estimate - fcst_val) if trend_estimate is not None else None
    gap_pct = (gap / fcst_val) if gap is not None else None
    if gap_pct is None:
        risk = 'Sin dato'
    elif crec_ytd < growth_needed - 0.05:
        risk = 'Alto'
    elif crec_ytd < growth_needed:
        risk = 'Moderado'
    else:
        risk = 'Bajo'

    categorias.append({
        'cat_nbr': cat_nbr, 'cat_desc': cat_desc,
        'fcst_sept': round(fcst_val, 2), 'ly_sept': round(ly_val, 2),
        'fcst_vobo': (round(fcst_vobo, 2) if fcst_vobo else None),
        'growth_needed': round(growth_needed, 4),
        'crec_mtd_actual': (round(float(crec_mtd), 4) if crec_mtd is not None else None),
        'crec_l7d_actual': (round(float(crec_l7d), 4) if crec_l7d is not None else None),
        'crec_ytd_actual': (round(float(crec_ytd), 4) if crec_ytd is not None else None),
        'com_mtd_actual': (round(float(com_mtd_actual), 2) if com_mtd_actual is not None else None),
        'trend_estimate': (round(trend_estimate, 2) if trend_estimate is not None else None),
        'gap': (round(gap, 2) if gap is not None else None),
        'gap_pct': (round(gap_pct, 4) if gap_pct is not None else None),
        'risk': risk,
    })
categorias.sort(key=lambda c: c['fcst_sept'], reverse=True)

fcst_total = sum(c['fcst_sept'] for c in categorias)
ly_total = sum(c['ly_sept'] for c in categorias)
fcst_vobo_total = sum(c['fcst_vobo'] for c in categorias if c['fcst_vobo'] is not None) or None
trend_total = sum(c['trend_estimate'] for c in categorias if c['trend_estimate'] is not None)

with open(out_dir / 'dashboard_data.json', 'r', encoding='utf-8') as f:
    tab1_kpis = json.load(f)['kpis']

tot_com_ytd = float(full['Com_Pesos_YTD'].sum())
tot_com_ytdly = float(full['Com_Pesos_YTDLY'].sum())
crec_ytd_actual_total = (tot_com_ytd - tot_com_ytdly) / tot_com_ytdly

kpis = {
    'fcst_total': round(fcst_total, 2), 'ly_total': round(ly_total, 2),
    'fcst_vobo_total': (round(fcst_vobo_total, 2) if fcst_vobo_total else None),
    'growth_needed_total': round((fcst_total - ly_total) / ly_total, 4),
    'crec_mtd_actual_total': tab1_kpis['com_mtd_growth'],
    'crec_l7d_actual_total': tab1_kpis['com_l7d_growth'],
    'crec_ytd_actual_total': round(crec_ytd_actual_total, 4),
    'trend_total': round(trend_total, 2),
    'gap_total': round(trend_total - fcst_total, 2),
    'gap_pct_total': round((trend_total - fcst_total) / fcst_total, 4),
}


def fmt_pct(x):
    sign = '+' if x >= 0 else ''
    return f"{sign}{x*100:.1f}%"


riesgo_alto = [c['cat_desc'] for c in categorias if c['risk'] == 'Alto']
concentracion_txt = (
    f"<strong>[Concentracion] El riesgo esta concentrado en {', '.join(riesgo_alto)}</strong> "
    "&mdash; vienen desacelerando en su tendencia YTD justo cuando el FCST les pide mas crecimiento, no menos."
) if riesgo_alto else (
    "<strong>[Concentracion] Ninguna categoria esta en riesgo Alto</strong> con la tendencia YTD actual "
    "&mdash; el riesgo, si lo hay, es moderado y disperso entre categorias."
)

insights_top = [
    f"<strong>[FCST] El objetivo de septiembre para {area} es {fmt_pct(kpis['growth_needed_total'])} YoY</strong> vs Sept 2025 "
    f"(${ly_total/1e6:.1f}M &rarr; ${fcst_total/1e6:.1f}M) &mdash; el YTD real de .com va en {fmt_pct(kpis['crec_ytd_actual_total'])} "
    f"(la base que usa el estimado de abajo), con un MTD de {fmt_pct(kpis['crec_mtd_actual_total'])} y una ultima semana de {fmt_pct(kpis['crec_l7d_actual_total'])}.",
    (
        f"<strong>[Riesgo] Si el ritmo YTD se mantiene</strong>, el estimado de septiembre sale en "
        f"${kpis['trend_total']/1e6:.1f}M &mdash; un faltante de ${abs(kpis['gap_total'])/1e6:.1f}M ({fmt_pct(kpis['gap_pct_total'])}) vs el target."
        if kpis['gap_total'] < 0 else
        f"<strong>[Positivo] Con el ritmo YTD acumulado</strong>, el estimado de tendencia (${kpis['trend_total']/1e6:.1f}M) ya supera el target."
    ),
    concentracion_txt,
]
if kpis['fcst_vobo_total']:
    diff_vobo = kpis['trend_total'] - kpis['fcst_vobo_total']
    insights_top.append(
        f"<strong>[Referencia] El forecast oficial del equipo central (FCST VoBo)</strong> para {area} es ${kpis['fcst_vobo_total']/1e6:.1f}M "
        f"&mdash; nuestro estimado basado en tendencia YTD (${kpis['trend_total']/1e6:.1f}M) queda "
        f"{'por encima' if diff_vobo >= 0 else 'por debajo'} por ${abs(diff_vobo)/1e6:.1f}M."
    )

data = {
    'disponible': True,
    'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
    'area': area,
    'kpis': kpis,
    'categorias': categorias,
    'insights_top': insights_top,
}

with open(out_dir / 'sept_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"[{team_key}] KPIs FCST:", json.dumps(kpis, indent=2, ensure_ascii=False))
print(f"[{team_key}] Categorias FCST:", len(categorias))

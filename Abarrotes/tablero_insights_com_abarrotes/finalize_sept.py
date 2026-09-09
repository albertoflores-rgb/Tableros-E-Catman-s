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
from datetime import date, timedelta

# merged_full.csv se lee UNA sola vez aqui arriba (item-level, ya trae
# YTD/MTD/L7D/AMX, SIEMPRE con TODOS los items incluyendo Status='D') --
# build() de mas abajo filtra a 'frame' segun el sufijo ('' = todos,
# '_sin_baja' = excluye Status='D') y se llama 2 veces para que el toggle
# 'excluir bajas' del dashboard alcance FCST/AMX/Fiestas Patrias, no solo
# Resumen (peticion de Alberto, 09-sep-2026: no descartar items, solo dar
# la OPCION de filtrarlos).
full = pd.read_csv('merged_full.csv')

# ---------- 1. Leer FCST Septiembre (target .com por categoria + comparable LY) ----------
# OJO: NO hardcodear la ruta completa -- la carpeta intermedia se ha
# movido antes sin avisar (de "OneDrive\W2\..." a "OneDrive\Seguros
# 2026\W2\..."). Se busca el archivo por NOMBRE con rglob desde la raiz
# del OneDrive para sobrevivir a que Alberto siga reorganizando carpetas
# -- esto corre TODOS LOS DIAS via Task Scheduler, no se puede dar el lujo
# de tronar por un folder renombrado.
import pathlib
onedrive_root = pathlib.Path(r"C:\Users\a0f07dn\OneDrive - Walmart Inc")
fcst_path = next(onedrive_root.rglob("FCST Septiembre 2026.xlsx"))

import openpyxl
wb = openpyxl.load_workbook(fcst_path, data_only=True)
ws = wb['Abarrotes']

# Columnas fila 33/79: 4=cat41, 6=cat46, 8=cat49, 10=cat53, 12=cat43, 14=cat68, 16=Total
COL_BY_CAT = {41: 4, 46: 6, 49: 8, 53: 10, 43: 12, 68: 14}
fcst_row = {c: ws.cell(row=33, column=col).value for c, col in COL_BY_CAT.items()}
fcst_total = ws.cell(row=33, column=16).value
ly_row = {c: ws.cell(row=79, column=col + 1).value for c, col in COL_BY_CAT.items()}
ly_total = sum(ly_row.values())

with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    tab1_data = json.load(f)


def fmt_pct(x):
    sign = '+' if x >= 0 else ''
    return f"{sign}{x*100:.1f}%"


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


AMX_INI = date(2026, 9, 9)
AMX_FIN = date(2026, 9, 16)
# BigQuery no tiene la venta de "hoy" todavia (1 dia de atraso normal) --
# ver misma logica/comentario en catman_equipos/pipeline/_common.py::
# compute_evento_amx. 'Dia comparable': se topa dias_transcurridos y el
# LY contra el que se compara al ultimo dia que YA deberia estar cargado
# en BQ, para no comparar un TY parcial contra un LY de 8 dias completos
# (peticion de Alberto, 09-sep-2026).
AMX_DATA_LAG_DIAS = 1
hoy = pd.Timestamp.now().date()
dia_con_datos = hoy - timedelta(days=AMX_DATA_LAG_DIAS)
dia_comparable = min(dia_con_datos, AMX_FIN)
amx_iniciado = dia_comparable >= AMX_INI
dias_totales = (AMX_FIN - AMX_INI).days + 1
dias_transcurridos = (dia_comparable - AMX_INI).days + 1 if amx_iniciado else 0
frac_comparable = (dias_transcurridos / dias_totales) if amx_iniciado else 0.0
terminado = dia_con_datos > AMX_FIN


def safe_growth(cur, prev):
    # Antes de que arranque el evento, Com_Pesos_AMX/Piso_Pesos_AMX son 0 de
    # verdad (todavia no hay ventas), pero *_AMXLY ya trae datos reales de
    # 2025 -- calcular el % ahi daria un falso "-100%" que asusta sin
    # decir nada util. Se regresa None ("n/d" en el front) hasta que el
    # evento arranque de verdad.
    if not amx_iniciado:
        return None
    if prev in (0, None) or pd.isna(prev):
        return None
    return (cur - prev) / prev


def build(suffix: str) -> dict:
    frame = full if suffix == '' else full[full['Status'] != 'D']

    # ---------- 2. Crecimiento real YTD/MTD/L7D por categoria ----------
    # El Gap de FCST usa YTD (no L7D) como base de tendencia -- decision de
    # Alberto (01-sep-2026): L7D es muy ruidoso semana a semana para proyectar
    # un mes completo, YTD da una base mas estable acumulada del anio.
    cat_agg = pd.read_csv(f'cat_agg{suffix}.csv').set_index('Cat_Nbr')
    ytd_cat = frame.groupby('Cat_Nbr')[['Com_Pesos_YTD', 'Com_Pesos_YTDLY']].sum()

    categorias = []
    for cat_nbr, fcst_val in fcst_row.items():
        cat_desc = cat_agg.loc[cat_nbr, 'Cat_Desc']
        ly_val = ly_row[cat_nbr]
        crec_mtd = cat_agg.loc[cat_nbr, 'Crec_Com_MTD']
        crec_l7d = cat_agg.loc[cat_nbr, 'Crec_Com_L7D']
        ytdly_val = ytd_cat.loc[cat_nbr, 'Com_Pesos_YTDLY']
        # Guardia explicita (no solo dividir directo): la vista 'sin_baja'
        # puede dejar una categoria con YTDLY en $0 si todo su historico
        # vivia en items hoy de baja -- sin esto, 0/0 da NaN y contamina
        # trend_total/gap_total silenciosamente.
        if ytdly_val in (0, None) or pd.isna(ytdly_val):
            crec_ytd = None
        else:
            crec_ytd = (ytd_cat.loc[cat_nbr, 'Com_Pesos_YTD'] - ytdly_val) / ytdly_val
        com_mtd_actual = cat_agg.loc[cat_nbr, 'Com_Pesos_MTD']
        growth_needed = (fcst_val - ly_val) / ly_val
        trend_estimate = ly_val * (1 + crec_ytd) if crec_ytd is not None else None
        gap = (trend_estimate - fcst_val) if trend_estimate is not None else None
        gap_pct = (gap / fcst_val) if gap is not None else None
        if crec_ytd is None:
            risk = 'Sin dato'
        elif crec_ytd < growth_needed - 0.05:
            risk = 'Alto'
        elif crec_ytd < growth_needed:
            risk = 'Moderado'
        else:
            risk = 'Bajo'
        categorias.append({
            'cat_nbr': int(cat_nbr), 'cat_desc': cat_desc,
            'fcst_sept': round(fcst_val, 2), 'ly_sept': round(ly_val, 2),
            'growth_needed': round(growth_needed, 4),
            'crec_mtd_actual': round(float(crec_mtd), 4), 'crec_l7d_actual': round(float(crec_l7d), 4),
            'crec_ytd_actual': (round(float(crec_ytd), 4) if crec_ytd is not None else None),
            'com_mtd_actual': round(float(com_mtd_actual), 2),
            'trend_estimate': (round(trend_estimate, 2) if trend_estimate is not None else None),
            'gap': (round(gap, 2) if gap is not None else None),
            'gap_pct': (round(gap_pct, 4) if gap_pct is not None else None),
            'risk': risk,
        })
    categorias.sort(key=lambda c: c['fcst_sept'], reverse=True)

    trend_total = sum(c['trend_estimate'] for c in categorias if c['trend_estimate'] is not None)

    # Crecimiento MTD/L7D total real de .com Abarrotes -- se lee de
    # dashboard_data.json (pestana 1, misma vista todos/sin_baja), NUNCA
    # se hardcodea aqui para que no se desactualice con el resto del
    # tablero. YTD si se calcula aqui mismo sumando directo el item-level.
    tab1_kpis = tab1_data['todos' if suffix == '' else 'sin_baja']['kpis']

    tot_com_ytd, tot_com_ytdly = float(frame['Com_Pesos_YTD'].sum()), float(frame['Com_Pesos_YTDLY'].sum())
    crec_ytd_actual_total = (tot_com_ytd - tot_com_ytdly) / tot_com_ytdly

    kpis = {
        'fcst_total': round(fcst_total, 2), 'ly_total': round(ly_total, 2),
        'growth_needed_total': round((fcst_total - ly_total) / ly_total, 4),
        'crec_mtd_actual_total': tab1_kpis['com_mtd_growth'],
        'crec_l7d_actual_total': tab1_kpis['com_l7d_growth'],
        'crec_ytd_actual_total': round(crec_ytd_actual_total, 4),
        'trend_total': round(trend_total, 2),
        'gap_total': round(trend_total - fcst_total, 2),
        'gap_pct_total': round((trend_total - fcst_total) / fcst_total, 4),
    }

    # ---------- 3. Item-level: subcategorias de Fiestas Patrias / boost de busqueda ----------
    sub = frame[frame['Sub_Cat_Desc'].isin(TARGET_SUBCATS.keys())].copy()
    sub['Boost_Motivo'] = sub['Sub_Cat_Desc'].map(lambda s: TARGET_SUBCATS[s][0])
    sub['Fiestas_Patrias'] = sub['Sub_Cat_Desc'].map(lambda s: TARGET_SUBCATS[s][1])
    sub['Share_Com_MTD_calc'] = sub['Com_Pesos_MTD'] / (sub['Com_Pesos_MTD'] + sub['Piso_Pesos_MTD'])

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

    # ---------- 4. Evento "A la Mexicana" (9-16 sep 2026) ----------
    amx_cat = frame.groupby(['Cat_Nbr', 'Cat_Desc']).agg(
        Com_Pesos_AMX=('Com_Pesos_AMX', 'sum'), Com_Pesos_AMXLY=('Com_Pesos_AMXLY', 'sum'),
        Piso_Pesos_AMX=('Piso_Pesos_AMX', 'sum'), Piso_Pesos_AMXLY=('Piso_Pesos_AMXLY', 'sum'),
    ).reset_index()

    amx_categorias = []
    for _, r in amx_cat.iterrows():
        com_amx, com_amxly = float(r['Com_Pesos_AMX']), float(r['Com_Pesos_AMXLY'])
        piso_amx, piso_amxly = float(r['Piso_Pesos_AMX']), float(r['Piso_Pesos_AMXLY'])
        com_amxly_comp, piso_amxly_comp = com_amxly * frac_comparable, piso_amxly * frac_comparable
        total_amx = com_amx + piso_amx
        crec_com = safe_growth(com_amx, com_amxly_comp)
        crec_piso = safe_growth(piso_amx, piso_amxly_comp)
        amx_categorias.append({
            'cat_nbr': int(r['Cat_Nbr']), 'cat_desc': r['Cat_Desc'],
            'com_amx': round(com_amx, 2), 'com_amxly': round(com_amxly, 2),
            'com_amxly_comparable': round(com_amxly_comp, 2),
            'crec_com_amx': (round(crec_com, 4) if crec_com is not None else None),
            'piso_amx': round(piso_amx, 2), 'piso_amxly': round(piso_amxly, 2),
            'piso_amxly_comparable': round(piso_amxly_comp, 2),
            'crec_piso_amx': (round(crec_piso, 4) if crec_piso is not None else None),
            'share_com_amx': (round(com_amx / total_amx, 4) if total_amx > 0 else None),
        })
    amx_categorias.sort(key=lambda c: c['com_amx'], reverse=True)

    tot_com_amx, tot_com_amxly = float(frame['Com_Pesos_AMX'].sum()), float(frame['Com_Pesos_AMXLY'].sum())
    tot_piso_amx, tot_piso_amxly = float(frame['Piso_Pesos_AMX'].sum()), float(frame['Piso_Pesos_AMXLY'].sum())
    tot_com_amxly_comp, tot_piso_amxly_comp = tot_com_amxly * frac_comparable, tot_piso_amxly * frac_comparable
    crec_com_amx_total = safe_growth(tot_com_amx, tot_com_amxly_comp)
    crec_piso_amx_total = safe_growth(tot_piso_amx, tot_piso_amxly_comp)

    iniciado = amx_iniciado
    if not iniciado:
        amx_status_msg = f"El evento arranca el {AMX_INI.strftime('%d-%b-%Y')} -- estos valores se activan solos ese dia con la corrida diaria de siempre, no hace falta tocar nada."
    elif not terminado:
        amx_status_msg = (
            f"Evento en curso: dia {dias_transcurridos} de {dias_totales} "
            f"({AMX_INI.strftime('%d-%b')} -> {AMX_FIN.strftime('%d-%b')}). "
            f"Crecimiento vs LY de los mismos {dias_transcurridos} dias transcurridos (dia comparable), "
            f"no vs los {dias_totales} dias completos de LY -- BigQuery tiene 1 dia de atraso normal en la venta de hoy."
        )
    else:
        amx_status_msg = f"Evento cerrado ({AMX_INI.strftime('%d-%b')} -> {AMX_FIN.strftime('%d-%b')}) -- resultado final vs LY completo (mismos {dias_totales} dias)."

    evento_amx = {
        'fecha_ini': AMX_INI.isoformat(), 'fecha_fin': AMX_FIN.isoformat(),
        'iniciado': iniciado, 'terminado': terminado,
        'dias_transcurridos': dias_transcurridos, 'dias_totales': dias_totales,
        'status_msg': amx_status_msg,
        'kpis': {
            'com_amx': round(tot_com_amx, 2), 'com_amxly': round(tot_com_amxly, 2),
            'com_amxly_comparable': round(tot_com_amxly_comp, 2),
            'crec_com_amx': (round(crec_com_amx_total, 4) if crec_com_amx_total is not None else None),
            'piso_amx': round(tot_piso_amx, 2), 'piso_amxly': round(tot_piso_amxly, 2),
            'piso_amxly_comparable': round(tot_piso_amxly_comp, 2),
            'crec_piso_amx': (round(crec_piso_amx_total, 4) if crec_piso_amx_total is not None else None),
        },
        'categorias': amx_categorias,
    }

    # ---------- 5. Insights ejecutivos ----------
    riesgo_alto = [c['cat_desc'] for c in categorias if c['risk'] == 'Alto']
    concentracion_txt = (
        f"<strong>[Concentracion] El riesgo esta concentrado en {', '.join(riesgo_alto)}</strong> "
        "&mdash; vienen desacelerando en su tendencia YTD justo cuando el FCST les pide mas crecimiento, no menos."
    ) if riesgo_alto else (
        "<strong>[Concentracion] Ninguna categoria esta en riesgo Alto</strong> con la tendencia YTD actual "
        "&mdash; el riesgo, si lo hay, es moderado y disperso entre categorias."
    )

    insights_top = [
        f"<strong>[FCST] El objetivo de septiembre es {fmt_pct(kpis['growth_needed_total'])} YoY</strong> vs Sept 2025 "
        f"(${ly_total/1e6:.1f}M &rarr; ${fcst_total/1e6:.1f}M) &mdash; el YTD real de .com Abarrotes va en {fmt_pct(kpis['crec_ytd_actual_total'])} "
        f"(la base que usa el estimado de abajo), con un MTD de agosto de {fmt_pct(kpis['crec_mtd_actual_total'])} y una ultima semana de {fmt_pct(kpis['crec_l7d_actual_total'])}.",
        (
            f"<strong>[Riesgo] Si el ritmo YTD se mantiene</strong> (base mas estable que una sola semana suelta), el estimado de septiembre sale en "
            f"${kpis['trend_total']/1e6:.1f}M &mdash; un faltante de ${abs(kpis['gap_total'])/1e6:.1f}M ({fmt_pct(kpis['gap_pct_total'])}) vs el target."
            if kpis['gap_total'] < 0 else
            f"<strong>[Positivo] Con el ritmo YTD acumulado</strong>, el estimado de tendencia (${kpis['trend_total']/1e6:.1f}M) ya supera el target."
        ),
        concentracion_txt,
        f"<strong>[Accionables] {len(items['apagar_incendios'])} items</strong> con alto volumen en Piso estan cayendo fuerte en .com "
        f"(candidatos a 'apagar incendio' antes de septiembre), <strong>{len(items['doblar_apuesta'])} items</strong> ya tienen momentum "
        f"sostenido para escalar, y <strong>{len(items['blanco_total'])} items</strong> tienen demanda fisica real pero cero promo vigente.",
    ]

    return {
        'kpis': kpis,
        'categorias': categorias,
        'items': items,
        'evento_amx': evento_amx,
        'insights_top': insights_top,
    }


# ---------- Contexto del reporte de boosteos de busqueda (terminos Fiestas
# Patrias) -- NO depende del universo de items (viene de un reporte HTML
# aparte), asi que se calcula UNA sola vez, fuera de build(). ----------
boost_html = open('../reporte_internal_search_boosteos.html', encoding='utf-8').read()
m = re.search(r'const DATA = (\{.*?\});', boost_html, re.DOTALL)
boost_data = json.loads(m.group(1))
sept_kw_ctx = {
    'fiestas_26_top': boost_data['sept_kw'].get('fiestas_26_top', []),
    'fiestas_26_count': boost_data['sept_kw'].get('fiestas_26_count'),
    'climbers': boost_data['sept_kw'].get('climbers', []),
}

data = {
    'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
    'sept_kw_context': sept_kw_ctx,
    'todos': build(''),
    'sin_baja': build('_sin_baja'),
}

with open('sept_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('KPIs (todos):', json.dumps(data['todos']['kpis'], indent=2, ensure_ascii=False))
print('Categorias:', len(data['todos']['categorias']))
print('Items (todos):', {k: len(v) for k, v in data['todos']['items'].items()})
print('Evento AMX (todos):', json.dumps(data['todos']['evento_amx']['kpis'], indent=2, ensure_ascii=False), '|', data['todos']['evento_amx']['status_msg'])
print('Guardado sept_data.json')

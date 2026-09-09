# -*- coding: utf-8 -*-
"""Pipeline generico y parametrizado por equipo (team_key) para generar
el tablero de Insights .com de cualquiera de los 6 equipos de E-Catman.

Por que existe esto (en vez de copiar tablero_insights_com_perecederos/
5 veces mas): la logica de merge/KPIs/movers es IDENTICA para todos los
equipos -- lo unico que cambia es el nombre del area, el owner, cuantas
categorias tiene, y sus datos. Un solo pipeline parametrizado evita
mantener 6 copias casi-identicas de ~600 lineas cada una.

Uso (desde catman_equipos/pipeline/):
    python run_team_pipeline.py <team_key>

Esto asume que ya corriste (una sola vez para todos los equipos):
    python ../run_query_combined.py
    python ../split_by_team.py
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PIPELINE_DIR = Path(__file__).parent
CATMAN_DIR = PIPELINE_DIR.parent
WORKSPACE_DIR = CATMAN_DIR.parent
sys.path.insert(0, str(CATMAN_DIR))

from teams_config import TEAMS, EXTRA_TEAMS  # noqa: E402

# Evento "A la Mexicana" -- MISMAS fechas que usa
# tablero_insights_com_abarrotes/finalize_sept.py (no se importa de ahi
# directo porque ese pipeline es standalone a proposito, ver su
# docstring/CHANGELOG -- se mantiene esta unica copia aqui para los 6
# equipos genericos en vez de repetirla en cada uno).
AMX_INI = date(2026, 9, 9)
AMX_FIN = date(2026, 9, 16)


def team_dir(team_key: str) -> Path:
    d = WORKSPACE_DIR / f"tablero_insights_com_{team_key}"
    d.mkdir(exist_ok=True)
    return d


def get_team_cfg(team_key: str) -> dict:
    # EXTRA_TEAMS (ej. 'total_departamentos') reusa el mismo pipeline
    # generico que los 6 equipos reales -- ver teams_config.py. No se
    # incluyen en TEAMS a proposito para que 'run_team_pipeline.py --all'
    # (y el main.py de W5) sigan procesando SOLO los 6 equipos reales.
    if team_key in TEAMS:
        return TEAMS[team_key]
    if team_key in EXTRA_TEAMS:
        return EXTRA_TEAMS[team_key]
    raise SystemExit(
        f"Team desconocido: {team_key}. Opciones: {list(TEAMS) + list(EXTRA_TEAMS)}"
    )


def _safe_amx_growth(cur: float, prev: float, amx_iniciado: bool):
    """Antes de que arranque el evento, *_AMX es 0 de verdad (todavia no
    hay ventas) pero *_AMXLY ya trae datos reales de 2025 -- calcular el
    % ahi daria un falso '-100%' que asusta sin decir nada util. Se
    regresa None ('n/d' en el front) hasta que el evento arranque."""
    if not amx_iniciado:
        return None
    if prev in (0, None) or pd.isna(prev):
        return None
    return (cur - prev) / prev


def compute_evento_amx(full: pd.DataFrame) -> dict:
    """Bloque del evento 'A la Mexicana' (9-16 sep 2026), MISMA logica
    que tablero_insights_com_abarrotes/finalize_sept.py seccion 4 --
    replicada aqui (una sola vez, no una por equipo) para que los 6
    equipos genericos tengan el mismo bloque en su pestana de FCST
    Septiembre. Requiere que 'full' (merged_full.csv) traiga las
    columnas Com_Pesos_AMX/AMXLY y Piso_Pesos_AMX/AMXLY -- ya vienen de
    query_item_total_template.sql para los 6 equipos, sin cambios.
    """
    hoy = pd.Timestamp.now().date()
    amx_iniciado = hoy >= AMX_INI

    amx_cat = full.groupby(['Cat_Nbr', 'Cat_Desc']).agg(
        Com_Pesos_AMX=('Com_Pesos_AMX', 'sum'), Com_Pesos_AMXLY=('Com_Pesos_AMXLY', 'sum'),
        Piso_Pesos_AMX=('Piso_Pesos_AMX', 'sum'), Piso_Pesos_AMXLY=('Piso_Pesos_AMXLY', 'sum'),
    ).reset_index()

    amx_categorias = []
    for _, r in amx_cat.iterrows():
        com_amx, com_amxly = float(r['Com_Pesos_AMX']), float(r['Com_Pesos_AMXLY'])
        piso_amx, piso_amxly = float(r['Piso_Pesos_AMX']), float(r['Piso_Pesos_AMXLY'])
        total_amx = com_amx + piso_amx
        crec_com = _safe_amx_growth(com_amx, com_amxly, amx_iniciado)
        crec_piso = _safe_amx_growth(piso_amx, piso_amxly, amx_iniciado)
        amx_categorias.append({
            'cat_nbr': int(r['Cat_Nbr']), 'cat_desc': r['Cat_Desc'],
            'com_amx': round(com_amx, 2), 'com_amxly': round(com_amxly, 2),
            'crec_com_amx': (round(crec_com, 4) if crec_com is not None else None),
            'piso_amx': round(piso_amx, 2), 'piso_amxly': round(piso_amxly, 2),
            'crec_piso_amx': (round(crec_piso, 4) if crec_piso is not None else None),
            'share_com_amx': (round(com_amx / total_amx, 4) if total_amx > 0 else None),
        })
    amx_categorias.sort(key=lambda c: c['com_amx'], reverse=True)

    tot_com_amx, tot_com_amxly = float(full['Com_Pesos_AMX'].sum()), float(full['Com_Pesos_AMXLY'].sum())
    tot_piso_amx, tot_piso_amxly = float(full['Piso_Pesos_AMX'].sum()), float(full['Piso_Pesos_AMXLY'].sum())
    crec_com_amx_total = _safe_amx_growth(tot_com_amx, tot_com_amxly, amx_iniciado)
    crec_piso_amx_total = _safe_amx_growth(tot_piso_amx, tot_piso_amxly, amx_iniciado)

    dias_totales = (AMX_FIN - AMX_INI).days + 1
    terminado = hoy > AMX_FIN
    if not amx_iniciado:
        dias_transcurridos = 0
        amx_status_msg = f"El evento arranca el {AMX_INI.strftime('%d-%b-%Y')} -- estos valores se activan solos ese dia con la corrida diaria de siempre, no hace falta tocar nada."
    elif not terminado:
        dias_transcurridos = (hoy - AMX_INI).days + 1
        amx_status_msg = f"Evento en curso: dia {dias_transcurridos} de {dias_totales} ({AMX_INI.strftime('%d-%b')} -> {AMX_FIN.strftime('%d-%b')})."
    else:
        dias_transcurridos = dias_totales
        amx_status_msg = f"Evento cerrado ({AMX_INI.strftime('%d-%b')} -> {AMX_FIN.strftime('%d-%b')}) -- resultado final vs LY."

    return {
        'fecha_ini': AMX_INI.isoformat(), 'fecha_fin': AMX_FIN.isoformat(),
        'iniciado': amx_iniciado, 'terminado': terminado,
        'dias_transcurridos': dias_transcurridos, 'dias_totales': dias_totales,
        'status_msg': amx_status_msg,
        'kpis': {
            'com_amx': round(tot_com_amx, 2), 'com_amxly': round(tot_com_amxly, 2),
            'crec_com_amx': (round(crec_com_amx_total, 4) if crec_com_amx_total is not None else None),
            'piso_amx': round(tot_piso_amx, 2), 'piso_amxly': round(tot_piso_amxly, 2),
            'crec_piso_amx': (round(crec_piso_amx_total, 4) if crec_piso_amx_total is not None else None),
        },
        'categorias': amx_categorias,
    }

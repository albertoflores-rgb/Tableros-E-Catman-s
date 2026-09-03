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
from pathlib import Path

PIPELINE_DIR = Path(__file__).parent
CATMAN_DIR = PIPELINE_DIR.parent
WORKSPACE_DIR = CATMAN_DIR.parent
sys.path.insert(0, str(CATMAN_DIR))

from teams_config import TEAMS, EXTRA_TEAMS  # noqa: E402


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

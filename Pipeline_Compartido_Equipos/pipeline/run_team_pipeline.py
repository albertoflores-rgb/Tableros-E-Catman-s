# -*- coding: utf-8 -*-
"""Orquestador: corre el pipeline completo (merge -> finalize_data ->
finalize_explorer -> build_dashboard) para UN equipo.

Requisito previo (una sola vez para todos los equipos):
    cd .. && python run_query_combined.py && python split_by_team.py

Uso:
    python run_team_pipeline.py <team_key>
    python run_team_pipeline.py --all      # corre los 6 equipos
"""
import subprocess
import sys
from pathlib import Path

from _common import get_team_cfg
from teams_config import TEAMS

PIPELINE_DIR = Path(__file__).parent
PYTHON = sys.executable

STEPS = ['build_merge.py', 'finalize_data.py', 'finalize_sept.py', 'finalize_explorer.py', 'build_dashboard.py']
DSV_STEP = 'merge_dsv.py'
TEAMS_WITH_DSV = {'tecnologia', 'seasonal', 'apparel'}


def steps_for(team_key: str):
    steps = list(STEPS)
    if team_key in TEAMS_WITH_DSV:
        # DSV debe correr DESPUES de build_merge.py (crea merged_full.csv) y
        # ANTES de finalize_data.py/finalize_explorer.py (lo leen).
        steps.insert(steps.index('finalize_data.py'), DSV_STEP)
    return steps


def run_team(team_key: str) -> None:
    get_team_cfg(team_key)  # valida que exista, truena temprano si no
    print(f"\n{'='*60}\n{team_key.upper()}\n{'='*60}")
    for step in steps_for(team_key):
        result = subprocess.run(
            [PYTHON, str(PIPELINE_DIR / step), team_key],
            cwd=str(PIPELINE_DIR),
        )
        if result.returncode != 0:
            raise SystemExit(f"[{team_key}] Fallo en {step} (exit {result.returncode})")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    arg = sys.argv[1]
    if arg == '--all':
        for tk in TEAMS:
            run_team(tk)
    else:
        run_team(arg)

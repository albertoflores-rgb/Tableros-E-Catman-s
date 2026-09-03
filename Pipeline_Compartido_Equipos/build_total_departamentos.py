# -*- coding: utf-8 -*-
"""Orquestador dedicado para el 7mo tablero: 'Total Departamentos'
(vista consolidada de los 6 equipos de E-Catman + Abarrotes + las 5
categorias 'huerfanas' -- ver teams_config.py).

Por que un wrapper y no un pipeline nuevo desde cero: el pipeline
generico de catman_equipos/pipeline/ (build_merge -> finalize_data ->
finalize_explorer -> build_dashboard, con finalize_sept saltandose la
pestana 3 via el flag 'no_fcst') ya sirve tal cual para este 7mo
tablero -- 'total_departamentos' vive en teams_config.EXTRA_TEAMS y
pipeline/_common.py::get_team_cfg() ya lo resuelve igual que a un
equipo real. Este script solo:
  1. Verifica que exista el CSV crudo de este 'equipo' (lo genera
     split_by_team.py a partir del CSV combinado -- requiere haber
     corrido antes run_query_combined.py + split_by_team.py).
  2. Corre pipeline/run_team_pipeline.py total_departamentos (mismos
     pasos que cualquier equipo real, SIN merge_dsv.py -- DSV queda
     fuera de alcance v1 para esta vista consolidada).

Uso:
    python run_query_combined.py      # 1 sola pasada de BQ, universo completo (76 cats)
    python split_by_team.py           # separa CSVs (6 equipos + total_departamentos), sin costo BQ
    python build_total_departamentos.py
"""
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PIPELINE_DIR = SCRIPT_DIR / "pipeline"
RAW_CSV = SCRIPT_DIR / "raw_bq_item_total_total_departamentos.csv"


def run() -> None:
    if not RAW_CSV.exists():
        raise SystemExit(
            f"No existe {RAW_CSV}. Corre primero:\n"
            f"  python run_query_combined.py\n"
            f"  python split_by_team.py"
        )

    print("=" * 60)
    print("TOTAL DEPARTAMENTOS (vista consolidada)")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, str(PIPELINE_DIR / "run_team_pipeline.py"), "total_departamentos"],
        cwd=str(PIPELINE_DIR),
    )
    if result.returncode != 0:
        raise SystemExit(f"Fallo el pipeline de total_departamentos (exit {result.returncode})")

    html_path = SCRIPT_DIR.parent / "tablero_insights_com_total_departamentos" / "tablero_insights_com_total_departamentos.html"
    print(f"[OK] Tablero generado: {html_path}")


if __name__ == "__main__":
    run()

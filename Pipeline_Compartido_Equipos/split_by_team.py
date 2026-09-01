# -*- coding: utf-8 -*-
"""Separa raw_bq_item_total_catman_combined.csv (ya jalado UNA vez de
BigQuery por run_query_combined.py) en un CSV por equipo, filtrando
localmente por Cat_Nbr con pandas -- CERO costo de BigQuery adicional.

Uso:
    python split_by_team.py
"""
from pathlib import Path

import pandas as pd

from teams_config import TEAMS

SCRIPT_DIR = Path(__file__).parent
COMBINED_CSV = SCRIPT_DIR / "raw_bq_item_total_catman_combined.csv"


def run() -> None:
    if not COMBINED_CSV.exists():
        raise SystemExit(
            f"No existe {COMBINED_CSV}. Corre primero: python run_query_combined.py"
        )

    df = pd.read_csv(COMBINED_CSV, low_memory=False)
    print(f"CSV combinado: {len(df)} filas, {df['Cat_Nbr'].nunique()} categorias distintas.")

    for team_key, cfg in TEAMS.items():
        sub = df[df["Cat_Nbr"].isin(cfg["cat_nbrs"])]
        out_path = SCRIPT_DIR / f"raw_bq_item_total_{team_key}.csv"
        sub.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"  {team_key:18s} ({cfg['owner']:10s}): {len(sub):6d} filas -> {out_path.name}")


if __name__ == "__main__":
    run()

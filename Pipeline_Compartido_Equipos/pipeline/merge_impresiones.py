# -*- coding: utf-8 -*-
"""merge_impresiones.py -- agrega el campo "Impresiones_Adobe" (proxy
de impresiones en sitio: searchResults + browseResults, eVar168) a la
vista de Total Departamentos. NO corre para los 6 equipos individuales
-- esta data es un snapshot de UN dia (no una serie automatizada) y
vive fuera del pipeline diario de venta/inventario a proposito, ver
`tablero_adobe_impresiones_item/README.md`.

Por que solo Total Departamentos: es donde se revivio este hallazgo
(el extinto "Total Departamentos V1" ad-hoc que costaba ~3.8TB por
incluir Impresiones Adobe directo en el query combinado). Aqui se une
LOCALMENTE (pandas merge por Item_Nbr), sin volver a tocar BigQuery
con el query pesado -- el costo de Impresiones ya se pago aparte y por
separado en `tablero_adobe_impresiones_item/run_query.py` (~15 GB por
UN dia, ver ese README). Los 6 tableros de equipo siguen sin esto,
igual que siempre.

Uso: python merge_impresiones.py total_departamentos
"""
import sys
import pandas as pd

from _common import team_dir, get_team_cfg, WORKSPACE_DIR

TEAMS_WITH_IMPRESIONES = {'total_departamentos'}

team_key = sys.argv[1]
get_team_cfg(team_key)
if team_key not in TEAMS_WITH_IMPRESIONES:
    raise SystemExit(
        f"[{team_key}] Impresiones Adobe no aplica a este equipo (solo: "
        f"{sorted(TEAMS_WITH_IMPRESIONES)}). No se corre este script para {team_key}."
    )

out_dir = team_dir(team_key)
impresiones_path = WORKSPACE_DIR / 'tablero_adobe_impresiones_item' / 'raw_adobe_impresiones_item.csv'

if not impresiones_path.exists():
    print(
        f"[{team_key}] AVISO: no se encontro {impresiones_path} -- se omite Impresiones_Adobe, "
        f"el resto del tablero se genera normal. Corre tablero_adobe_impresiones_item/run_query.py primero."
    )
    sys.exit(0)

imp = pd.read_csv(impresiones_path, dtype={'Item_Nbr': str})
fecha_impresiones = imp['Fecha'].iloc[0] if len(imp) else None
imp['Item_Nbr'] = pd.to_numeric(imp['Item_Nbr'], errors='coerce')
imp = imp.dropna(subset=['Item_Nbr'])
imp['Item_Nbr'] = imp['Item_Nbr'].astype('int64')
imp_agg = imp.groupby('Item_Nbr', as_index=False).agg(Impresiones_Adobe=('Ocurrencias', 'sum'))

full = pd.read_csv(out_dir / 'merged_full.csv', low_memory=False)
n_before = len(full)

full = full.merge(imp_agg, on='Item_Nbr', how='left')
assert len(full) == n_before, "El merge de Impresiones no debe duplicar filas -- revisar Item_Nbr duplicados"

n_match = full['Impresiones_Adobe'].notna().sum()
print(f"[{team_key}] Fecha de impresiones: {fecha_impresiones}")
print(f"[{team_key}] Items con impresiones: {n_match} de {n_before} ({n_match/n_before*100:.1f}%)")
print(f"[{team_key}] Impresiones totales: {full['Impresiones_Adobe'].sum():,.0f}")

full.to_csv(out_dir / 'merged_full.csv', index=False, encoding='utf-8-sig')
print(f"[{team_key}] merged_full.csv actualizado con Impresiones_Adobe")

# -*- coding: utf-8 -*-
"""merge_dsv.py -- agrega el campo "Inventario DSV" a los equipos de
Mercancias Generales (Tecnologia, Seasonal, Apparel). NO corre para el
resto de equipos -- DSV es exclusivo de Mercancias Generales (confirmado
por Alberto, 01-sep-2026).

Llave de cruce: `Item_Nbr` (nuestro campo = Old_NBR/SKU en el schema de
origen) contra el campo "UPC" del export de DSV -- que Alberto confirmo
es en realidad ese MISMO numero de item, no un codigo de barras real.
(Ojo: hubo un primer intento fallido usando `Item_Nbr_Raw` -- el ITEM_NBR
interno crudo de Walmart -- que dio 0 matches porque ese es un numero de
sistema completamente distinto al SKU/Old_NBR que usa DSV. `Item_Nbr` es
el correcto: valida con match real de 554/1032/1351 items respectivamente.)

Uso: python merge_dsv.py <team_key>
"""
import sys
import pandas as pd

from _common import team_dir, get_team_cfg, WORKSPACE_DIR

TEAMS_WITH_DSV = {'tecnologia', 'seasonal', 'apparel'}

team_key = sys.argv[1]
get_team_cfg(team_key)
if team_key not in TEAMS_WITH_DSV:
    raise SystemExit(
        f"[{team_key}] DSV no aplica a este equipo (solo Mercancias Generales: "
        f"{sorted(TEAMS_WITH_DSV)}). No se corre este script para {team_key}."
    )

out_dir = team_dir(team_key)
dsv_path = WORKSPACE_DIR / 'dsv_inventario' / 'inventario_dsv_raw.csv'

dsv = pd.read_csv(dsv_path, encoding='utf-8-sig')
dsv['Item_Nbr'] = (
    dsv['UPC'].astype(str).str.replace("'", '', regex=False).str.strip()
)
dsv['Item_Nbr'] = pd.to_numeric(dsv['Item_Nbr'], errors='coerce')
dsv = dsv.dropna(subset=['Item_Nbr'])
dsv['Item_Nbr'] = dsv['Item_Nbr'].astype('int64')

# Un mismo Item_Nbr puede aparecer 2+ veces en el export DSV (guias/
# proveedores distintos para el mismo item) -- se suma el inventario y
# se conserva el primer proveedor/costo como referencia.
dsv_agg = dsv.groupby('Item_Nbr', as_index=False).agg(
    Inventario_DSV=('Inventario', 'sum'),
    DSV_Proveedor=('Empresa', 'first'),
    DSV_Costo=('Costo', 'first'),
)

full = pd.read_csv(out_dir / 'merged_full.csv', low_memory=False)
n_before = len(full)

full = full.merge(dsv_agg, on='Item_Nbr', how='left')
assert len(full) == n_before, "El merge de DSV no debe duplicar filas -- revisar Item_Nbr duplicados"

n_match = full['Inventario_DSV'].notna().sum()
print(f"[{team_key}] Items con inventario DSV: {n_match} de {n_before} ({n_match/n_before*100:.1f}%)")
print(f"[{team_key}] Inventario DSV total: {full['Inventario_DSV'].sum():,.0f} unidades")

full.to_csv(out_dir / 'merged_full.csv', index=False, encoding='utf-8-sig')
print(f"[{team_key}] merged_full.csv actualizado con Inventario_DSV/DSV_Proveedor/DSV_Costo")

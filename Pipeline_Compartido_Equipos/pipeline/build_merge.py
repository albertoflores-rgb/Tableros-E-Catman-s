# -*- coding: utf-8 -*-
"""build_merge.py generico -- ver Perecederos para el original que
inspiro esto. Uso: python build_merge.py <team_key>
"""
import sys
import pandas as pd
import numpy as np

from _common import team_dir, get_team_cfg, CATMAN_DIR

team_key = sys.argv[1]
cfg = get_team_cfg(team_key)
out_dir = team_dir(team_key)

raw_csv = CATMAN_DIR / f"raw_bq_item_total_{team_key}.csv"
bq = pd.read_csv(raw_csv, low_memory=False)
bq['Item_Nbr'] = bq['Item_Nbr'].astype('int64')

df = bq.copy()
print(f"[{team_key}] Items totales:", len(df))

df['Inv_Pzas_Total'] = df['OHQty_Clubes'] + df['OHQty_FC_MX'] + df['OHQty_FC_MTY']
df['Inv_MXN_Total'] = df['OHQty_Clubes_MXN'] + df['OHMXN_FC_MX'] + df['OHMXN_FC_MTY']

for periodo in ('YTD', 'MTD', 'L7D'):
    com_col, piso_col = f'Com_Pesos_{periodo}', f'Piso_Pesos_{periodo}'
    total = df[com_col] + df[piso_col]
    df[f'Share_Com_{periodo}'] = np.where(total > 0, df[com_col] / total, np.nan)

df['Top_L7D_Cat'] = (
    df.groupby('Cat_Nbr')['Com_Pesos_L7D']
    .rank(method='first', ascending=False)
    .astype(int)
)


def safe_growth(cur, prev):
    prev = prev.replace(0, np.nan)
    return (cur - prev) / prev


cat_agg = df.groupby(['Cat_Nbr', 'Cat_Desc']).agg(
    Com_Pesos_MTD=('Com_Pesos_MTD', 'sum'),
    Com_Pesos_MTDLY=('Com_Pesos_MTDLY', 'sum'),
    Piso_Pesos_MTD=('Piso_Pesos_MTD', 'sum'),
    Piso_Pesos_MTDLY=('Piso_Pesos_MTDLY', 'sum'),
    Com_Pesos_L7D=('Com_Pesos_L7D', 'sum'),
    Com_Pesos_L7DLY=('Com_Pesos_L7DLY', 'sum'),
    Piso_Pesos_L7D=('Piso_Pesos_L7D', 'sum'),
    Piso_Pesos_L7DLY=('Piso_Pesos_L7DLY', 'sum'),
    Ordenes_Com_MTD=('Ordenes_Com_MTD', 'sum'),
    Numero_Socios_MTD=('Numero_Socios_MTD', 'sum'),
    N_Items=('Item_Nbr', 'nunique'),
).reset_index()

cat_agg['Crec_Com_MTD'] = safe_growth(cat_agg['Com_Pesos_MTD'], cat_agg['Com_Pesos_MTDLY'])
cat_agg['Crec_Piso_MTD'] = safe_growth(cat_agg['Piso_Pesos_MTD'], cat_agg['Piso_Pesos_MTDLY'])
cat_agg['Crec_Com_L7D'] = safe_growth(cat_agg['Com_Pesos_L7D'], cat_agg['Com_Pesos_L7DLY'])
cat_agg['Crec_Piso_L7D'] = safe_growth(cat_agg['Piso_Pesos_L7D'], cat_agg['Piso_Pesos_L7DLY'])
cat_agg['Share_Com_MTD'] = cat_agg['Com_Pesos_MTD'] / (cat_agg['Com_Pesos_MTD'] + cat_agg['Piso_Pesos_MTD'])


def top_n(frame, n=20):
    return frame.head(n)


riesgo = top_n(
    df[(df['Semaforo_OH'].isin(['OOS', 'Crítico (<6)'])) & (df['Com_Pesos_MTD'] > 0)]
    .sort_values('Piso_Pesos_MTD', ascending=False)
)
impulsar = top_n(
    df[df['Crecimiento_Com_Pesos_MTD'] <= -0.10]
    .sort_values('Piso_Pesos_MTD', ascending=False)
)
replicar = top_n(
    df[df['Crecimiento_Com_Pesos_MTD'] >= 0.20]
    .sort_values('Com_Pesos_MTD', ascending=False)
)

print(f"[{team_key}] Movers (top 20 por volumen, SIN gate de parrilla/promo):")
print(f"  Riesgo: {len(riesgo)} | Impulsar: {len(impulsar)} | Replicar: {len(replicar)}")

cat_agg.to_csv(out_dir / 'cat_agg.csv', index=False, encoding='utf-8-sig')
df.to_csv(out_dir / 'merged_full.csv', index=False, encoding='utf-8-sig')
riesgo.to_csv(out_dir / 'movers_riesgo.csv', index=False, encoding='utf-8-sig')
impulsar.to_csv(out_dir / 'movers_impulsar.csv', index=False, encoding='utf-8-sig')
replicar.to_csv(out_dir / 'movers_replicar.csv', index=False, encoding='utf-8-sig')
print(f"[{team_key}] Guardado en {out_dir}")

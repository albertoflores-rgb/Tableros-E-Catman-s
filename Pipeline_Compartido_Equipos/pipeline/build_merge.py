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
    # Socios_Cat_* ya vienen correctos por categoria desde BigQuery
    # (COUNT DISTINCT Membresia_Nbr agrupado por Cat_Nbr -- ver
    # cte_socios_cat en query_item_total_template.sql). Son constantes
    # dentro de cada categoria, por eso 'first' y NUNCA 'sum' -- sumar
    # un COUNT(DISTINCT) ya agregado multiplicaria por el numero de
    # items de la categoria (ese era el bug original).
    Socios_Cat_MTD=('Socios_Cat_MTD', 'first'),
    Socios_Cat_MTDLY=('Socios_Cat_MTDLY', 'first'),
    Socios_Cat_YTD=('Socios_Cat_YTD', 'first'),
    Socios_Cat_YTDLY=('Socios_Cat_YTDLY', 'first'),
    Socios_Cat_L7D=('Socios_Cat_L7D', 'first'),
    Socios_Cat_L7DLY=('Socios_Cat_L7DLY', 'first'),
    N_Items=('Item_Nbr', 'nunique'),
).reset_index()

cat_agg['Crec_Com_MTD'] = safe_growth(cat_agg['Com_Pesos_MTD'], cat_agg['Com_Pesos_MTDLY'])
cat_agg['Crec_Piso_MTD'] = safe_growth(cat_agg['Piso_Pesos_MTD'], cat_agg['Piso_Pesos_MTDLY'])
cat_agg['Crec_Com_L7D'] = safe_growth(cat_agg['Com_Pesos_L7D'], cat_agg['Com_Pesos_L7DLY'])
cat_agg['Crec_Piso_L7D'] = safe_growth(cat_agg['Piso_Pesos_L7D'], cat_agg['Piso_Pesos_L7DLY'])
cat_agg['Share_Com_MTD'] = cat_agg['Com_Pesos_MTD'] / (cat_agg['Com_Pesos_MTD'] + cat_agg['Piso_Pesos_MTD'])


def top_n(frame, n=20):
    return frame.head(n)


# Universo COMPLETO que cumple cada filtro (sin cap) -- se usa para:
#   1. Conteos reales N_Riesgo/N_Impulsar/N_Replicar por categoria (cat_agg)
#   2. El detalle al hacer click en una tarjeta de categoria (ver
#      finalize_data.py -> categoria_items), igual que
#      accionables_items.csv en el pipeline de Abarrotes.
# Las tablas GLOBALES del tablero (top 20) siguen capadas -- no se toca
# ese comportamiento ya publicado, solo se agrega la vista por categoria.
riesgo_full = (
    df[(df['Semaforo_OH'].isin(['OOS', 'Crítico (<6)'])) & (df['Com_Pesos_MTD'] > 0)]
    .sort_values('Piso_Pesos_MTD', ascending=False)
)
impulsar_full = (
    df[df['Crecimiento_Com_Pesos_MTD'] <= -0.10]
    .sort_values('Piso_Pesos_MTD', ascending=False)
)
replicar_full = (
    df[df['Crecimiento_Com_Pesos_MTD'] >= 0.20]
    .sort_values('Com_Pesos_MTD', ascending=False)
)

riesgo = top_n(riesgo_full)
impulsar = top_n(impulsar_full)
replicar = top_n(replicar_full)

print(f"[{team_key}] Movers (top 20 GLOBAL por volumen, SIN gate de parrilla/promo):")
print(f"  Riesgo: {len(riesgo)}/{len(riesgo_full)} | Impulsar: {len(impulsar)}/{len(impulsar_full)} | Replicar: {len(replicar)}/{len(replicar_full)}")

# accionables_items.csv: union de los 3 universos completos con columna
# 'Accion' -- mismo nombre/forma que el pipeline de Abarrotes, para que
# finalize_data.py pueda agrupar por Cat_Desc y armar el detalle
# clickeable por tarjeta sin reinventar la logica de item_row().
accionables_items = pd.concat([
    riesgo_full.assign(Accion='Riesgo de quiebre'),
    impulsar_full.assign(Accion='Impulsar .com'),
    replicar_full.assign(Accion='Replicar exito'),
], ignore_index=True)

n_por_cat = accionables_items.groupby(['Cat_Desc', 'Accion']).size().unstack(fill_value=0)
for accion, col in (('Riesgo de quiebre', 'N_Riesgo'), ('Impulsar .com', 'N_Impulsar'), ('Replicar exito', 'N_Replicar')):
    cat_agg[col] = cat_agg['Cat_Desc'].map(n_por_cat.get(accion, {})).fillna(0).astype(int)

cat_agg.to_csv(out_dir / 'cat_agg.csv', index=False, encoding='utf-8-sig')
df.to_csv(out_dir / 'merged_full.csv', index=False, encoding='utf-8-sig')
riesgo.to_csv(out_dir / 'movers_riesgo.csv', index=False, encoding='utf-8-sig')
impulsar.to_csv(out_dir / 'movers_impulsar.csv', index=False, encoding='utf-8-sig')
replicar.to_csv(out_dir / 'movers_replicar.csv', index=False, encoding='utf-8-sig')
accionables_items.to_csv(out_dir / 'accionables_items.csv', index=False, encoding='utf-8-sig')
print(f"[{team_key}] Guardado en {out_dir}")

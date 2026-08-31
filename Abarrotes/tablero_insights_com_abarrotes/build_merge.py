# -*- coding: utf-8 -*-
"""Merge BQ + Promos + Parrilla, agrega a nivel categoria e item, genera JSON para el dashboard."""
import pandas as pd
import numpy as np
import json

pd.set_option('display.width', 200)

# ---------- Cargar fuentes ----------
bq = pd.read_csv('raw_bq_item_total.csv')
promos = pd.read_csv('promos_historico_abarrotes.csv')
parrilla = pd.read_csv('parrilla_agosto_abarrotes.csv')

# ---------- Promos vigentes (una fila por item, la promo vigente mas reciente) ----------
promos['ITEM ID'] = pd.to_numeric(promos['ITEM ID'], errors='coerce')
vigentes = promos[promos['Status'] == 'Vigente'].copy()
vigentes['INICIO'] = pd.to_datetime(vigentes['INICIO'], errors='coerce')
vigentes = vigentes.sort_values('INICIO').drop_duplicates('ITEM ID', keep='last')
vigentes = vigentes[['ITEM ID', 'PROMO', '% AHORRO', 'INICIO', 'FIN', 'FUENTE', 'Exclusivo Online']]
vigentes.columns = ['Item_Nbr', 'Promo_Desc', 'Pct_Ahorro', 'Promo_Inicio', 'Promo_Fin', 'Promo_Fuente', 'Promo_Canal']
# '% AHORRO' viene como texto en el CSV origen (mezcla numeros y '-' para
# promos sin descuento porcentual, ej. EDLP) -- convertir a numero real.
vigentes['Pct_Ahorro'] = pd.to_numeric(vigentes['Pct_Ahorro'], errors='coerce')

# ---------- Parrilla ----------
parrilla_set = set(parrilla['Item_Nbr'].astype('int64'))

# ---------- Merge ----------
bq['Item_Nbr'] = bq['Item_Nbr'].astype('int64')
df = bq.merge(vigentes, on='Item_Nbr', how='left')
df['En_Parrilla'] = df['Item_Nbr'].isin(parrilla_set)
df['Promo_Vigente'] = df['Promo_Inicio'].notna()
df['Accionable'] = df['En_Parrilla'] & df['Promo_Vigente']

print("Items totales Abarrotes:", len(df))
print("En parrilla:", df['En_Parrilla'].sum())
print("Con promo vigente:", df['Promo_Vigente'].sum())
print("Accionables (parrilla + promo vigente):", df['Accionable'].sum())

# ---------- Clasificacion de accion por item (solo accionables) ----------
def clasifica(row):
    crec_com = row['Crecimiento_Com_Pesos_MTD']
    oh = row['Semaforo_OH']
    if pd.isna(crec_com):
        crec_com = 0
    if oh in ('OOS', 'Crítico (<6)') and row['Com_Pesos_MTD'] > 0:
        return 'Riesgo de quiebre'
    if crec_com <= -0.10:
        return 'Impulsar .com'
    if crec_com >= 0.20:
        return 'Replicar exito'
    return 'Monitorear'

acc = df[df['Accionable']].copy()
acc['Accion'] = acc.apply(clasifica, axis=1)

# ---------- Metricas derivadas a nivel item: inventario total + share .com vs brick ----------
df['Inv_Pzas_Total'] = df['OHQty_Clubes'] + df['OHQty_FC_MX'] + df['OHQty_FC_MTY']
df['Inv_MXN_Total'] = df['OHQty_Clubes_MXN'] + df['OHMXN_FC_MX'] + df['OHMXN_FC_MTY']

for periodo in ('YTD', 'MTD', 'L7D'):
    com_col, piso_col = f'Com_Pesos_{periodo}', f'Piso_Pesos_{periodo}'
    total = df[com_col] + df[piso_col]
    df[f'Share_Com_{periodo}'] = np.where(total > 0, df[com_col] / total, np.nan)

acc = acc.merge(
    df[['Item_Nbr', 'Inv_Pzas_Total', 'Inv_MXN_Total', 'Share_Com_YTD', 'Share_Com_MTD', 'Share_Com_L7D']],
    on='Item_Nbr', how='left',
)

# ---------- Ranking .com L7D dentro de cada categoria (1 = top vendedor .com ultimos 7 dias) ----------
df['Top_L7D_Cat'] = (
    df.groupby('Cat_Nbr')['Com_Pesos_L7D']
    .rank(method='first', ascending=False)
    .astype(int)
)
acc = acc.merge(df[['Item_Nbr', 'Top_L7D_Cat']], on='Item_Nbr', how='left')

# ---------- Agregado a nivel categoria ----------
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

# accionables count por categoria
acc_counts = acc.groupby('Cat_Nbr').agg(
    N_Accionables=('Item_Nbr', 'nunique'),
    N_Impulsar=('Accion', lambda s: (s == 'Impulsar .com').sum()),
    N_Riesgo=('Accion', lambda s: (s == 'Riesgo de quiebre').sum()),
    N_Replicar=('Accion', lambda s: (s == 'Replicar exito').sum()),
).reset_index()
cat_agg = cat_agg.merge(acc_counts, on='Cat_Nbr', how='left').fillna(0)

cat_agg = cat_agg.sort_values('Com_Pesos_MTD', ascending=False)

print("\n=== Categorias ===")
print(cat_agg[['Cat_Desc', 'Com_Pesos_MTD', 'Crec_Com_MTD', 'Crec_Piso_MTD', 'Crec_Com_L7D', 'N_Accionables']])

# ---------- Guardar outputs ----------
cat_agg.to_csv('cat_agg.csv', index=False, encoding='utf-8-sig')
acc.to_csv('accionables_items.csv', index=False, encoding='utf-8-sig')
df.to_csv('merged_full.csv', index=False, encoding='utf-8-sig')

print("\nGuardado cat_agg.csv, accionables_items.csv, merged_full.csv")

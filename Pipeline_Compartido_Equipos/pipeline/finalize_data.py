# -*- coding: utf-8 -*-
"""finalize_data.py generico -- dashboard_data.json (Tab 1) para
cualquier equipo. Uso: python finalize_data.py <team_key>
"""
import sys
import pandas as pd
import json

from _common import team_dir, get_team_cfg

team_key = sys.argv[1]
cfg = get_team_cfg(team_key)
area = cfg['area']
out_dir = team_dir(team_key)

cat = pd.read_csv(out_dir / 'cat_agg.csv')
full = pd.read_csv(out_dir / 'merged_full.csv', low_memory=False)
riesgo = pd.read_csv(out_dir / 'movers_riesgo.csv')
impulsar = pd.read_csv(out_dir / 'movers_impulsar.csv')
replicar = pd.read_csv(out_dir / 'movers_replicar.csv')
acc = pd.read_csv(out_dir / 'accionables_items.csv', low_memory=False)


def r2(x):
    if pd.isna(x):
        return None
    return round(float(x), 4)


tot_com_mtd = full['Com_Pesos_MTD'].sum()
tot_com_mtdly = full['Com_Pesos_MTDLY'].sum()
tot_piso_mtd = full['Piso_Pesos_MTD'].sum()
tot_piso_mtdly = full['Piso_Pesos_MTDLY'].sum()
tot_com_l7d = full['Com_Pesos_L7D'].sum()
tot_com_l7dly = full['Com_Pesos_L7DLY'].sum()
tot_piso_l7d = full['Piso_Pesos_L7D'].sum()
tot_piso_l7dly = full['Piso_Pesos_L7DLY'].sum()

# Socios .com -- SOLO ecom (Piso/Brick no tiene grano de socio, ver
# nota en query_item_total_template.sql / cte_socios_cat). El total de
# equipo es la SUMA de los valores YA CORRECTOS por categoria en
# cat_agg (cada uno es un COUNT DISTINCT real hecho en BigQuery) -- es
# un APROXIMADO honesto: si un mismo socio compra en 2 categorias del
# equipo se cuenta 2 veces. Se etiqueta como tal en el frontend
# (badge "Piso: en construccion") para no aparentar mas precision de
# la que hay.
tot_socios_mtd = cat['Socios_Cat_MTD'].sum()
tot_socios_mtdly = cat['Socios_Cat_MTDLY'].sum()
tot_socios_ytd = cat['Socios_Cat_YTD'].sum()
tot_socios_l7d = cat['Socios_Cat_L7D'].sum()

kpis = {
    "com_mtd": r2(tot_com_mtd),
    "com_mtd_growth": r2((tot_com_mtd - tot_com_mtdly) / tot_com_mtdly),
    "piso_mtd": r2(tot_piso_mtd),
    "piso_mtd_growth": r2((tot_piso_mtd - tot_piso_mtdly) / tot_piso_mtdly),
    "com_l7d_growth": r2((tot_com_l7d - tot_com_l7dly) / tot_com_l7dly),
    "piso_l7d_growth": r2((tot_piso_l7d - tot_piso_l7dly) / tot_piso_l7dly),
    "share_com_mtd": r2(tot_com_mtd / (tot_com_mtd + tot_piso_mtd)),
    "com_socios_mtd": int(tot_socios_mtd),
    "com_socios_mtd_growth": (r2((tot_socios_mtd - tot_socios_mtdly) / tot_socios_mtdly) if tot_socios_mtdly else None),
    "com_socios_ytd": int(tot_socios_ytd),
    "com_socios_l7d": int(tot_socios_l7d),
    "socios_nota": "Solo .com -- Venta Piso/Brick en construccion. Aproximado: suma por categoria, puede haber traslape si un socio compro en mas de una.",
    "n_items": int(full['Item_Nbr'].nunique()),
    "n_riesgo": len(riesgo),
    "n_impulsar": len(impulsar),
    "n_replicar": len(replicar),
}

categorias = []
for _, r in cat.iterrows():
    categorias.append({
        "cat_nbr": int(r['Cat_Nbr']),
        "cat_desc": r['Cat_Desc'],
        "com_mtd": r2(r['Com_Pesos_MTD']),
        "com_mtdly": r2(r['Com_Pesos_MTDLY']),
        "crec_com_mtd": r2(r['Crec_Com_MTD']),
        "piso_mtd": r2(r['Piso_Pesos_MTD']),
        "piso_mtdly": r2(r['Piso_Pesos_MTDLY']),
        "crec_piso_mtd": r2(r['Crec_Piso_MTD']),
        "crec_com_l7d": r2(r['Crec_Com_L7D']),
        "crec_piso_l7d": r2(r['Crec_Piso_L7D']),
        "share_com_mtd": r2(r['Share_Com_MTD']),
        "n_items": int(r['N_Items']),
        "n_riesgo": int(r['N_Riesgo']),
        "n_impulsar": int(r['N_Impulsar']),
        "n_replicar": int(r['N_Replicar']),
    })
categorias.sort(key=lambda c: c['com_mtd'], reverse=True)


def item_row(r):
    return {
        "item_nbr": int(r['Item_Nbr']),
        "item_desc": r['Item_Desc_1'],
        "cat_desc": r['Cat_Desc'],
        "com_mtd": r2(r['Com_Pesos_MTD']),
        "crec_com_mtd": r2(r['Crecimiento_Com_Pesos_MTD']),
        "crec_com_l7d": r2(r['Crecimiento_Com_Pesos_L7D']),
        "piso_mtd": r2(r['Piso_Pesos_MTD']),
        "crec_piso_mtd": r2(r['Crecimiento_Piso_Pesos_MTD']),
        "semaforo": r['Semaforo_OH'],
        "top_l7d_cat": (int(r['Top_L7D_Cat']) if pd.notna(r['Top_L7D_Cat']) else None),
    }


movers = {
    "riesgo": [item_row(r) for _, r in riesgo.iterrows()],
    "impulsar": [item_row(r) for _, r in impulsar.iterrows()],
    "replicar": [item_row(r) for _, r in replicar.iterrows()],
}

# ---------- Listas por categoria (para expandir al dar click en las
# tarjetas) -- a diferencia de Abarrotes, aqui el universo que cumple
# cada filtro puede ser grande (sin gate de parrilla/promo), asi que se
# capa a top 15 por categoria (por volumen) para no inflar el JSON --
# el conteo real (chip de la tarjeta) SI viene del universo completo,
# ver N_Riesgo/N_Impulsar/N_Replicar en cat_agg.csv (build_merge.py). ----------
CAT_ITEM_CAP = 15
categoria_items = {}
for cat_desc, grp in acc.groupby('Cat_Desc'):
    cat_impulsar = grp[grp['Accion'] == 'Impulsar .com'].sort_values('Piso_Pesos_MTD', ascending=False).head(CAT_ITEM_CAP)
    cat_replicar = grp[grp['Accion'] == 'Replicar exito'].sort_values('Com_Pesos_MTD', ascending=False).head(CAT_ITEM_CAP)
    cat_riesgo = grp[grp['Accion'] == 'Riesgo de quiebre'].sort_values('Piso_Pesos_MTD', ascending=False).head(CAT_ITEM_CAP)
    categoria_items[cat_desc] = {
        "impulsar": [item_row(r) for _, r in cat_impulsar.iterrows()],
        "replicar": [item_row(r) for _, r in cat_replicar.iterrows()],
        "riesgo": [item_row(r) for _, r in cat_riesgo.iterrows()],
    }


def fmt_pct(x):
    sign = '+' if x >= 0 else ''
    return f"{sign}{x*100:.1f}%"


insights_top = []

decel = kpis['com_mtd_growth'] - kpis['com_l7d_growth']
if decel > 0.10:
    insights_top.append(
        f"<strong>[Alerta] El .com de {area} desacelera:</strong> crece {fmt_pct(kpis['com_mtd_growth'])} en el MTD vs LY, "
        f"pero la tendencia de los \u00faltimos 7 d\u00edas cae a {fmt_pct(kpis['com_l7d_growth'])} vs LY \u2014 revisar qu\u00e9 se fren\u00f3 esta \u00faltima semana."
    )
else:
    insights_top.append(
        f"<strong>[Positivo] El .com de {area} mantiene el paso:</strong> {fmt_pct(kpis['com_mtd_growth'])} en el MTD y "
        f"{fmt_pct(kpis['com_l7d_growth'])} en los \u00faltimos 7 d\u00edas vs LY \u2014 la tendencia reciente confirma el resultado del mes."
    )

insights_top.append(
    f"<strong>[Mix] .com {'crece' if kpis['com_mtd_growth'] >= 0 else 'cae'} {fmt_pct(kpis['com_mtd_growth'])} MTD</strong> vs Piso ({fmt_pct(kpis['piso_mtd_growth'])}), "
    f"y hoy representa {kpis['share_com_mtd']*100:.1f}% de la venta total de {area}."
)

top_cats_by_size = sorted(categorias, key=lambda c: c['com_mtd'], reverse=True)[:6]
best_l7d = max(top_cats_by_size, key=lambda c: c['crec_com_l7d'])
worst_l7d = min(top_cats_by_size, key=lambda c: c['crec_com_l7d'])
insights_top.append(
    f"<strong>[Momentum] {best_l7d['cat_desc']}</strong> tiene la mejor tendencia reciente en .com: {fmt_pct(best_l7d['crec_com_l7d'])} en los \u00faltimos 7 d\u00edas "
    f"(vs {fmt_pct(best_l7d['crec_com_mtd'])} en el MTD)."
)
if worst_l7d['crec_com_l7d'] < worst_l7d['crec_com_mtd']:
    insights_top.append(
        f"<strong>[Atenci\u00f3n] {worst_l7d['cat_desc']}</strong> es la que m\u00e1s se frena: {fmt_pct(worst_l7d['crec_com_mtd'])} en el MTD pero solo {fmt_pct(worst_l7d['crec_com_l7d'])} en los \u00faltimos 7 d\u00edas."
    )

insights_top.append(
    f"<strong>[Movers] {kpis['n_riesgo']} items</strong> con inventario cr\u00edtico/OOS y venta .com activa (top 20 por volumen Piso), "
    f"<strong>{kpis['n_impulsar']} items</strong> cayendo &le;-10% en .com MTD (top 20 por volumen Piso) y "
    f"<strong>{kpis['n_replicar']} items</strong> creciendo &ge;+20% en .com MTD (top 20 por volumen .com). "
    f"Nota: sin una parrilla/tracker de promos para {area} todav\u00eda, estas listas NO est\u00e1n curadas por promo vigente como en Abarrotes -- son top-20 puros por volumen."
)

data = {
    "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    "area": area,
    "owner": cfg['owner'],
    "kpis": kpis,
    "categorias": categorias,
    "movers": movers,
    "categoria_items": categoria_items,
    "insights_top": insights_top,
}

with open(out_dir / 'dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"[{team_key}] KPIs:", json.dumps(kpis, indent=2, ensure_ascii=False))
print(f"[{team_key}] Categorias:", len(categorias))

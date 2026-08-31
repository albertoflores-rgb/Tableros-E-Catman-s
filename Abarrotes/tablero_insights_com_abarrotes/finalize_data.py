# -*- coding: utf-8 -*-
"""Genera dashboard_data.json listo para inyectar en el HTML."""
import pandas as pd
import numpy as np
import json

cat = pd.read_csv('cat_agg.csv')
acc = pd.read_csv('accionables_items.csv')
full = pd.read_csv('merged_full.csv')

def r2(x):
    if pd.isna(x):
        return None
    return round(float(x), 4)

# ---------- KPIs globales (todo Abarrotes, 6 categorias) ----------
tot_com_mtd = full['Com_Pesos_MTD'].sum()
tot_com_mtdly = full['Com_Pesos_MTDLY'].sum()
tot_piso_mtd = full['Piso_Pesos_MTD'].sum()
tot_piso_mtdly = full['Piso_Pesos_MTDLY'].sum()
tot_com_l7d = full['Com_Pesos_L7D'].sum()
tot_com_l7dly = full['Com_Pesos_L7DLY'].sum()
tot_piso_l7d = full['Piso_Pesos_L7D'].sum()
tot_piso_l7dly = full['Piso_Pesos_L7DLY'].sum()

kpis = {
    "com_mtd": r2(tot_com_mtd),
    "com_mtd_growth": r2((tot_com_mtd - tot_com_mtdly) / tot_com_mtdly),
    "piso_mtd": r2(tot_piso_mtd),
    "piso_mtd_growth": r2((tot_piso_mtd - tot_piso_mtdly) / tot_piso_mtdly),
    "com_l7d_growth": r2((tot_com_l7d - tot_com_l7dly) / tot_com_l7dly),
    "piso_l7d_growth": r2((tot_piso_l7d - tot_piso_l7dly) / tot_piso_l7dly),
    "share_com_mtd": r2(tot_com_mtd / (tot_com_mtd + tot_piso_mtd)),
    "n_items": int(full['Item_Nbr'].nunique()),
    "n_parrilla": int(full['En_Parrilla'].sum()),
    "n_promo_vigente": int(full['Promo_Vigente'].sum()),
    "n_accionables": int(full['Accionable'].sum()),
    "n_impulsar": int((acc['Accion'] == 'Impulsar .com').sum()),
    "n_riesgo": int((acc['Accion'] == 'Riesgo de quiebre').sum()),
    "n_replicar": int((acc['Accion'] == 'Replicar exito').sum()),
    "n_monitorear": int((acc['Accion'] == 'Monitorear').sum()),
}

# ---------- Categorias ----------
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
        "n_accionables": int(r['N_Accionables']),
        "n_impulsar": int(r['N_Impulsar']),
        "n_riesgo": int(r['N_Riesgo']),
        "n_replicar": int(r['N_Replicar']),
    })
categorias.sort(key=lambda c: c['com_mtd'], reverse=True)

# ---------- Items accionables curados ----------
def item_row(r):
    top_rank = r.get('Top_L7D_Cat') if hasattr(r, 'get') else r['Top_L7D_Cat']
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
        "promo": r['Promo_Desc'] if pd.notna(r['Promo_Desc']) else None,
        "pct_ahorro": (r2(r['Pct_Ahorro']) if isinstance(r['Pct_Ahorro'], (int, float)) and not pd.isna(r['Pct_Ahorro']) else None),
        "promo_fin": (str(r['Promo_Fin'])[:10] if pd.notna(r['Promo_Fin']) else None),
        "accion": r['Accion'],
        "top_l7d_cat": (int(top_rank) if pd.notna(top_rank) else None),
    }

impulsar = acc[acc['Accion'] == 'Impulsar .com'].sort_values('Piso_Pesos_MTD', ascending=False)
riesgo = acc[acc['Accion'] == 'Riesgo de quiebre'].sort_values('Piso_Pesos_MTD', ascending=False)
replicar = (
    acc[acc['Accion'] == 'Replicar exito']
    .sort_values('Com_Pesos_MTD', ascending=False)
    .groupby('Cat_Desc', group_keys=False)
    .head(3)
    .sort_values('Com_Pesos_MTD', ascending=False)
)

accionables = {
    "impulsar": [item_row(r) for _, r in impulsar.iterrows()],
    "riesgo": [item_row(r) for _, r in riesgo.iterrows()],
    "replicar": [item_row(r) for _, r in replicar.iterrows()],
}

# ---------- Listas COMPLETAS por categoria (para expandir al dar click en las tarjetas) ----------
categoria_items = {}
for cat_desc, grp in acc.groupby('Cat_Desc'):
    cat_impulsar = grp[grp['Accion'] == 'Impulsar .com'].sort_values('Piso_Pesos_MTD', ascending=False)
    cat_replicar = grp[grp['Accion'] == 'Replicar exito'].sort_values('Com_Pesos_MTD', ascending=False)
    cat_riesgo = grp[grp['Accion'] == 'Riesgo de quiebre'].sort_values('Piso_Pesos_MTD', ascending=False)
    categoria_items[cat_desc] = {
        "impulsar": [item_row(r) for _, r in cat_impulsar.iterrows()],
        "replicar": [item_row(r) for _, r in cat_replicar.iterrows()],
        "riesgo": [item_row(r) for _, r in cat_riesgo.iterrows()],
    }

# ---------- Insights ejecutivos (texto generado con numeros reales) ----------
def fmt_pct(x):
    sign = '+' if x >= 0 else ''
    return f"{sign}{x*100:.1f}%"

insights_top = []

decel = kpis['com_mtd_growth'] - kpis['com_l7d_growth']
if decel > 0.10:
    insights_top.append(
        f"<strong>[Alerta] El .com de Abarrotes desacelera:</strong> crece {fmt_pct(kpis['com_mtd_growth'])} en el MTD vs LY, "
        f"pero la tendencia de los \u00faltimos 7 d\u00edas cae a {fmt_pct(kpis['com_l7d_growth'])} vs LY \u2014 revisar qu\u00e9 se fren\u00f3 esta \u00faltima semana."
    )
else:
    insights_top.append(
        f"<strong>[Positivo] El .com de Abarrotes mantiene el paso:</strong> {fmt_pct(kpis['com_mtd_growth'])} en el MTD y "
        f"{fmt_pct(kpis['com_l7d_growth'])} en los \u00faltimos 7 d\u00edas vs LY \u2014 la tendencia reciente confirma el resultado del mes."
    )

insights_top.append(
    f"<strong>[Mix] .com crece {fmt_pct(kpis['com_mtd_growth'])} MTD</strong>, muy por encima de Piso ({fmt_pct(kpis['piso_mtd_growth'])}), "
    f"pero .com todav\u00eda es solo {kpis['share_com_mtd']*100:.1f}% de la venta total de Abarrotes \u2014 el canal sigue chico frente a la oportunidad."
)

top_cats_by_size = sorted(categorias, key=lambda c: c['com_mtd'], reverse=True)[:4]
best_l7d = max(top_cats_by_size, key=lambda c: c['crec_com_l7d'])
worst_l7d = min(top_cats_by_size, key=lambda c: c['crec_com_l7d'])
insights_top.append(
    f"<strong>[Momentum] {best_l7d['cat_desc']}</strong> tiene la mejor tendencia reciente en .com: {fmt_pct(best_l7d['crec_com_l7d'])} en los \u00faltimos 7 d\u00edas "
    f"(vs {fmt_pct(best_l7d['crec_com_mtd'])} en el MTD) \u2014 replicar lo que est\u00e1 funcionando ah\u00ed en otras categor\u00edas."
)
if worst_l7d['crec_com_l7d'] < worst_l7d['crec_com_mtd']:
    insights_top.append(
        f"<strong>[Atenci\u00f3n] {worst_l7d['cat_desc']}</strong> es la que m\u00e1s se frena: {fmt_pct(worst_l7d['crec_com_mtd'])} en el MTD pero solo {fmt_pct(worst_l7d['crec_com_l7d'])} en los \u00faltimos 7 d\u00edas \u2014 "
        f"tiene {worst_l7d['n_accionables']} items en parrilla + promo vigente listos para empujar."
    )

insights_top.append(
    f"<strong>[Accionables] {kpis['n_accionables']} items</strong> est\u00e1n en parrilla 10+1 de agosto CON promo vigente \u2014 "
    f"{kpis['n_impulsar']} necesitan impulso inmediato en .com (crecimiento negativo pese a promo activa) y "
    f"{kpis['n_replicar']} ya son casos de \u00e9xito ({fmt_pct(0.20)} o m\u00e1s de crecimiento) que conviene replicar en banners/b\u00fasqueda."
)

data = {
    "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    "kpis": kpis,
    "categorias": categorias,
    "accionables": accionables,
    "categoria_items": categoria_items,
    "insights_top": insights_top,
}

with open('dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("KPIs:", json.dumps(kpis, indent=2, ensure_ascii=False))
print("\nCategorias:", len(categorias))
print("Impulsar:", len(accionables['impulsar']), "Riesgo:", len(accionables['riesgo']), "Replicar:", len(accionables['replicar']))
print("\nGuardado dashboard_data.json")

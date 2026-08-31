# -*- coding: utf-8 -*-
"""Genera promos_data.json: detalle de promos vigentes + mapeo en sitio
(carruseles de Home, LP Despensa y LP Socio de Negocio) para la pestana 3.
Incluye las mismas metricas YTD/MTD/L7D + inventario + share que el
Explorador BQ (pestana 2), mas los datos propios de la promo y el mapeo."""
import pandas as pd
import json

site = pd.read_csv('site_mapping.csv')


def r2(x):
    if pd.isna(x):
        return None
    return round(float(x), 4)


def clean(x):
    return None if pd.isna(x) else x


def periodo_dict(r, periodo):
    return {
        "piso_pzas": r2(r[f'Piso_Pzas_{periodo}']),
        "piso_pesos": r2(r[f'Piso_Pesos_{periodo}']),
        "com_pzas": r2(r[f'Com_Pzas_{periodo}']),
        "com_pesos": r2(r[f'Com_Pesos_{periodo}']),
        "piso_pesos_ly": r2(r[f'Piso_Pesos_{periodo}LY']),
        "com_pesos_ly": r2(r[f'Com_Pesos_{periodo}LY']),
        "crec_piso": r2(r[f'Crecimiento_Piso_Pesos_{periodo}']),
        "crec_com": r2(r[f'Crecimiento_Com_Pesos_{periodo}']),
        "share_com": r2(r[f'Share_Com_{periodo}']),
    }


items = []
for _, r in site.iterrows():
    items.append({
        "item_nbr": int(r['Item_Nbr']),
        "item_desc": r['Item_Desc'],
        "cat_desc": clean(r['Cat_Desc']),
        "sub_cat_desc": clean(r['Sub_Cat_Desc']),
        "promo_desc": clean(r['Promo_Desc']),
        "pct_ahorro": r2(r['Pct_Ahorro']) if isinstance(r['Pct_Ahorro'], (int, float)) else None,
        "promo_fin": (str(r['Promo_Fin'])[:10] if pd.notna(r['Promo_Fin']) else None),
        "semaforo": clean(r['Semaforo_OH']),
        "top_l7d_cat": (int(r['Top_L7D_Cat']) if pd.notna(r['Top_L7D_Cat']) else None),
        "tiendas_con_inv": (int(r['Club_con_Inventario']) if pd.notna(r['Club_con_Inventario']) else None),
        "inv_pzas_total": r2(r['Inv_Pzas_Total']),
        "inv_mxn_total": r2(r['Inv_MXN_Total']),
        "ytd": periodo_dict(r, 'YTD'),
        "mtd": periodo_dict(r, 'MTD'),
        "l7d": periodo_dict(r, 'L7D'),
        "com_mtd": r2(r['Com_Pesos_MTD']),
        "crec_com_mtd": r2(r['Crecimiento_Com_Pesos_MTD']),
        "visto_en": r['Visto_En'],
        "n_paginas": int(r['N_Paginas']),
        "home": {
            "visto": bool(r['match_Home']),
            "score": r2(r['match_Home_score']),
            "carrusel": clean(r['match_Home_carrusel']),
            "producto": clean(r['match_Home_producto']),
        },
        "despensa": {
            "visto": bool(r['match_Despensa']),
            "score": r2(r['match_Despensa_score']),
            "carrusel": clean(r['match_Despensa_carrusel']),
            "producto": clean(r['match_Despensa_producto']),
        },
        "socio_negocio": {
            "visto": bool(r['match_Socio de Negocio']),
            "score": r2(r['match_Socio de Negocio_score']),
            "carrusel": clean(r['match_Socio de Negocio_carrusel']),
            "producto": clean(r['match_Socio de Negocio_producto']),
        },
    })

# Ordenar: primero los que NO se ven en ningun lado (oportunidad), luego por venta .com desc
items.sort(key=lambda x: (x['n_paginas'], -(x['com_mtd'] or 0)))

n_total = len(items)
n_vistos = sum(1 for i in items if i['n_paginas'] > 0)
n_home = sum(1 for i in items if i['home']['visto'])
n_despensa = sum(1 for i in items if i['despensa']['visto'])
n_socio = sum(1 for i in items if i['socio_negocio']['visto'])

summary = {
    "n_total": n_total,
    "n_vistos": n_vistos,
    "n_no_vistos": n_total - n_vistos,
    "n_home": n_home,
    "n_despensa": n_despensa,
    "n_socio_negocio": n_socio,
    "pct_vistos": round(n_vistos / n_total, 4) if n_total else 0,
}

data = {
    "summary": summary,
    "items": items,
    "disclaimer": (
        "Mapeo aproximado por texto (el sitio no expone SKU en el HTML, solo "
        "nombre de producto). El score indica que tan fuerte fue la coincidencia "
        "de palabras entre la descripcion de BQ y el nombre visible en el "
        "carrusel -- usar como referencia direccional, no como fuente exacta."
    ),
}

with open('promos_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Resumen:", json.dumps(summary, indent=2, ensure_ascii=False))
print("Guardado promos_data.json")

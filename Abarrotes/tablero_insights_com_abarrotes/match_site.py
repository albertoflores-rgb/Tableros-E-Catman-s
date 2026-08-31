# -*- coding: utf-8 -*-
"""Cruza promos vigentes (item desc abreviada de BQ/promos) contra los carruseles
reales del sitio (site_carousel_items.json) usando matching por tokens (no hay
SKU visible en el front, solo nombres de producto)."""
import json
import re
import unicodedata
import pandas as pd

STOPWORDS = {
    'DE', 'LA', 'EL', 'LOS', 'LAS', 'CON', 'PARA', 'Y', 'A', 'EN', 'SIN',
    'PZAS', 'PZA', 'PIEZA', 'PIEZAS', 'KG', 'GR', 'G', 'ML', 'L', 'C', 'U',
    'CU', 'PACK', 'CAJA', 'BOTE', 'BOLSA', 'SOBRE', 'SOBRES', 'VARIOS',
    'SURTIDO', 'SURTIDOS', 'REGULAR', 'CLASICO', 'CLASICA',
}


def normalize(text):
    if not isinstance(text, str):
        return []
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.upper()
    text = re.sub(r"([A-Z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([A-Z])", r"\1 \2", text)
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    tokens = [t for t in text.split() if len(t) >= 2 and t not in STOPWORDS]
    return tokens


def match_score(item_tokens, product_tokens):
    if not item_tokens:
        return 0.0, 0
    item_set, prod_set = set(item_tokens), set(product_tokens)
    overlap = item_set & prod_set
    return len(overlap) / len(item_set), len(overlap)


def best_match_in_page(item_tokens, carousels):
    best = {"score": 0.0, "overlap": 0, "carrusel": None, "producto": None}
    for c in carousels:
        for prod in c["items"]:
            score, overlap = match_score(item_tokens, normalize(prod))
            if score > best["score"]:
                best = {"score": round(score, 2), "overlap": overlap, "carrusel": c["titulo"], "producto": prod}
    return best


def main():
    promos = pd.read_csv('promos_historico_abarrotes.csv')
    promos['ITEM ID'] = pd.to_numeric(promos['ITEM ID'], errors='coerce')
    vigentes = promos[promos['Status'] == 'Vigente'].copy()
    vigentes['INICIO'] = pd.to_datetime(vigentes['INICIO'], errors='coerce')
    vigentes = vigentes.sort_values('INICIO').drop_duplicates('ITEM ID', keep='last')
    # '% AHORRO' viene como texto en el CSV origen (mezcla numeros y '-' para
    # promos sin descuento porcentual, ej. EDLP) -- convertir a numero real.
    vigentes['% AHORRO'] = pd.to_numeric(vigentes['% AHORRO'], errors='coerce')

    bq = pd.read_csv('merged_full.csv')[
        [
            'Item_Nbr', 'Item_Desc_1', 'Cat_Desc', 'Sub_Cat_Desc', 'Semaforo_OH',
            'Top_L7D_Cat', 'Club_con_Inventario', 'Inv_Pzas_Total', 'Inv_MXN_Total',
            'Piso_Pzas_YTD', 'Piso_Pesos_YTD', 'Com_Pzas_YTD', 'Com_Pesos_YTD',
            'Piso_Pzas_MTD', 'Piso_Pesos_MTD', 'Com_Pzas_MTD', 'Com_Pesos_MTD',
            'Piso_Pzas_L7D', 'Piso_Pesos_L7D', 'Com_Pzas_L7D', 'Com_Pesos_L7D',
            'Piso_Pesos_YTDLY', 'Com_Pesos_YTDLY', 'Piso_Pesos_MTDLY', 'Com_Pesos_MTDLY',
            'Piso_Pesos_L7DLY', 'Com_Pesos_L7DLY',
            'Crecimiento_Com_Pesos_YTD', 'Crecimiento_Piso_Pesos_YTD',
            'Crecimiento_Com_Pesos_MTD', 'Crecimiento_Piso_Pesos_MTD',
            'Crecimiento_Com_Pesos_L7D', 'Crecimiento_Piso_Pesos_L7D',
            'Share_Com_YTD', 'Share_Com_MTD', 'Share_Com_L7D',
        ]
    ].drop_duplicates('Item_Nbr')
    bq['Item_Nbr'] = bq['Item_Nbr'].astype('int64')

    vigentes = vigentes.rename(columns={'ITEM ID': 'Item_Nbr'})
    vigentes['Item_Nbr'] = vigentes['Item_Nbr'].astype('int64')
    vigentes = vigentes.merge(bq, on='Item_Nbr', how='left')

    with open('site_carousel_items.json', 'r', encoding='utf-8') as f:
        site = json.load(f)
    pages = {p['page']: p['carousels'] for p in site['pages']}

    rows = []
    threshold = 0.6
    min_overlap = 2
    extra_cols = [
        'Sub_Cat_Desc', 'Semaforo_OH', 'Top_L7D_Cat', 'Club_con_Inventario',
        'Inv_Pzas_Total', 'Inv_MXN_Total',
        'Piso_Pzas_YTD', 'Piso_Pesos_YTD', 'Com_Pzas_YTD', 'Com_Pesos_YTD',
        'Piso_Pzas_MTD', 'Piso_Pesos_MTD', 'Com_Pzas_MTD', 'Com_Pesos_MTD',
        'Piso_Pzas_L7D', 'Piso_Pesos_L7D', 'Com_Pzas_L7D', 'Com_Pesos_L7D',
        'Piso_Pesos_YTDLY', 'Com_Pesos_YTDLY', 'Piso_Pesos_MTDLY', 'Com_Pesos_MTDLY',
        'Piso_Pesos_L7DLY', 'Com_Pesos_L7DLY',
        'Crecimiento_Com_Pesos_YTD', 'Crecimiento_Piso_Pesos_YTD',
        'Crecimiento_Com_Pesos_MTD', 'Crecimiento_Piso_Pesos_MTD',
        'Crecimiento_Com_Pesos_L7D', 'Crecimiento_Piso_Pesos_L7D',
        'Share_Com_YTD', 'Share_Com_MTD', 'Share_Com_L7D',
    ]
    for _, r in vigentes.iterrows():
        desc = r['Item_Desc_1'] if pd.notna(r['Item_Desc_1']) else r['ITEM DESC.']
        item_tokens = normalize(desc)
        row = {
            'Item_Nbr': int(r['Item_Nbr']),
            'Item_Desc': desc,
            'Cat_Desc': r.get('Cat_Desc'),
            'Promo_Desc': r['PROMO'],
            'Pct_Ahorro': r['% AHORRO'],
            'Promo_Fin': r['FIN'],
        }
        for c in extra_cols:
            row[c] = r.get(c)
        visto_en = []
        for page_name, carousels in pages.items():
            m = best_match_in_page(item_tokens, carousels)
            found = m['score'] >= threshold and m['overlap'] >= min_overlap
            row[f'match_{page_name}'] = found
            row[f'match_{page_name}_score'] = m['score']
            row[f'match_{page_name}_carrusel'] = m['carrusel'] if found else None
            row[f'match_{page_name}_producto'] = m['producto'] if found else None
            if found:
                visto_en.append(page_name)
        row['Visto_En'] = ', '.join(visto_en) if visto_en else 'Ninguno'
        row['N_Paginas'] = len(visto_en)
        rows.append(row)

    out = pd.DataFrame(rows)
    out = out.sort_values(['N_Paginas', 'Com_Pesos_MTD'], ascending=[True, False])
    out.to_csv('site_mapping.csv', index=False, encoding='utf-8-sig')

    print("Total promos vigentes:", len(out))
    print("Vistas en al menos 1 carrusel:", (out['N_Paginas'] > 0).sum())
    print("NO vistas en ningun carrusel:", (out['N_Paginas'] == 0).sum())
    print(out[['Item_Desc', 'Visto_En']].head(20).to_string(index=False))


if __name__ == '__main__':
    main()

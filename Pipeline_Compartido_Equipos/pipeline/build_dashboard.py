# -*- coding: utf-8 -*-
"""build_dashboard.py generico -- ensambla el HTML final para cualquier
equipo a partir de las plantillas compartidas en templates/.
Uso: python build_dashboard.py <team_key>
"""
import sys
import json

from _common import team_dir, get_team_cfg, PIPELINE_DIR

team_key = sys.argv[1]
cfg = get_team_cfg(team_key)
out_dir = team_dir(team_key)
tpl_dir = PIPELINE_DIR / 'templates'


def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


shell = read(tpl_dir / 'tpl_shell.html')
tab1_html = read(tpl_dir / 'tpl_tab1.html')
tab2_html = read(tpl_dir / 'tpl_tab2.html')
tab3_html = read(tpl_dir / 'tpl_tab3.html')
tab1_js = read(tpl_dir / 'tpl_tab1.js')
tab2_js = read(tpl_dir / 'tpl_tab2.js')
tab3_js = read(tpl_dir / 'tpl_tab3.js')

with open(out_dir / 'dashboard_data.json', 'r', encoding='utf-8') as f:
    data1 = json.load(f)
with open(out_dir / 'explorer_data.json', 'r', encoding='utf-8') as f:
    data2 = json.load(f)
with open(out_dir / 'sept_data.json', 'r', encoding='utf-8') as f:
    data3 = json.load(f)

n_cats = len(data1['categorias'])

html = (
    shell
    .replace('__TAB1__', tab1_html)
    .replace('__TAB2__', tab2_html)
    .replace('__TAB3__', tab3_html)
    .replace('__SCRIPT1__', tab1_js)
    .replace('__SCRIPT2__', tab2_js)
    .replace('__SCRIPT3__', tab3_js)
    .replace('__DATA1__', json.dumps(data1, ensure_ascii=False))
    .replace('__DATA2__', json.dumps(data2, ensure_ascii=False))
    .replace('__DATA3__', json.dumps(data3, ensure_ascii=False))
    .replace('__GENERATED_AT__', data1['generated_at'])
    .replace('__AREA__', cfg['area'])
    .replace('__OWNER__', cfg['owner'])
    .replace('__N_CATS__', str(n_cats))
)

# tab1_html/tab2_html tambien traen __AREA__/__OWNER__ -- ya se sustituyeron
# arriba porque se insertaron ANTES del segundo bloque de .replace().

out_path = out_dir / f'tablero_insights_com_{team_key}.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[{team_key}] Guardado {out_path}")
print(f"[{team_key}] Tamano: {round(len(html) / 1024, 1)} KB")

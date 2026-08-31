# -*- coding: utf-8 -*-
"""Ensambla el tablero final (4 pestanas) a partir de las plantillas tpl_*.html/js
y los 4 JSON de datos (dashboard_data.json, explorer_data.json, promos_data.json,
sept_data.json)."""
import json


def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


shell = read('tpl_shell.html')
tab1_html = read('tpl_tab1.html')
tab2_html = read('tpl_tab2.html')
tab3_html = read('tpl_tab3.html')
tab4_html = read('tpl_tab4.html')
tab5_html = read('tpl_tab5.html')
tab1_js = read('tpl_tab1.js')
tab2_js = read('tpl_tab2.js')
tab3_js = read('tpl_tab3.js')
tab4_js = read('tpl_tab4.js')
tab5_js = read('tpl_tab5.js')

with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    data1 = json.load(f)
with open('explorer_data.json', 'r', encoding='utf-8') as f:
    data2 = json.load(f)
with open('promos_data.json', 'r', encoding='utf-8') as f:
    data3 = json.load(f)
with open('sept_data.json', 'r', encoding='utf-8') as f:
    data4 = json.load(f)
with open('historico_data.json', 'r', encoding='utf-8') as f:
    data5 = json.load(f)

html = (
    shell
    .replace('__TAB1__', tab1_html)
    .replace('__TAB2__', tab2_html)
    .replace('__TAB3__', tab3_html)
    .replace('__TAB4__', tab4_html)
    .replace('__TAB5__', tab5_html)
    .replace('__SCRIPT1__', tab1_js)
    .replace('__SCRIPT2__', tab2_js)
    .replace('__SCRIPT3__', tab3_js)
    .replace('__SCRIPT4__', tab4_js)
    .replace('__SCRIPT5__', tab5_js)
    .replace('__DATA1__', json.dumps(data1, ensure_ascii=False))
    .replace('__DATA2__', json.dumps(data2, ensure_ascii=False))
    .replace('__DATA3__', json.dumps(data3, ensure_ascii=False))
    .replace('__DATA4__', json.dumps(data4, ensure_ascii=False))
    .replace('__DATA5__', json.dumps(data5, ensure_ascii=False))
    .replace('__GENERATED_AT__', data1['generated_at'])
)

out_path = 'tablero_insights_com_abarrotes.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print('Guardado', out_path)
print('Tamano:', round(len(html) / 1024, 1), 'KB')

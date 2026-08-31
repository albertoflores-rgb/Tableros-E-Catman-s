# -*- coding: utf-8 -*-
"""Extrae la hoja Historico de promos (filtrada a Abarrotes) a CSV."""
import sys, os, csv
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl

ABARROTES_CATS = {41, 43, 46, 49, 53, 68}

base = "C:\\Users\\a0f07dn\\OneDrive - Walmart Inc\\W2\\Sam\u00b4s\\E-Catman\\Promos Activas\\Agosto"
fname = [f for f in os.listdir(base) if f.startswith("Hist")][0]
path = os.path.join(base, fname)
print("Leyendo:", path)

wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
ws = wb["Histórico"]

rows_iter = ws.iter_rows(min_row=2, values_only=True)
header = next(rows_iter)
header = [h if h else f"col{i}" for i, h in enumerate(header)]
print("Header:", header)

out_rows = []
for r in rows_iter:
    if r[0] is None:
        continue
    try:
        cat = int(r[0])
    except (TypeError, ValueError):
        continue
    if cat not in ABARROTES_CATS:
        continue
    out_rows.append(r)

print("Filas Abarrotes en Historico:", len(out_rows))

out_path = "promos_historico_abarrotes.csv"
with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(header[:len(header)])
    for r in out_rows:
        writer.writerow(r)
print("Guardado:", out_path)

# -*- coding: utf-8 -*-
"""Extrae items de parrilla 10+1 (todas las semanas de agosto), filtrado a Abarrotes."""
import sys, os, csv, pathlib
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl

ABARROTES_CATS = {41, 43, 46, 49, 53, 68}
WEEK_SHEETS = ["10+1 10082026", "10+1 17082026", "10+1 24082026", "10+1 31082026"]

onedrive_root = pathlib.Path(r"C:\Users\a0f07dn\OneDrive - Walmart Inc")
base = next(onedrive_root.rglob("Promos Activas")) / "Agosto"
fname = [f for f in os.listdir(base) if f.startswith("Parrilla")][0]
path = os.path.join(base, fname)
print("Leyendo:", path)

wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

item_weeks = {}   # item_nbr -> set of week labels
item_meta = {}    # item_nbr -> (desc, cat, subcat, subcat_desc, promocion)

for sheet in WEEK_SHEETS:
    ws = wb[sheet]
    rows_iter = ws.iter_rows(min_row=4, values_only=True)  # data starts row 4 (header row3)
    n = 0
    for r in rows_iter:
        if r[0] is None:
            continue
        try:
            item_nbr = int(r[0])
            cat = int(r[2])
        except (TypeError, ValueError):
            continue
        if cat not in ABARROTES_CATS:
            continue
        item_weeks.setdefault(item_nbr, set()).add(sheet)
        if item_nbr not in item_meta:
            item_meta[item_nbr] = (r[1], cat, r[4], r[5], r[14] if len(r) > 14 else None)
        n += 1
    print(sheet, "-> items abarrotes:", n)

out_path = "parrilla_agosto_abarrotes.csv"
with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Item_Nbr", "Item_Desc", "Cat_Nbr", "Subcat_Nbr", "Subcat_Desc", "Promocion", "Semanas_En_Parrilla", "N_Semanas"])
    for item_nbr, weeks in item_weeks.items():
        desc, cat, subcat, subcat_desc, promo = item_meta[item_nbr]
        writer.writerow([item_nbr, desc, cat, subcat, subcat_desc, promo, "|".join(sorted(weeks)), len(weeks)])

print("Total items unicos parrilla Abarrotes (Agosto):", len(item_weeks))
print("Guardado:", out_path)

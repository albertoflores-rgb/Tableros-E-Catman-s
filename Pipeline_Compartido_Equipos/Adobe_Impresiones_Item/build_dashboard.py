# -*- coding: utf-8 -*-
"""Construye el tablero standalone de Adobe Impresiones por Item --
HTML plano (Tailwind + Chart.js, sin servidor), con boton de descarga
de CSV (client-side, autocontenido en el HTML -- no depende de un
archivo separado sobrevivir la publicacion en Puppy Pages).

Enriquece el crudo de BigQuery (Item_Nbr, Ocurrencias) con
descripcion/categoria/marca del catalogo local (catalogo_slim.csv,
llave item9) para que la tabla sea legible, no solo SKUs pelones.

Uso:
    python build_dashboard.py
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

APP_DIR = Path(__file__).parent
WORKSPACE_DIR = APP_DIR.parent
RAW_CSV = APP_DIR / "raw_adobe_impresiones_item.csv"
CATALOGO_CSV = WORKSPACE_DIR / "catalogo_slim.csv"
OUT_HTML = APP_DIR / "tablero_adobe_impresiones_item.html"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV, dtype={"Item_Nbr": str})
    df["Ocurrencias"] = df["Ocurrencias"].astype(int)

    cat = pd.read_csv(
        CATALOGO_CSV, dtype={"item9": str}, encoding="utf-8", encoding_errors="replace"
    )
    cat = cat.rename(columns={"item9": "Item_Nbr"})[
        ["Item_Nbr", "desc", "squad", "categoria", "subcategoria", "marca"]
    ]
    for col in ["desc", "squad", "categoria", "subcategoria", "marca"]:
        cat[col] = cat[col].astype(str).str.strip()
    cat = cat.drop_duplicates(subset="Item_Nbr")

    merged = df.merge(cat, on="Item_Nbr", how="left")
    return merged


def build_kpis(df: pd.DataFrame, fecha: str) -> dict:
    n_items = len(df)
    n_matched = df["desc"].notna().sum()
    return {
        "fecha": fecha,
        "n_items": n_items,
        "n_matched": int(n_matched),
        "pct_matched": round(n_matched / n_items * 100, 1) if n_items else 0,
        "total_ocurrencias": int(df["Ocurrencias"].sum()),
        "top_squad": (
            df.groupby("squad")["Ocurrencias"].sum().sort_values(ascending=False).index[0]
            if df["squad"].notna().any()
            else "N/D"
        ),
    }


def build_html(df: pd.DataFrame, kpis: dict) -> str:
    df_sorted = df.sort_values("Ocurrencias", ascending=False).reset_index(drop=True)
    top20 = df_sorted.head(20)

    table_rows = df_sorted.fillna("").to_dict(orient="records")
    csv_rows = df_sorted.fillna("").to_dict(orient="records")

    chart_labels = json.dumps(
        [(r["desc"][:28] + "..." if isinstance(r["desc"], str) and len(r["desc"]) > 28
          else (r["desc"] or r["Item_Nbr"])) for r in top20.fillna("").to_dict(orient="records")],
        ensure_ascii=False,
    )
    chart_values = json.dumps([int(v) for v in top20["Ocurrencias"].tolist()])
    table_json = json.dumps(table_rows, ensure_ascii=False)
    csv_json = json.dumps(csv_rows, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Adobe Impresiones por Item -- Sam's Club MX (Standalone)</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
</head>
<body class="bg-gray-50 text-gray-800">
<div class="max-w-7xl mx-auto px-4 py-8">

  <header class="mb-8">
    <h1 class="text-3xl font-bold text-[#004B8D]">Adobe Impresiones por Item</h1>
    <p class="text-gray-500 mt-1">
      Tablero standalone -- revivido del "Total Departamentos V1" (Puppy Pages), separado
      del tablero actual de Total Departamentos. Fuente: Adobe Analytics (proxy searchResults +
      browseResults, eVar168), fecha <strong>{kpis['fecha']}</strong>.
    </p>
    <p class="text-xs text-gray-400 mt-2">
      Query: <code>Respaldo_Querys/saved_queries/SAMS - Adobe Impresiones Item (Investigacion) v2.sql</code>
      &middot; "Impresion" es un proxy validado con datos, no un evento oficial de Adobe Event Manager
      (pendiente confirmar nombre oficial con Adobe Admin).
    </p>
  </header>

  <section class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white rounded-xl shadow p-4">
      <p class="text-xs text-gray-400 uppercase">Items con impresion</p>
      <p class="text-2xl font-bold text-[#004B8D]">{kpis['n_items']:,}</p>
    </div>
    <div class="bg-white rounded-xl shadow p-4">
      <p class="text-xs text-gray-400 uppercase">Ocurrencias totales</p>
      <p class="text-2xl font-bold text-[#004B8D]">{kpis['total_ocurrencias']:,}</p>
    </div>
    <div class="bg-white rounded-xl shadow p-4">
      <p class="text-xs text-gray-400 uppercase">% con match a catalogo</p>
      <p class="text-2xl font-bold text-[#A4CE4E]">{kpis['pct_matched']}%</p>
    </div>
    <div class="bg-white rounded-xl shadow p-4">
      <p class="text-xs text-gray-400 uppercase">Squad con mas impresiones</p>
      <p class="text-xl font-bold text-[#004B8D]">{kpis['top_squad']}</p>
    </div>
  </section>

  <section class="bg-white rounded-xl shadow p-4 mb-8">
    <h2 class="font-bold text-lg mb-3">Top 20 items por ocurrencias</h2>
    <div style="height: 380px;">
      <canvas id="topChart"></canvas>
    </div>
  </section>

  <section class="bg-white rounded-xl shadow p-4">
    <div class="flex items-center justify-between flex-wrap gap-3 mb-3">
      <h2 class="font-bold text-lg">Detalle completo ({kpis['n_items']:,} items)</h2>
      <div class="flex gap-2 items-center">
        <input id="searchBox" type="text" placeholder="Buscar item, descripcion, categoria..."
               class="border rounded px-3 py-1.5 text-sm w-64">
        <button id="downloadBtn"
                class="bg-[#004B8D] text-white text-sm px-4 py-1.5 rounded hover:opacity-90">
          Descargar CSV
        </button>
      </div>
    </div>
    <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
      <table class="w-full text-sm">
        <thead class="sticky top-0 bg-gray-100">
          <tr>
            <th class="text-left p-2">Item_Nbr</th>
            <th class="text-left p-2">Descripcion</th>
            <th class="text-left p-2">Squad</th>
            <th class="text-left p-2">Categoria</th>
            <th class="text-left p-2">Marca</th>
            <th class="text-right p-2">Ocurrencias</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </section>

  <footer class="text-xs text-gray-400 mt-8">
    Generado por Tyzon (Code Puppy) &middot; datos crudos de BigQuery, sin muestreo
    &middot; costo real de esta corrida: ver <code>run_query.py</code>
  </footer>
</div>

<script>
const TABLE_DATA = {table_json};
const CSV_DATA = {csv_json};

function renderTable(rows) {{
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = rows.map(r => `
    <tr class="border-b hover:bg-gray-50">
      <td class="p-2 font-mono">${{r.Item_Nbr}}</td>
      <td class="p-2">${{r.desc || '<span class="text-gray-300">sin match</span>'}}</td>
      <td class="p-2">${{r.squad || '-'}}</td>
      <td class="p-2">${{r.categoria || '-'}}</td>
      <td class="p-2">${{r.marca || '-'}}</td>
      <td class="p-2 text-right font-semibold">${{Number(r.Ocurrencias).toLocaleString()}}</td>
    </tr>
  `).join('');
}}
renderTable(TABLE_DATA);

document.getElementById('searchBox').addEventListener('input', (e) => {{
  const q = e.target.value.toLowerCase();
  const filtered = TABLE_DATA.filter(r =>
    String(r.Item_Nbr).toLowerCase().includes(q) ||
    String(r.desc || '').toLowerCase().includes(q) ||
    String(r.categoria || '').toLowerCase().includes(q) ||
    String(r.squad || '').toLowerCase().includes(q)
  );
  renderTable(filtered);
}});

document.getElementById('downloadBtn').addEventListener('click', () => {{
  const headers = ['Item_Nbr', 'desc', 'squad', 'categoria', 'subcategoria', 'marca', 'Ocurrencias'];
  const escape = (v) => `"${{String(v ?? '').replace(/"/g, '""')}}"`;
  const lines = [headers.join(',')].concat(
    CSV_DATA.map(r => headers.map(h => escape(r[h])).join(','))
  );
  const blob = new Blob(["\\ufeff" + lines.join('\\n')], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'adobe_impresiones_item_{kpis["fecha"]}.csv';
  a.click();
  URL.revokeObjectURL(url);
}});

new Chart(document.getElementById('topChart'), {{
  type: 'bar',
  data: {{
    labels: {chart_labels},
    datasets: [{{
      label: 'Ocurrencias',
      data: {chart_values},
      backgroundColor: '#004B8D',
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ beginAtZero: true }} }}
  }}
}});
</script>
</body>
</html>
"""


def main() -> None:
    df = load_data()
    fecha = df["Fecha"].iloc[0]
    kpis = build_kpis(df, fecha)
    html = build_html(df, kpis)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"[OK] Tablero generado: {OUT_HTML}")
    print(f"     Tamano: {OUT_HTML.stat().st_size / 1024:.1f} KB")
    print(f"     KPIs: {kpis}")


if __name__ == "__main__":
    main()

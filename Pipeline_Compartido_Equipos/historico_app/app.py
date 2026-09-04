# -*- coding: utf-8 -*-
"""Mini-app FastAPI -- Historico MENSUAL 2025 completo + YTD 2026,
compartida entre TODO el negocio (6 equipos E-Catman + Abarrotes + 5
categorias huerfanas -- 76 en total, selector de area en el dropdown,
un solo servidor -- no N apps separadas). Incluye tabla de metricas
(precio/costo/margen/CR YoY/MoM/share .com-piso) por mes.

Correr:
    .venv\\Scripts\\python.exe -m uvicorn app:app --reload --port 8421
Luego abrir http://127.0.0.1:8421
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import db

APP_DIR = Path(__file__).parent
app = FastAPI(title="Historico Mensual 2025+2026 -- Todo el Negocio E-Catman")


@app.get("/", response_class=HTMLResponse)
def index():
    return (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/api/teams")
def teams():
    return db.get_teams()


@app.get("/api/meta")
def meta():
    return {"n_months_2026": db.n_months_2026()}


@app.get("/api/entities")
def entities(team: str, level: str, cat_filter: int | None = None,
             subcat_filter: int | None = None, search: str | None = None):
    return db.get_entities(team, level, cat_filter, subcat_filter, search)


@app.get("/api/series")
def series(team: str, level: str, keys: str, metric: str = "pesos", canal: str = "total"):
    key_list = [k for k in keys.split(",") if k]
    return db.get_series(team, level, key_list, metric, canal)


@app.get("/api/metrics_table")
def metrics_table(team: str, level: str, keys: str):
    """Tabla de metricas mensuales (precio/costo/margen/CR YoY/MoM/share
    .com-piso) con YTD 2026 + LY 2025 completo lado a lado. Grano: el
    mismo nivel elegido (categoria/subcategoria/item), agregando todos
    los clubs -- ver db.get_metrics_table()."""
    key_list = [k for k in keys.split(",") if k]
    return db.get_metrics_table(team, level, key_list)


@app.get("/api/tienda_item")
def tienda_item(item_nbr: int):
    """Nivel Tienda-Item -- consulta EN VIVO a BigQuery (1 item a la
    vez), no sale del parquet pre-pulled. Tarda unos segundos porque es
    un query real, no una lectura local -- avisar al usuario en el UI."""
    return db.get_tienda_item_clubs(item_nbr)


app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

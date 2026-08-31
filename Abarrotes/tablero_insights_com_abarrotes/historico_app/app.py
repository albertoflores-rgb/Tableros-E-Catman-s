# -*- coding: utf-8 -*-
"""Mini-app FastAPI -- Historico Diario 2026 con crecimiento TY vs LY,
4 niveles de agregacion (Categoria, Subcategoria, Item, Tienda-Item).

Correr:
    .venv\\Scripts\\python.exe -m uvicorn app:app --reload --port 8420
Luego abrir http://127.0.0.1:8420
"""
from __future__ import annotations
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import db

APP_DIR = Path(__file__).parent
app = FastAPI(title="Historico Diario 2026 -- Abarrotes")


@app.get("/", response_class=HTMLResponse)
def index():
    return (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/api/meta")
def meta():
    return {"n_days": db.n_days()}


@app.get("/api/entities")
def entities(level: str, cat_filter: int | None = None, subcat_filter: int | None = None,
             search: str | None = None, item_filter: int | None = None):
    return db.get_entities(level, cat_filter, subcat_filter, search, item_filter)


@app.get("/api/series")
def series(level: str, keys: str, metric: str = "pesos", canal: str = "total"):
    key_list = [k for k in keys.split(",") if k]
    return db.get_series(level, key_list, metric, canal)


app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

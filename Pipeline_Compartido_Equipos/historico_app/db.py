# -*- coding: utf-8 -*-
"""Capa de datos de la mini-app -- variante MENSUAL multi-equipo.

Dos fuentes de datos, a proposito distintas:
  1. Parquet pre-pulled (historico_mensual_combined.parquet) -- grano
     Anio x Mes x Item (SIN club), las 72 categorias de los 6 equipos
     E-Catman + Abarrotes (agregado 03-sep-2026 como una 'area' mas del
     selector, ver AREAS abajo -- NO se toco teams_config.TEAMS).
     Cubre los niveles Categoria / Subcategoria / Item.
  2. Query EN VIVO a BigQuery (query_item_club_mensual_template.sql)
     -- SOLO para el nivel Tienda-Item, 1 item a la vez, bajo demanda.
     Un intento anterior metio el nivel Club en el pull masivo y el
     dataframe resultante (66 categorias x 20 meses x ~186 clubs x
     items) crecio a varios GB y casi tumba la maquina por falta de
     RAM (visto en vivo 01-sep-2026) -- por eso Tienda-Item se resuelve
     en vivo, no desde el parquet.

teams_config.py sigue siendo la UNICA fuente de verdad de que
categorias le tocan a cada equipo (y de ABARROTES_CAT_NBRS) -- no se
duplica esa lista aqui, solo se combina en el dict local AREAS.
"""
from __future__ import annotations
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb
from google.cloud import bigquery

APP_DIR = Path(__file__).parent
CATMAN_DIR = APP_DIR.parent
sys.path.insert(0, str(CATMAN_DIR))

from teams_config import TEAMS, ABARROTES_CAT_NBRS, all_cat_nbrs_universe  # noqa: E402

# "Areas" que puede elegir el usuario en el selector de esta mini-app --
# los 6 equipos de teams_config.TEAMS SIN modificarlos (no se muta ese
# dict -- lo usa tambien el pipeline de produccion de los tableros
# estaticos, run_team_pipeline.py / run_query_combined.py, y no queremos
# ningun efecto secundario ahi) + una entrada local "abarrotes" que
# reusa ABARROTES_CAT_NBRS (unica fuente de verdad ya existente en
# teams_config.py) para no duplicar la lista de categorias, + una
# entrada "todo_el_negocio" (agregada 03-sep-2026) que junta las 76
# categorias completas (6 equipos + Abarrotes + 5 huerfanas, mismo
# universo que "Total Departamentos") para poder ver/filtrar el
# negocio completo sin tener que sumar areas a mano. A proposito NO se
# agrega a teams_config.TEAMS ni a teams_config.EXTRA_TEAMS -- esos dos
# dicts alimentan run_team_pipeline.py/main.py de W5/W6, y Abarrotes ya
# tiene su propio pipeline (W4) separado a proposito; solo esta
# mini-app de historico MENSUAL necesita verlos como areas mas.
AREAS: dict = {
    "todo_el_negocio": {
        "owner": "Alberto",
        "area": "Todo el Negocio (76 categorias)",
        "cat_nbrs": all_cat_nbrs_universe(),
    },
    **TEAMS,
    "abarrotes": {
        "owner": "Abarrotes",
        "area": "Abarrotes",
        "cat_nbrs": ABARROTES_CAT_NBRS,
    },
}

PROJECT = "wmt-intl-cons-mx-users"
DATE_INI = "2025-01-01"
DATE_FIN = (date.today() - timedelta(days=1)).isoformat()

_con: duckdb.DuckDBPyConnection | None = None
_bq_client: bigquery.Client | None = None
_item_club_template: str | None = None

LEVEL_COL = {
    "categoria": "CAT_NBR",
    "subcategoria": "SUBCAT_NBR",
    "item": "ITEM_NBR",
}
LEVEL_LABEL_COL = {
    "categoria": "CAT_NOMBRE",
    "subcategoria": "SUBCAT_NOMBRE",
    "item": "ITEM_DESC_1",
}


def get_connection() -> duckdb.DuckDBPyConnection:
    global _con
    if _con is None:
        _con = duckdb.connect(database=":memory:")
        parquet_path = (APP_DIR / "historico_mensual_combined.parquet").as_posix()
        _con.execute(f"CREATE VIEW fact AS SELECT * FROM read_parquet('{parquet_path}')")
    return _con


def get_bq_client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=PROJECT)
    return _bq_client


def get_teams() -> list[dict]:
    return [{"key": k, "label": cfg["area"], "owner": cfg["owner"]} for k, cfg in AREAS.items()]


def _team_cat_nbrs(team_key: str) -> list[int]:
    if team_key not in AREAS:
        raise ValueError(f"Equipo desconocido: {team_key}")
    return AREAS[team_key]["cat_nbrs"]


def n_months_2026() -> int:
    con = get_connection()
    r = con.execute("SELECT MAX(Mes) FROM fact WHERE Anio = 2026").fetchone()[0]
    return int(r) if r is not None else 0


def get_entities(team_key: str, level: str, cat_filter: int | None = None,
                  subcat_filter: int | None = None, search: str | None = None,
                  limit: int = 200):
    """Nivel tienda_item NO se resuelve aqui -- ver get_tienda_item_clubs()."""
    con = get_connection()
    team_cats = _team_cat_nbrs(team_key)
    cats_sql = ",".join(str(c) for c in team_cats)  # confiable -- viene de teams_config.py

    key_col = LEVEL_COL[level]
    label_col = LEVEL_LABEL_COL[level]
    where = [f"CAT_NBR IN ({cats_sql})"]
    params: list = []
    if level in ("subcategoria", "item") and cat_filter is not None:
        where.append("CAT_NBR = ?")
        params.append(cat_filter)
    if level == "item" and subcat_filter is not None:
        where.append("SUBCAT_NBR = ?")
        params.append(subcat_filter)
    if level == "item" and search:
        where.append("(ITEM_DESC_1 ILIKE ? OR CAST(ITEM_NBR AS VARCHAR) ILIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    extra_meta = ", CAT_NBR" if level in ("subcategoria", "item") else ""
    sql = f"""
        SELECT {key_col} AS key, ANY_VALUE({label_col}) AS label,
               SUM(Venta_Pesos_Fisico + Venta_Pesos_Com) AS total {extra_meta}
        FROM fact
        WHERE {' AND '.join(where)}
        GROUP BY {key_col} {extra_meta}
        ORDER BY total DESC
        LIMIT {limit}
    """
    rows = con.execute(sql, params).fetchall()
    out = []
    for r in rows:
        e = {"key": str(r[0]), "label": r[1]}
        if extra_meta:
            e["cat_nbr"] = r[3]
        out.append(e)
    return out


def get_series(team_key: str, level: str, keys: list[str], metric: str, canal: str):
    """Series mensuales para Categoria/Subcategoria/Item (parquet local).
    Regresa, para cada key: {label, y2025: [12 meses], y2026: [12 meses,
    con None despues del mes actual], growth: [%YoY por mes], growth_pct:
    %YTD acumulado, total_2026: suma YTD}."""
    con = get_connection()
    team_cats = _team_cat_nbrs(team_key)
    cats_sql = ",".join(str(c) for c in team_cats)
    n_mo = n_months_2026()

    key_col = LEVEL_COL[level]
    label_col = LEVEL_LABEL_COL[level]
    if not keys:
        return {}
    placeholders = ", ".join(["?"] * len(keys))
    group_key_expr = f"CAST({key_col} AS VARCHAR)"
    label_expr = f"ANY_VALUE({label_col})"

    sql = f"""
        SELECT {group_key_expr} AS gkey, Anio, Mes, {label_expr} AS label,
               SUM(Venta_Pzas_Fisico) AS pzas_fisico, SUM(Venta_Pesos_Fisico) AS pesos_fisico,
               SUM(Venta_Pzas_Com) AS pzas_com, SUM(Venta_Pesos_Com) AS pesos_com
        FROM fact
        WHERE CAT_NBR IN ({cats_sql}) AND {key_col} IN ({placeholders}) AND Anio IN (2025, 2026)
        GROUP BY gkey, Anio, Mes
    """
    rows = con.execute(sql, keys).fetchall()
    return _rows_to_series(rows, n_mo, metric, canal)


MONTH_LABELS_ES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def _safe_div(num: float | None, den: float | None) -> float | None:
    """a/b redondeado a 2 decimales, o None si b es 0/None -- evita
    ZeroDivisionError repartido por todo el archivo (DRY)."""
    if not den:
        return None
    return round(num / den, 2) if num is not None else None


def _pct_change(new: float | None, old: float | None) -> float | None:
    """% de cambio (new vs old) *100, o None si old es 0/None/negativo."""
    if not old:
        return None
    return round((new - old) / old * 100, 2)


def get_metrics_table(team_key: str, level: str, keys: list[str]):
    """Tabla de metricas de negocio a corte MENSUAL, con YTD 2026 y LY
    2025 completo lado a lado para el comparable -- construida 'a
    generales de cada item' (agregando todos los clubs, igual que el
    resto de esta mini-app). Para cada key en `keys` regresa 12 filas
    (Ene..Dic) con, en este orden (pedido explicito de Alberto
    03-sep-2026): Venta $ LY/TY, Venta Piezas LY/TY, CR% YoY, Tendencia
    MoM (encadenada Dic-2025 -> Ene-2026), Utilidad (Margen unitario TY
    x Piezas TY), Margen TY (precio - costo, unitario), Precio
    Promedio LY/TY, Costo Promedio (referencia snapshot -- ver
    cte_costo_item en el .sql) y Share .com TY. Tambien regresa un
    resumen YTD 2026 y Total 2025.

    Nota de diseño (DRY): el Precio Promedio se deriva de las ventas
    reales del mes ($ / piezas) -- varia mes a mes de verdad, a
    diferencia del Costo Promedio que es un snapshot constante (no hay
    historia de costo por mes en la fuente, ver nota en el .sql).
    """
    con = get_connection()
    team_cats = _team_cat_nbrs(team_key)
    cats_sql = ",".join(str(c) for c in team_cats)
    n_mo = n_months_2026()
    if not keys:
        return {}

    key_col = LEVEL_COL[level]
    label_col = LEVEL_LABEL_COL[level]
    placeholders = ", ".join(["?"] * len(keys))

    sales_sql = f"""
        SELECT CAST({key_col} AS VARCHAR) AS gkey, Anio, Mes, ANY_VALUE({label_col}) AS label,
               SUM(Venta_Pzas_Fisico) AS pzas_fisico, SUM(Venta_Pesos_Fisico) AS pesos_fisico,
               SUM(Venta_Pzas_Com) AS pzas_com, SUM(Venta_Pesos_Com) AS pesos_com
        FROM fact
        WHERE CAT_NBR IN ({cats_sql}) AND {key_col} IN ({placeholders}) AND Anio IN (2025, 2026)
        GROUP BY gkey, Anio, Mes
    """
    sales_rows = con.execute(sales_sql, keys).fetchall()

    # Costo/Precio snapshot ponderado por volumen de piezas del periodo --
    # constante por item, pero al agregar a categoria/subcategoria se
    # pondera por venta real en vez de un simple promedio simple.
    cost_sql = f"""
        SELECT gkey,
               SUM(Costo_Unit_Snapshot * w) / NULLIF(SUM(w), 0) AS costo_prom
        FROM (
            SELECT CAST({key_col} AS VARCHAR) AS gkey, ITEM_NBR,
                   ANY_VALUE(Costo_Unit_Snapshot) AS Costo_Unit_Snapshot,
                   SUM(Venta_Pzas_Fisico + Venta_Pzas_Com) AS w
            FROM fact
            WHERE CAT_NBR IN ({cats_sql}) AND {key_col} IN ({placeholders}) AND Anio IN (2025, 2026)
            GROUP BY gkey, ITEM_NBR
        )
        GROUP BY gkey
    """
    cost_by_key = dict(con.execute(cost_sql, keys).fetchall())

    # Reindexa ventas a {gkey: {(anio, mes): (pzas_tot, pesos_tot, pesos_com, pesos_fisico)}}
    by_key: dict = {}
    for gkey, anio, mes, label, pzas_f, pesos_f, pzas_c, pesos_c in sales_rows:
        d = by_key.setdefault(gkey, {"label": label, "cells": {}})
        pzas_tot = float(pzas_f or 0) + float(pzas_c or 0)
        pesos_tot = float(pesos_f or 0) + float(pesos_c or 0)
        d["cells"][(anio, mes)] = {
            "pzas": pzas_tot, "pesos": pesos_tot,
            "pesos_com": float(pesos_c or 0), "pesos_fisico": float(pesos_f or 0),
        }

    result: dict = {}
    for gkey, d in by_key.items():
        costo_prom = cost_by_key.get(gkey)
        cells = d["cells"]

        # Serie continua Ene-2025..Dic-2025..Ene-2026..(n_mo)-2026 para MoM encadenado.
        continuous_pesos = [cells.get((2025, m), {}).get("pesos", 0.0) for m in range(1, 13)]
        continuous_pesos += [cells.get((2026, m), {}).get("pesos", 0.0) for m in range(1, n_mo + 1)]
        mom_all = [None] * len(continuous_pesos)
        for i in range(1, len(continuous_pesos)):
            mom_all[i] = _pct_change(continuous_pesos[i], continuous_pesos[i - 1])

        rows = []
        for m in range(1, 13):
            ly = cells.get((2025, m), {"pzas": 0.0, "pesos": 0.0, "pesos_com": 0.0, "pesos_fisico": 0.0})
            ty = cells.get((2026, m)) if m <= n_mo else None

            precio_ly = _safe_div(ly["pesos"], ly["pzas"])
            precio_ty = _safe_div(ty["pesos"], ty["pzas"]) if ty else None

            margen_ty = round(precio_ty - costo_prom, 2) if (precio_ty is not None and costo_prom is not None) else None
            utilidad_ty = round(margen_ty * ty["pzas"], 2) if (margen_ty is not None and ty) else None

            rows.append({
                "mes": m, "mes_label": MONTH_LABELS_ES[m - 1],
                "pesos_ly": round(ly["pesos"], 2), "pesos_ty": round(ty["pesos"], 2) if ty else None,
                "pzas_ly": round(ly["pzas"], 2), "pzas_ty": round(ty["pzas"], 2) if ty else None,
                "cr_yoy": _pct_change(ty["pesos"], ly["pesos"]) if ty else None,
                "mom_ly": mom_all[m - 1],
                "mom_ty": mom_all[12 + m - 1] if m <= n_mo else None,
                "utilidad_ty": utilidad_ty,
                "margen_ty": margen_ty,
                "precio_prom_ly": precio_ly, "precio_prom_ty": precio_ty,
                "costo_prom": round(costo_prom, 2) if costo_prom is not None else None,
                "share_com_ty": round(ty["pesos_com"] / ty["pesos"] * 100, 1) if (ty and ty["pesos"]) else None,
            })

        ytd_pzas_ty = sum(cells.get((2026, m), {}).get("pzas", 0.0) for m in range(1, n_mo + 1))
        ytd_pesos_ty = sum(cells.get((2026, m), {}).get("pesos", 0.0) for m in range(1, n_mo + 1))
        ytd_pesos_com_ty = sum(cells.get((2026, m), {}).get("pesos_com", 0.0) for m in range(1, n_mo + 1))
        ytd_pesos_ly = sum(cells.get((2025, m), {}).get("pesos", 0.0) for m in range(1, n_mo + 1))
        ytd_pzas_ly = sum(cells.get((2025, m), {}).get("pzas", 0.0) for m in range(1, n_mo + 1))
        total_pesos_ly = sum(cells.get((2025, m), {}).get("pesos", 0.0) for m in range(1, 13))
        total_pzas_ly = sum(cells.get((2025, m), {}).get("pzas", 0.0) for m in range(1, 13))

        precio_ytd = _safe_div(ytd_pesos_ty, ytd_pzas_ty)
        margen_ytd = round(precio_ytd - costo_prom, 2) if (precio_ytd is not None and costo_prom is not None) else None
        utilidad_ytd = round(margen_ytd * ytd_pzas_ty, 2) if margen_ytd is not None else None
        precio_total_ly = _safe_div(total_pesos_ly, total_pzas_ly)
        margen_total_ly = round(precio_total_ly - costo_prom, 2) if (precio_total_ly is not None and costo_prom is not None) else None

        result[gkey] = {
            "label": d["label"],
            "rows": rows,
            "ytd_2026": {
                "pesos": round(ytd_pesos_ty, 2), "pzas": round(ytd_pzas_ty, 2),
                "precio_prom": precio_ytd, "costo_prom": round(costo_prom, 2) if costo_prom is not None else None,
                "margen": margen_ytd, "utilidad": utilidad_ytd,
                "cr_yoy": _pct_change(ytd_pesos_ty, ytd_pesos_ly),
                "share_com": round(ytd_pesos_com_ty / ytd_pesos_ty * 100, 1) if ytd_pesos_ty else None,
            },
            "total_2025": {
                "pesos": round(total_pesos_ly, 2), "pzas": round(total_pzas_ly, 2),
                "precio_prom": precio_total_ly, "costo_prom": round(costo_prom, 2) if costo_prom is not None else None,
                "margen": margen_total_ly,
            },
        }

    return result


def _rows_to_series(rows, n_mo: int, metric: str, canal: str) -> dict:
    metric_col = {
        ("pzas", "fisico"): 4, ("pesos", "fisico"): 5,
        ("pzas", "com"): 6, ("pesos", "com"): 7,
    }
    result: dict = {}
    for r in rows:
        gkey, anio, mes, label = r[0], r[1], r[2], r[3]
        if gkey not in result:
            result[gkey] = {"label": label, "y2025": [0.0] * 12, "y2026": [None] * 12}
        if canal == "total":
            val = (r[metric_col[(metric, "fisico")]] or 0) + (r[metric_col[(metric, "com")]] or 0)
        else:
            val = r[metric_col[(metric, canal)]] or 0
        bucket = "y2025" if anio == 2025 else "y2026"
        idx = mes - 1
        if bucket == "y2026" and result[gkey][bucket][idx] is None:
            result[gkey][bucket][idx] = 0.0
        result[gkey][bucket][idx] = round((result[gkey][bucket][idx] or 0.0) + float(val), 2)

    for gkey, d in result.items():
        for i in range(n_mo, 12):
            d["y2026"][i] = None

        growth = [None] * 12
        for i in range(n_mo):
            ly = d["y2025"][i]
            ty = d["y2026"][i] or 0.0
            growth[i] = round((ty - ly) / ly * 100, 2) if ly else None
        d["growth"] = growth

        sum_ty = sum(v for v in d["y2026"][:n_mo] if v is not None)
        sum_ly_ytd = sum(d["y2025"][:n_mo])
        d["growth_pct"] = ((sum_ty - sum_ly_ytd) / sum_ly_ytd * 100) if sum_ly_ytd else None
        d["total_2026"] = round(sum_ty, 2)
        d["total_2025"] = round(sum(d["y2025"]), 2)

    return result


# ---------------------------------------------------------------------
# Nivel Tienda-Item -- EN VIVO, 1 item a la vez, no sale del parquet.
# ---------------------------------------------------------------------

def _load_item_club_template() -> str:
    global _item_club_template
    if _item_club_template is None:
        _item_club_template = (APP_DIR / "query_item_club_mensual_template.sql").read_text(encoding="utf-8")
    return _item_club_template


def get_tienda_item_clubs(item_nbr: int):
    """Corre el query en vivo para UN item y regresa clubs + su serie ya
    calculada -- se hace en una sola llamada (a diferencia de Abarrotes,
    que separa get_entities/get_series para este nivel) porque aqui cada
    click SI cuesta un query real a BQ, mejor no duplicarlo."""
    template = _load_item_club_template()
    sql = (template
           .replace("{DATE_INI}", DATE_INI)
           .replace("{DATE_FIN}", DATE_FIN)
           .replace("{ITEM_NBR}", str(item_nbr)))
    client = get_bq_client()
    df = client.query(sql, project=PROJECT).to_dataframe()

    if df.empty:
        return {"clubs": [], "series": {}}

    n_mo = n_months_2026()
    rows = [
        (str(int(r.CLUB_NBR)), int(r.Anio), int(r.Mes), r.CLUB_NAME or f"Club {int(r.CLUB_NBR)}",
         r.Venta_Pzas_Fisico, r.Venta_Pesos_Fisico, r.Venta_Pzas_Com, r.Venta_Pesos_Com)
        for r in df.itertuples(index=False)
    ]
    totals_by_club: dict = {}
    for gkey, anio, mes, label, *_ in rows:
        totals_by_club.setdefault(gkey, {"label": label, "total": 0.0})
    for gkey, anio, mes, label, pzas_f, pesos_f, pzas_c, pesos_c in rows:
        totals_by_club[gkey]["total"] += float(pesos_f or 0) + float(pesos_c or 0)

    clubs = sorted(
        [{"key": k, "label": v["label"]} for k, v in totals_by_club.items()],
        key=lambda c: -totals_by_club[c["key"]]["total"],
    )

    series_pesos_total = _rows_to_series(rows, n_mo, "pesos", "total")
    series_pesos_fisico = _rows_to_series(rows, n_mo, "pesos", "fisico")
    series_pesos_com = _rows_to_series(rows, n_mo, "pesos", "com")
    series_pzas_total = _rows_to_series(rows, n_mo, "pzas", "total")
    series_pzas_fisico = _rows_to_series(rows, n_mo, "pzas", "fisico")
    series_pzas_com = _rows_to_series(rows, n_mo, "pzas", "com")

    by_metric_canal = {
        ("pesos", "total"): series_pesos_total, ("pesos", "fisico"): series_pesos_fisico,
        ("pesos", "com"): series_pesos_com, ("pzas", "total"): series_pzas_total,
        ("pzas", "fisico"): series_pzas_fisico, ("pzas", "com"): series_pzas_com,
    }
    return {"clubs": clubs, "series": {f"{m}|{c}": s for (m, c), s in by_metric_canal.items()}}

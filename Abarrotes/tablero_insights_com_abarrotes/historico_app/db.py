# -*- coding: utf-8 -*-
"""Capa de datos de la mini-app: una sola conexion DuckDB en memoria que
lee ty.parquet / ly.parquet directo (sin ETL de carga -- DuckDB puede
consultar Parquet tal cual) y expone 2 funciones genericas que cubren
los 4 niveles (categoria, subcategoria, item, tienda_item) sin duplicar
logica por nivel (DRY): get_entities() para poblar selectores/buscador,
get_series() para las series diarias TY/LY + crecimiento.
"""
from __future__ import annotations
import duckdb
from pathlib import Path

APP_DIR = Path(__file__).parent

_con: duckdb.DuckDBPyConnection | None = None

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
        ty_path = (APP_DIR / "ty.parquet").as_posix()
        ly_path = (APP_DIR / "ly.parquet").as_posix()
        _con.execute(f"""
            CREATE VIEW fact AS
            SELECT * FROM read_parquet('{ty_path}')
            UNION ALL
            SELECT * FROM read_parquet('{ly_path}')
        """)
    return _con


def n_days() -> int:
    con = get_connection()
    return int(con.execute("SELECT MAX(Day_Offset) + 1 FROM fact WHERE Periodo = 'TY'").fetchone()[0])


def get_entities(level: str, cat_filter: int | None = None, subcat_filter: int | None = None,
                  search: str | None = None, item_filter: int | None = None, limit: int = 200):
    con = get_connection()

    if level == "tienda_item":
        if item_filter is None:
            return []
        rows = con.execute("""
            SELECT CLUB_NBR AS key, ANY_VALUE(CLUB_NAME) AS label, SUM(Venta_Pesos_Fisico + Venta_Pesos_Com) AS total
            FROM fact
            WHERE Periodo = 'TY' AND ITEM_NBR = ?
            GROUP BY CLUB_NBR
            ORDER BY total DESC
        """, [item_filter]).fetchall()
        return [{"key": str(r[0]), "label": r[1] or f"Club {r[0]}", "cat_nbr": None} for r in rows]

    key_col = LEVEL_COL[level]
    label_col = LEVEL_LABEL_COL[level]
    where = ["Periodo = 'TY'"]
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


def get_series(level: str, keys: list[str], metric: str, canal: str):
    """Regresa, para cada key: {label, ty: [...N dias...], ly: [...N dias...],
    growth_pct: float|None} -- alineado por Day_Offset (0..N-1)."""
    con = get_connection()
    n = n_days()

    if level == "tienda_item":
        pairs = [tuple(k.split("|")) for k in keys]  # (item_nbr, club_nbr)
        if not pairs:
            return {}
        conds = " OR ".join(["(ITEM_NBR = ? AND CLUB_NBR = ?)"] * len(pairs))
        params: list = [v for pair in pairs for v in pair]
        group_key_expr = "CAST(ITEM_NBR AS VARCHAR) || '|' || CAST(CLUB_NBR AS VARCHAR)"
        label_expr = "ANY_VALUE(ITEM_DESC_1) || ' @ ' || ANY_VALUE(CLUB_NAME)"
    else:
        key_col = LEVEL_COL[level]
        label_col = LEVEL_LABEL_COL[level]
        if not keys:
            return {}
        placeholders = ", ".join(["?"] * len(keys))
        conds = f"{key_col} IN ({placeholders})"
        params = keys
        group_key_expr = f"CAST({key_col} AS VARCHAR)"
        label_expr = f"ANY_VALUE({label_col})"

    sql = f"""
        SELECT {group_key_expr} AS gkey, Periodo, Day_Offset, {label_expr} AS label,
               SUM(Venta_Pzas_Fisico) AS pzas_fisico, SUM(Venta_Pesos_Fisico) AS pesos_fisico,
               SUM(Venta_Pzas_Com) AS pzas_com, SUM(Venta_Pesos_Com) AS pesos_com
        FROM fact
        WHERE ({conds}) AND Day_Offset BETWEEN 0 AND {n - 1}
        GROUP BY gkey, Periodo, Day_Offset
    """
    rows = con.execute(sql, params).fetchall()

    metric_col = {
        ("pzas", "fisico"): 4, ("pesos", "fisico"): 5,
        ("pzas", "com"): 6, ("pesos", "com"): 7,
    }
    result: dict = {}
    for r in rows:
        gkey, periodo, day_off, label = r[0], r[1], r[2], r[3]
        if gkey not in result:
            result[gkey] = {
                "label": label,
                "ty": [0.0] * n, "ly": [0.0] * n,
            }
        if canal == "total":
            val = (r[metric_col[(metric, "fisico")]] or 0) + (r[metric_col[(metric, "com")]] or 0)
        else:
            val = r[metric_col[(metric, canal)]] or 0
        bucket = "ty" if periodo == "TY" else "ly"
        result[gkey][bucket][day_off] = round(float(val), 2)

    for gkey, d in result.items():
        # Crecimiento ACUMULADO dia a dia (no crecimiento diario crudo --
        # ese es muy ruidoso, ej. LY=0 un dia da un pico de %infinito).
        # cum_ty[i]/cum_ly[i] van suavizando el ratio conforme avanza el
        # periodo, que es justo lo que se quiere ver en una tendencia.
        cum_ty, cum_ly, growth = 0.0, 0.0, [None] * n
        for i in range(n):
            cum_ty += d["ty"][i]
            cum_ly += d["ly"][i]
            growth[i] = round((cum_ty - cum_ly) / cum_ly * 100, 2) if cum_ly else None
        sum_ty, sum_ly = sum(d["ty"]), sum(d["ly"])
        d["growth"] = growth
        d["growth_pct"] = ((sum_ty - sum_ly) / sum_ly * 100) if sum_ly else None
        d["total_ty"] = round(sum_ty, 2)
        # OJO: el valor LY crudo NO se expone al frontend (a proposito --
        # solo se usa aqui para calcular growth/growth_pct). Se descarta
        # antes de regresar la respuesta.
        del d["ly"]

    return result

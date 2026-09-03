# -*- coding: utf-8 -*-
"""Config central de las areas de E-Catman -- UN SOLO lugar para ajustar
categorias por equipo.

Por que existe este archivo: antes de esto, cambiar el filtro de una
categoria significaba editar un WHERE hardcoded a la mitad de un .sql
de 500+ lineas (y repetir ese bug-hunt por cada equipo). Ahora:
  - El .sql (`query_item_total_template.sql`) usa un parametro
    `@cat_filter` -- nunca mas se toca el SQL para cambiar categorias.
  - Este archivo es la UNICA fuente de verdad de que categoria le
    pertenece a que equipo.

Para agregar/quitar una categoria de un equipo: edita la lista
`cat_nbrs` de abajo y vuelve a correr `run_query_team.py <team_key>`.
No hace falta tocar nada mas.

OJO -- resuelto (01-sep-2026): la categoria 51 SOLO es de "seasonal".
Se quito de "impulso" por confirmacion directa de Alberto (era un
typo del copy-paste original, no una categoria compartida).
"""

TEAMS = {
    "perecederos": {
        "owner": "Pacheco",
        "area": "Perecederos - Deli Fresh y Congelados",
        "cat_nbrs": [42, 44, 38, 56, 72, 77, 76, 39, 57, 59, 91, 79],
        "github_folder": "Congelados y deli",
    },
    "impulso": {
        "owner": "Kevin",
        "area": "Impulso",
        "cat_nbrs": [1, 19, 28, 40, 48, 52, 55, 58],
        "github_folder": "Impulso",
    },
    "seasonal": {
        "owner": "Nat / Dani",
        "area": "Seasonal",
        "cat_nbrs": [7, 9, 10, 69, 12, 11, 16, 14, 18, 17, 51, 78, 85, 83, 92, 50, 94],
        "github_folder": "Temporada",
    },
    "apparel": {
        "owner": "Dani",
        "area": "Apparel",
        "cat_nbrs": [21, 22, 23, 26, 33, 34, 36, 63, 66, 67],
        "github_folder": "Ropa",
    },
    "tecnologia": {
        "owner": "Valeria",
        "area": "Tecnologia",
        "cat_nbrs": [3, 5, 6, 15, 29, 31, 32, 60, 61, 71, 81, 98],
        "github_folder": "Tecnologia",
    },
    "salud_bienestar": {
        "owner": "Estef",
        "area": "Salud y Bienestar",
        "cat_nbrs": [2, 4, 8, 13, 27, 47, 54],
        "github_folder": "Salud y Bienestar",
    },
}


def all_cat_nbrs_used_more_than_once() -> dict:
    """Utilidad de diagnostico: regresa {cat_nbr: [team_keys]} para
    cualquier categoria que aparezca en mas de un equipo -- para
    detectar typos de copy-paste como el de la cat 51 arriba."""
    seen: dict[int, list[str]] = {}
    for team_key, cfg in TEAMS.items():
        for cat in cfg["cat_nbrs"]:
            seen.setdefault(cat, []).append(team_key)
    return {cat: teams for cat, teams in seen.items() if len(teams) > 1}


def all_cat_nbrs_combined() -> list:
    """Union de TODAS las categorias de TODOS los equipos, sin duplicados,
    ordenada. Usada por run_query_combined.py para jalar los 6 equipos en
    UNA sola pasada de BigQuery en vez de 6 -- el costo de este query esta
    dominado por el escaneo completo de las tablas base (SKU_DLY_POS,
    Sams_Ventas, MDSE_INVENTORY), NO por cuantas categorias traiga el
    filtro, asi que 6 queries separados = 6x el costo de 1 query combinado.
    Ver README.md, seccion 'Optimizacion de costo'."""
    combined = set()
    for cfg in TEAMS.values():
        combined.update(cfg["cat_nbrs"])
    return sorted(combined)


# ================================================================
# Fase 2 -- Tablero "Total Departamentos" (03-sep-2026)
# ================================================================
# Categorias de Abarrotes -- copiadas TAL CUAL del WHERE de
# tablero_insights_com_abarrotes/query_item_total_abarrotes.sql (esa
# query se deja intacta, esto es solo para poder incluir su universo
# en el filtro combinado de "Total Departamentos"). Si algun dia
# Abarrotes cambia sus categorias, actualizar aqui a mano tambien --
# no hay forma de importar directo de un .sql sin duplicar parsing.
ABARROTES_CAT_NBRS = [41, 43, 46, 49, 53, 68]

# Categorias "huerfanas": SI existen en el catalogo real (confirmado
# 03-sep-2026 contra la tabla dimension autoritativa
# `wmt-edw-sandbox.Black_Bird.Catalogo_Cat_Compradores` -- la MISMA
# tabla que el JOIN de Cat_Desc en query_item_total_template.sql,
# alias `e`, ON b.CATEGORY_NBR = e.DEPT_NBR) pero NO le pertenecen a
# ninguno de los 6 equipos de E-Catman ni a Abarrotes. Se descubrieron
# comparando el output de esa tabla dimension (76 categorias validas
# con Cat_Desc) contra la union de teams_config + Abarrotes (72) --
# la diferencia son estas 5 (mas la categoria 36 en teams_config.apparel
# que NO tiene match en la dimension -- parece inactiva/obsoleta, se
# deja tal cual en teams_config.apparel sin tocar, es pre-existente).
# Sin esto el tablero "Total Departamentos" estaria incompleto contra
# el universo real de categorias con venta/inventario.
ORPHAN_CAT_NBRS = [
    45,  # TABACO -- division IMPULSO, no esta en teams_config['impulso']
    62,  # AZUCAR -- division ABARROTES, no esta en query_item_total_abarrotes.sql
    70,  # LIBROS -- division TECNOLOGIA, no esta en teams_config['tecnologia']
    73,  # BULK DELI -- division REFRIGERADOS..., no esta en teams_config['perecederos']
    88,  # JOYERIA -- division ROPA, no esta en teams_config['apparel']
]


def all_cat_nbrs_universe() -> list:
    """Union de TODO el universo de categorias con venta/inventario real:
    los 6 equipos de E-Catman + Abarrotes + las 5 'huerfanas'. Usada por
    run_query_combined.py para que UNA sola pasada de BigQuery alimente
    tanto los 6 tableros de equipo como el 7mo tablero 'Total
    Departamentos' -- confirmado con `bq --dry_run` (03-sep-2026) que
    esto cuesta EXACTAMENTE LO MISMO (~18GB) que filtrar solo 66
    categorias, por la misma razon de siempre: el costo lo domina el
    escaneo completo de las tablas base, no el tamano del filtro."""
    universe = set(all_cat_nbrs_combined())
    universe.update(ABARROTES_CAT_NBRS)
    universe.update(ORPHAN_CAT_NBRS)
    return sorted(universe)


# "Equipos" adicionales que reusan el mismo pipeline generico
# (pipeline/run_team_pipeline.py, build_merge.py, finalize_*.py,
# build_dashboard.py) pero que NO son uno de los 6 equipos reales de
# E-Catman -- viven en un dict aparte para que:
#   1. `run_team_pipeline.py --all` y el `main.py` de W5 SIGAN
#      procesando solo los 6 equipos reales (no se altera la rutina
#      diaria de las 7am con esto).
#   2. `pipeline/_common.py::get_team_cfg()` los reconozca igual que a
#      un equipo real cuando se les llama por su team_key explicito
#      (ej. `run_team_pipeline.py total_departamentos`).
EXTRA_TEAMS = {
    "total_departamentos": {
        "owner": "Alberto",
        "area": "Total Departamentos",
        "cat_nbrs": all_cat_nbrs_universe(),
        "github_folder": "Total_Departamentos",
        # Bandera leida por finalize_sept.py: esta vista consolidada no
        # tiene una sola hoja de FCST propia en el Excel de Alberto (cada
        # equipo tiene la suya) -- se omite la pestana 3 con un aviso
        # claro en vez de intentar adivinar/sumar FCSTs de hojas distintas.
        "no_fcst": True,
        # Bandera informativa (no leida por codigo todavia): DSV queda
        # fuera de alcance para v1 de este tablero -- ver merge_dsv.py,
        # que solo corre para tecnologia/seasonal/apparel via
        # TEAMS_WITH_DSV, no via este flag.
        "no_dsv": True,
    },
}


def get_any_team_cfg(team_key: str) -> dict:
    """Como TEAMS[team_key], pero tambien busca en EXTRA_TEAMS -- usada
    por pipeline/_common.py::get_team_cfg() para que el pipeline
    generico funcione igual para los 6 equipos reales y para
    'total_departamentos' sin duplicar logica."""
    if team_key in TEAMS:
        return TEAMS[team_key]
    if team_key in EXTRA_TEAMS:
        return EXTRA_TEAMS[team_key]
    raise KeyError(team_key)


if __name__ == "__main__":
    dupes = all_cat_nbrs_used_more_than_once()
    if dupes:
        print("Categorias que aparecen en mas de un equipo:")
        for cat, teams in dupes.items():
            print(f"  Cat_Nbr {cat}: {teams}")
    else:
        print("Sin categorias duplicadas entre equipos.")

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


if __name__ == "__main__":
    dupes = all_cat_nbrs_used_more_than_once()
    if dupes:
        print("Categorias que aparecen en mas de un equipo:")
        for cat, teams in dupes.items():
            print(f"  Cat_Nbr {cat}: {teams}")
    else:
        print("Sin categorias duplicadas entre equipos.")

# -*- coding: utf-8 -*-
"""validate_integrity.py -- chequeo de integridad GENERICO y NO
BLOQUEANTE: compara la venta .com de AYER contra el promedio diario de
los 7 dias anteriores (excluyendo ayer), para todo el universo de
categorias de E-Catman + Abarrotes. Si ayer cae por debajo del 30% de
ese promedio, emite una alerta clara -- pero NUNCA truena el pipeline
que lo llama (por diseno: este script SIEMPRE termina con exit code 0,
incluso si el query de BigQuery falla).

Por que existe esto: el 03-sep-2026 se diagnostico que la venta .com de
Sept 1-2 se veia "muy baja" en los 6 tableros porque la tabla fuente
`Sams_Ventas` tenia LATENCIA de asentamiento (no un bug de query) -- ver
kennel_recall "DIAGNOSTICO 03-sep-2026". Este chequeo es la deteccion
temprana generica para que la proxima vez que pase algo asi (latencia,
corte de datos, o una caida real de negocio) se note el mismo dia en
vez de hasta que alguien lo reporte.

Costo de este query: BARATO. `Sams_Ventas` esta particionada por dia
(columna `sales_order_detail_order_created_date`, ya tipo DATE) -- pedir
solo los ultimos 8 dias escanea nada mas esas particiones, sin importar
que tan grande sea la tabla completa o el YTD. Esto es INDEPENDIENTE
del query grande de Item Total (query_item_total_template.sql), que
siempre escanea el YTD completo (~18GB) sin importar el rango pedido.

Uso:
    python validate_integrity.py                  # universo completo (6 equipos + Abarrotes + huerfanas)
    python validate_integrity.py --umbral 0.30     # umbral de alerta configurable (default 0.30 = 30%)
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

PROJECT = "wmt-intl-cons-mx-users"
SCRIPT_DIR = Path(__file__).parent
LOG_PATH = SCRIPT_DIR / "integrity_check_log.jsonl"

SQL_TEMPLATE = """
DECLARE fecha_ayer DATE DEFAULT DATE_SUB(CURRENT_DATE('America/Mexico_City'), INTERVAL 1 DAY);
DECLARE fecha_ini  DATE DEFAULT DATE_SUB(fecha_ayer, INTERVAL 7 DAY);  -- ayer-7 .. ayer-1 = baseline (7 dias, SIN incluir ayer)

WITH cte_com_raw AS (
  SELECT
    DATE(s.sales_order_detail_order_created_date)              AS Fecha,
    SAFE_CAST(s.sales_order_detail_item_id_short AS INT64)      AS ITEM_NBR,
    s.sales_order_detail_net_paid_orders_wo_shipping_amount_1   AS Pesos
  FROM `wmt-mx-dl-controlledmgzn-prod.ecom.Sams_Ventas` AS s
  WHERE
    DATE(s.sales_order_detail_order_created_date) BETWEEN fecha_ini AND fecha_ayer
    AND s.sales_order_detail_commercial_sale_qty_base > 0
    AND s.sales_order_detail_item_id_short IS NOT NULL
),
cte_filtrado AS (
  SELECT r.Fecha, r.Pesos
  FROM cte_com_raw AS r
  INNER JOIN `wmt-edw-prod.MX_WC_VM.ITEM_DESC` AS bd ON r.ITEM_NBR = bd.Old_NBR
  WHERE {cat_where}
)
SELECT Fecha, SUM(Pesos) AS Venta_Pesos
FROM cte_filtrado
GROUP BY Fecha
ORDER BY Fecha
"""


def build_sql(cat_nbrs):
    if cat_nbrs:
        cat_where = "bd.CATEGORY_NBR IN UNNEST(@cat_filter)"
    else:
        cat_where = "TRUE"  # sin filtro = todo el sitio .com
    return SQL_TEMPLATE.format(cat_where=cat_where)


def check(cat_nbrs=None, label="Total Departamentos (universo completo)", umbral=0.30) -> dict:
    """Corre el chequeo. SIEMPRE regresa un dict (nunca levanta) -- el
    llamador decide si loguear/imprimir, pero el proceso de validacion
    en si mismo no debe poder tumbar un pipeline que lo invoque."""
    resultado = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "label": label,
        "ok": None,
        "alerta": False,
        "error": None,
    }
    try:
        from google.cloud import bigquery

        sql = build_sql(cat_nbrs)
        job_config = None
        if cat_nbrs:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ArrayQueryParameter("cat_filter", "INT64", cat_nbrs)]
            )
        client = bigquery.Client(project=PROJECT)
        job = client.query(sql, job_config=job_config, project=PROJECT) if job_config else client.query(sql, project=PROJECT)
        df = job.to_dataframe()

        if df.empty:
            resultado["error"] = "Query no regreso filas (0 dias con venta en el rango) -- no se puede evaluar."
            resultado["ok"] = False
            return resultado

        df = df.sort_values("Fecha")
        ayer = df.iloc[-1]
        baseline = df.iloc[:-1]  # los 7 dias anteriores a ayer

        venta_ayer = float(ayer["Venta_Pesos"])
        promedio_baseline = float(baseline["Venta_Pesos"].mean()) if len(baseline) else None
        ratio = (venta_ayer / promedio_baseline) if promedio_baseline else None

        resultado.update({
            "fecha_ayer": str(ayer["Fecha"]),
            "venta_ayer": round(venta_ayer, 2),
            "promedio_baseline_7d": (round(promedio_baseline, 2) if promedio_baseline is not None else None),
            "dias_baseline": len(baseline),
            "ratio": (round(ratio, 4) if ratio is not None else None),
            "umbral": umbral,
            "bytes_billed": job.total_bytes_billed,
        })

        if ratio is None:
            resultado["error"] = "Baseline de 7 dias vacio o en cero -- no se puede calcular ratio."
            resultado["ok"] = False
        elif ratio < umbral:
            resultado["alerta"] = True
            resultado["ok"] = False
        else:
            resultado["ok"] = True

    except Exception as exc:  # noqa: BLE001 -- a proposito: nunca debe tronar
        resultado["error"] = f"{type(exc).__name__}: {exc}"
        resultado["ok"] = False
        resultado["_traceback"] = traceback.format_exc()

    return resultado


def _print_result(r: dict) -> None:
    print("=" * 60)
    print(f"CHEQUEO DE INTEGRIDAD -- {r['label']}")
    print("=" * 60)
    if r.get("error"):
        print(f"[AVISO] No se pudo completar el chequeo: {r['error']}")
        print("Este chequeo es informativo/NO bloqueante -- el pipeline principal continua normal.")
        return
    print(f"Fecha evaluada (ayer): {r['fecha_ayer']}")
    print(f"Venta .com de ayer:    ${r['venta_ayer']:,.2f}")
    print(f"Promedio 7 dias previos (baseline, {r['dias_baseline']} dias): ${r['promedio_baseline_7d']:,.2f}")
    print(f"Ratio ayer/baseline:   {r['ratio']*100:.1f}%  (umbral de alerta: <{r['umbral']*100:.0f}%)")
    if r["alerta"]:
        print("")
        print("*** ALERTA: la venta .com de ayer cayo por debajo del umbral vs el promedio de los ultimos 7 dias. ***")
        print("*** Esto NO bloquea el pipeline -- pero revisa si es un problema de datos (latencia/corte) o una caida real de negocio antes de dar por buenos los KPIs del dia. ***")
    else:
        print("[OK] Venta de ayer dentro de rango esperado vs el promedio reciente.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--umbral", type=float, default=0.30, help="Umbral de alerta (default 0.30 = 30%%)")
    parser.add_argument("--cats", type=str, default=None, help="Lista de Cat_Nbr separados por coma (default: universo completo)")
    args = parser.parse_args()

    if args.cats:
        cat_nbrs = [int(c.strip()) for c in args.cats.split(",") if c.strip()]
        label = f"Categorias {cat_nbrs}"
    else:
        sys.path.insert(0, str(SCRIPT_DIR))
        from teams_config import all_cat_nbrs_universe
        cat_nbrs = all_cat_nbrs_universe()
        label = "Total Departamentos (universo completo, 6 equipos + Abarrotes + huerfanas)"

    resultado = check(cat_nbrs=cat_nbrs, label=label, umbral=args.umbral)
    _print_result(resultado)

    resultado_log = {k: v for k, v in resultado.items() if k != "_traceback"}
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(resultado_log, ensure_ascii=False) + "\n")

    # A proposito: SIEMPRE exit 0 -- este chequeo es informativo, nunca
    # debe tumbar un pipeline que lo invoque (ni siquiera si hay alerta).
    sys.exit(0)


if __name__ == "__main__":
    main()

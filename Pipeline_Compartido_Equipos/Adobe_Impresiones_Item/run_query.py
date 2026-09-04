# -*- coding: utf-8 -*-
"""Ejecuta query_adobe_impresiones_item.sql para UN dia especifico de
la tabla de eventos de Adobe (sams_mx_csd_adobe_event) y guarda el
resultado crudo en CSV.

Costo real validado (ver Respaldo_Querys/saved_queries/SAMS - Adobe
Impresiones Item (Investigacion) v2.sql): ~11 GB por dia procesado.

OJO -- por que la fecha esta hardcodeada y NO se autodetecta con un
"SELECT MAX(ds)": se intento (04-sep-2026) y la query de descubrimiento
se quedo corriendo mas de 100 segundos sin responder. La tabla fuente
es una VIEW sobre una tabla EXTERNA (ORC) -- a diferencia de una tabla
nativa de BigQuery, un filtro por `ds` (o un MAX(ds)) en una tabla
externa NO siempre goza de poda de particion "gratis": si el WHERE
tambien filtra por una columna que no es la de particion
(`op_cmpny_cd`), BigQuery puede terminar leyendo de mas. Se aborto esa
corrida para no gastar de mas / colgar el pipeline. Conclusion: usar
SIEMPRE una fecha fija conocida (la ya validada, o una nueva
confirmada a mano por Alberto) en vez de autodescubrir la fecha mas
reciente.

Uso:
    python run_query.py                  # usa FECHA_REPORTE de abajo
    python run_query.py 2026-09-03       # o pasa una fecha por CLI
"""
from __future__ import annotations
import sys
from pathlib import Path
from google.cloud import bigquery

PROJECT = "wmt-intl-cons-mx-users"  # proyecto de billing (igual que el resto del repo)
SQL_PATH = Path(__file__).parent / "query_adobe_impresiones_item.sql"
OUT_CSV = Path(__file__).parent / "raw_adobe_impresiones_item.csv"

# Fecha ya validada en la investigacion v2 (02-sep-2026, ~11 GB,
# 12,339 items, 10,332,116 ocurrencias). Cambiar aqui o por CLI arg
# cuando se quiera un dia mas reciente -- confirmar antes con Alberto
# que ese `ds` ya esta poblado, en vez de autodetectarlo (ver docstring).
FECHA_REPORTE = "2026-09-02"


def run(fecha_reporte: str) -> None:
    client = bigquery.Client(project=PROJECT)
    sql = SQL_PATH.read_text(encoding="utf-8")
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("fecha_reporte", "DATE", fecha_reporte),
        ]
    )
    print(f"Ejecutando query para {fecha_reporte} (costo estimado ~11 GB)...")
    job = client.query(sql, job_config=job_config, project=PROJECT)
    df = job.to_dataframe()

    bytes_billed = getattr(job, "total_bytes_billed", None)
    if bytes_billed is not None:
        print(f"Bytes facturados por BigQuery: {bytes_billed / (1024**3):.2f} GB")

    print("Filas (Item_Nbr distintos con impresiones ese dia):", len(df))
    print("Suma total de Ocurrencias:", int(df["Ocurrencias"].sum()))

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Guardado en {OUT_CSV}")


if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else FECHA_REPORTE
    run(fecha)

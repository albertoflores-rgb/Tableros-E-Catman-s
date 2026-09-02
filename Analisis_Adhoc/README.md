# Análisis Ad-Hoc

Esta carpeta es para queries de análisis puntual (bajo demanda), a
diferencia de `Pipeline_Compartido_Equipos/` y `Abarrotes/`, que son
pipelines automatizados/recurrentes con su propio orquestador.

Un query aquí no corre solo ni tiene tarea programada -- se ejecuta a
mano cuando alguien necesita esa vista específica.

## Contenido

### `Venta_Com_Promociones.sql`
Venta .com (Sam's Club MX, 176 clubs agregados) a nivel **Fecha + Ítem
+ Promoción atómica**, con piezas, pesos, órdenes y número de socios
(membresías únicas) por combinación.

**Hallazgo clave documentado en el propio archivo:** el campo
`sales_order_detail_order_promotion_discount_desc` de
`Sams_Ventas` NO es una promoción única -- es una concatenación con
`/` de todas las promociones que aplicaron juntas a esa línea de
orden, con `"null"`/`"NULL VALUE"` como relleno cuando no aplicó
ninguna en esa posición. El query separa esto con `SPLIT(...,'/')` +
`UNNEST` y descarta los placeholders, dejando ~837 promociones reales
en vez de miles de combinaciones sin sentido.

**Caveat de doble conteo:** si una venta tuvo 2+ promos combinadas,
se cuenta una vez POR CADA promo en `Venta_Pzas_Com`, `Venta_Pesos_Com`,
`Ordenes_Com` y `Numero_Socios_Com`. Sumar estas columnas entre filas
de un mismo ítem/día SIEMPRE da más que la venta real total -- correcto
para comparar promociones entre sí, no para sacar un total general.

**Costo real (rango 2025 completo + 2026 YTD):** ~6.2 GB procesados,
~3.97 millones de filas de salida (grano sin Club -- con Club llega a
~33 millones de filas, invitable). Correr con
`google-cloud-bigquery-storage` instalado en el entorno o la descarga
de millones de filas por REST se cuelga sin avisar.

```bash
# Necesita el mismo acceso a Sams_Ventas que el resto de queries .com
# (ver Pipeline_Compartido_Equipos/README.md, sección de AD groups).
bq query --use_legacy_sql=false < Venta_Com_Promociones.sql
# o, para bajarlo a CSV con Python (recomendado para >100K filas):
# ver catman_equipos/_run_venta_com_promos.py como referencia de patrón
```

# Tableros E-Catman — Insights .com

Tableros de Insights .com (venta física vs .com, movers, FCST y riesgo)
por equipo de E-Catman. Cada carpeta trae un HTML autocontenido — se
abre con doble-click, no requiere servidor ni instalar nada.

**¿Nueva/o por aquí?** Entra a la carpeta de tu equipo y corre el
`DESCARGAR_Y_ABRIR_TABLERO.bat` de adentro (doble-click). Eso es todo.

## Tableros

| Equipo | Carpeta | Owner | Pestañas |
|---|---|---|---|
| **Abarrotes** | [`Abarrotes/`](./Abarrotes/) | — | Resumen · Explorador BQ · Promos Vigentes · Septiembre FCST (+ evento "A la Mexicana") · Histórico Diario |
| **Perecederos / Congelados y Deli** | [`Congelados y deli/`](./Congelados%20y%20deli/) | Pacheco | Resumen · Explorador BQ · Septiembre FCST y Riesgo |
| **Impulso** | [`Impulso/`](./Impulso/) | Kevin | Resumen · Explorador BQ · Septiembre FCST y Riesgo |
| **Seasonal** | [`Temporada/`](./Temporada/) | Nat / Dani | Resumen · Explorador BQ (+DSV) · Septiembre FCST y Riesgo |
| **Apparel** | [`Ropa/`](./Ropa/) | Dani | Resumen · Explorador BQ (+DSV) · Septiembre FCST y Riesgo |
| **Tecnología** | [`Tecnologia/`](./Tecnologia/) | Valeria | Resumen · Explorador BQ (+DSV) · Septiembre FCST y Riesgo |
| **Salud y Bienestar** | [`Salud y Bienestar/`](./Salud%20y%20Bienestar/) | Estef | Resumen · Explorador BQ · Septiembre FCST y Riesgo |

Todos se actualizan automáticamente cada mañana vía Windows Task
Scheduler. "+DSV" = trae cruce de inventario con samsdsv.com
(exclusivo de Mercancías Generales: Tecnología, Seasonal, Apparel).

## Código fuente

- **Abarrotes** tiene su propio pipeline standalone dentro de su
  carpeta (es el más rico: promos, parrilla, histórico, evento AMX).
- Los otros 6 comparten un solo pipeline parametrizado en
  [`Pipeline_Compartido_Equipos/`](./Pipeline_Compartido_Equipos/)
  (DRY — misma lógica de merge/KPIs/FCST, solo cambia el equipo).

## Publicado (Puppy Pages)

Ver el README de cada carpeta para el link publicado de ese tablero
específico.

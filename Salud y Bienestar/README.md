# Salud y Bienestar

Carpeta para tableros, documentos y recursos relacionados con Salud y Bienestar.

## Para usuarios sin conocimientos tecnicos

Descarga y corre **[`DESCARGAR_Y_ABRIR_TABLERO.bat`](./DESCARGAR_Y_ABRIR_TABLERO.bat)**
(boton verde "Code" -> "Download ZIP" en GitHub, extrae, y corre el
.bat que ya viene adentro de esta carpeta). No requiere git, ni
Python, ni instalar nada -- solo doble-click.

Requiere conexion a internet (VPN o Eagle WiFi de Walmart). Para
refrescar a la version mas nueva en el futuro, vuelve a correr el
mismo `.bat`.

## Contenido

### `tablero_insights_com_salud_bienestar/`
Tablero **Insights .com Salud y Bienestar** (categorias 2,4,8,13,27,47,54). Owner: Estef.
HTML estatico de 3 pestanas -- Resumen y Movers · Explorador BQ
· Septiembre FCST y Riesgo -- autocontenido, se abre con doble click,
no requiere servidor.

Se actualiza automaticamente cada manana via Windows Task Scheduler
(`rutinas/W5_Tableros_Equipos_Ecatman/` en el workspace local).

### Fuente / como regenerarlo
El codigo fuente (pipeline Python + queries SQL + plantillas HTML) es
**compartido** entre los 6 equipos de este tipo de tablero -- vive en
[`../Pipeline_Compartido_Equipos/`](../Pipeline_Compartido_Equipos/),
NO duplicado en cada carpeta (evita mantener 6 copias casi-identicas).
Para regenerar este tablero especifico:

```bash
cd Pipeline_Compartido_Equipos/pipeline
python run_team_pipeline.py salud_bienestar
```

Este repo trae el **HTML final ya compilado**, no los CSV/JSON
intermedios (ver `.gitignore` en `Pipeline_Compartido_Equipos/`) --
son cachés regenerables corriendo el pipeline compartido.

## Sin parrilla/promos (a diferencia de Abarrotes)
Este equipo todavia no tiene parrilla 10+1 ni tracker de promos --
las tablas de "movers" son Top 20 por volumen ($), sin curar por
promo. Aviso explicito dentro del tablero.

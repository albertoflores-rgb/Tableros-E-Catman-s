# Abarrotes

Carpeta para tableros, documentos y recursos relacionados con el departamento de Abarrotes.

## Contenido

### `tablero_insights_com_abarrotes/`
Tablero **oficial publicado** de Insights .com Abarrotes (categorías
41·43·46·49·53·68). HTML estático de 5 pestañas (Resumen y Accionables
· Explorador BQ · Promos Vigentes + Mapeo en Sitio · Septiembre FCST y
Riesgo · Histórico Diario 2026), autocontenido -- se abre con doble
click, no requiere servidor.

Se actualiza automáticamente todos los días a las 8:30 AM vía Windows
Task Scheduler (`rutinas/W4_Tablero_Insights_Com_Abarrotes/` en el
workspace local). Publicado en:
https://puppy.walmart.com/sharing/a0f07dn/tablero-insights-com-abarrotes

Este repo trae el **código fuente** (scripts Python + queries SQL +
plantillas HTML) y el **HTML final ya compilado**. No trae los CSV/JSON
intermedios (ver `.gitignore`) -- son cachés regenerables corriendo los
scripts en el orden documentado en su README.

### `tablero_insights_com_abarrotes/historico_app/`
**Prueba/prototipo** -- mini-app FastAPI + DuckDB para el mismo
histórico diario, pero con el nivel **Tienda-Ítem** (Club x Ítem) que
no cupo en el HTML estático por volumen (15.3M filas/año), y con
crecimiento % acumulado vs año anterior en los 4 niveles. Requiere
correr un servidor local (`uvicorn app:app`) -- no es un HTML estático.
No trae los `.parquet` de datos (pesan >100MB c/u, superan el límite de
GitHub, y se regeneran corriendo `pull_data.py`).

Ver el README de cada subcarpeta para instrucciones de instalación y
uso.

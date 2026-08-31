@echo off
REM ============================================================
REM INICIAR_MINI_APP.bat -- Historico Diario 2026 vs 2025
REM (FastAPI + DuckDB). Deja el entorno listo desde cero y abre
REM el navegador solo. Correr con doble-click desde esta carpeta.
REM ============================================================
setlocal
cd /d "%~dp0"

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontro "uv" en el PATH.
    echo         Instalalo primero: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/4] Creando entorno virtual dedicado...
    uv venv
) else (
    echo [1/4] Entorno virtual ya existe, se reutiliza.
)

echo [2/4] Instalando dependencias (fastapi, duckdb, bigquery...)...
uv pip install --python .venv\Scripts\python.exe -r requirements.txt --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias. Revisa que tengas VPN/Eagle WiFi de Walmart.
    pause
    exit /b 1
)

if not exist "ty.parquet" (
    echo [3/4] No hay datos locales todavia -- descargando de BigQuery.
    echo        Esto tarda varios minutos y tiene costo real de BQ ^(~12-13 GB^).
    echo        Requiere: gcloud autenticado contra wmt-intl-cons-mx-users.
    .venv\Scripts\python.exe pull_data.py
    if errorlevel 1 (
        echo [ERROR] Fallo la descarga de datos. Revisa tu autenticacion de gcloud/BigQuery.
        pause
        exit /b 1
    )
) else (
    echo [3/4] Datos locales encontrados ^(ty.parquet / ly.parquet^), no se vuelven a descargar.
    echo        Para refrescar: borra ty.parquet y ly.parquet y vuelve a correr este .bat.
)

echo [4/4] Levantando servidor y abriendo el navegador...
start "" cmd /c "timeout /t 3 /nobreak >nul && start "" http://127.0.0.1:8420"
echo.
echo Servidor corriendo en esta ventana -- NO la cierres mientras uses la app.
echo Para apagarla: Ctrl+C aqui, o simplemente cierra esta ventana.
echo.
.venv\Scripts\python.exe -m uvicorn app:app --port 8420
endlocal

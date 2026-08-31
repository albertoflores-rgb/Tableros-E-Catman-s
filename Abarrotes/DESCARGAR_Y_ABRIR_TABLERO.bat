@echo off
REM ============================================================
REM DESCARGAR_Y_ABRIR_TABLERO.bat
REM
REM Punto de entrada para usuarios SIN conocimientos tecnicos.
REM No requiere git, ni Python, ni instalar nada -- solo Windows.
REM
REM Que hace:
REM   1) Descarga la ultima version del repo completo desde GitHub
REM      (todo ya vive en el .git, incluido el HTML final compilado).
REM   2) La descomprime en una carpeta junto a este .bat.
REM   3) Abre el tablero oficial (HTML autocontenido, 5 pestanas)
REM      directo en el navegador -- no necesita servidor.
REM
REM Correr con doble-click. Requiere conexion a internet
REM (VPN o Eagle WiFi de Walmart).
REM ============================================================
setlocal
cd /d "%~dp0"

set "REPO_ZIP_URL=https://github.com/albertoflores-rgb/Tableros-E-Catman-s/archive/refs/heads/main.zip"
set "DEST_DIR=%~dp0Tablero_Descargado"
set "ZIP_PATH=%~dp0_tablero_descarga_temp.zip"

echo ============================================================
echo   Tablero Insights .com Abarrotes -- Descarga automatica
echo ============================================================
echo.

echo [1/4] Descargando la ultima version desde GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { Invoke-WebRequest -Uri '%REPO_ZIP_URL%' -OutFile '%ZIP_PATH%' -UseBasicParsing } catch { Write-Host ('[ERROR] ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo descargar el tablero.
    echo         Verifica que tengas conexion a internet ^(VPN o Eagle
    echo         WiFi de Walmart^) e intenta de nuevo.
    pause
    exit /b 1
)

echo [2/4] Descomprimiendo...
if exist "%DEST_DIR%" rd /s /q "%DEST_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%DEST_DIR%' -Force"
if errorlevel 1 (
    echo [ERROR] No se pudo descomprimir el archivo descargado.
    pause
    exit /b 1
)
del /q "%ZIP_PATH%" >nul 2>&1

echo [3/4] Localizando el tablero dentro de la descarga...
set "HTML_FILE="
for /r "%DEST_DIR%" %%F in (tablero_insights_com_abarrotes.html) do set "HTML_FILE=%%F"

if not defined HTML_FILE (
    echo [ERROR] No se encontro tablero_insights_com_abarrotes.html
    echo         dentro del ZIP descargado. Avisa a quien mantiene este
    echo         repo -- puede que se haya movido o renombrado.
    pause
    exit /b 1
)

echo [4/4] Abriendo el tablero en tu navegador...
start "" "%HTML_FILE%"

echo.
echo ============================================================
echo   Listo! El tablero ya se abrio en tu navegador.
echo ============================================================
echo.
echo Se guardo una copia completa del repo en:
echo   %DEST_DIR%
echo.
echo Para actualizar a la version mas reciente en el futuro, vuelve
echo a correr este mismo .bat -- reemplaza la copia automaticamente.
echo.
echo Extra para usuarios avanzados: si tambien quieres el Historico
echo Diario con nivel Tienda-Item (requiere servidor local + acceso a
echo BigQuery), entra a esta carpeta y corre INICIAR_MINI_APP.bat:
echo   %DEST_DIR%\Tableros-E-Catman-s-main\Abarrotes\tablero_insights_com_abarrotes\historico_app\
echo.
pause
endlocal

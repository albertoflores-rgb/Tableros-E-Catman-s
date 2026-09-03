@echo off
REM ============================================================
REM ABRIR_6_TABLEROS_LIDER.bat -- Pipeline_Compartido_Equipos
REM
REM Abre los 6 tableros Insights .com (uno por cada equipo E-Catman)
REM A LA PAR en el navegador, para revision rapida del lider -- sin
REM tener que entrar carpeta por carpeta y darle doble-click a cada
REM uno por separado.
REM
REM Punto de entrada para usuarios SIN conocimientos tecnicos.
REM No requiere git, ni Python, ni instalar nada -- solo Windows.
REM Mismo patron que los .bat individuales de cada equipo (ver
REM "<Carpeta equipo>/DESCARGAR_Y_ABRIR_TABLERO.bat"): detecta solo
REM si el repo ya esta junto a este archivo, y si no, descarga el
REM ZIP completo de GitHub una sola vez.
REM
REM Lista de equipos (debe reflejar teams_config.py -- si se agrega,
REM quita o renombra un equipo ahi, actualizar tambien esta lista):
REM   Congelados y deli / tablero_insights_com_perecederos
REM   Impulso           / tablero_insights_com_impulso
REM   Temporada         / tablero_insights_com_seasonal
REM   Ropa              / tablero_insights_com_apparel
REM   Tecnologia        / tablero_insights_com_tecnologia
REM   Salud y Bienestar / tablero_insights_com_salud_bienestar
REM
REM Correr con doble-click.
REM ============================================================
setlocal
cd /d "%~dp0"

set "REPO_ZIP_URL=https://github.com/albertoflores-rgb/Tableros-E-Catman-s/archive/refs/heads/main.zip"
set "DEST_DIR=%~dp0Tableros_Descargados"
set "ZIP_PATH=%~dp0_tableros_descarga_temp.zip"
set "REPO_ROOT=%~dp0.."
set "BASE="

echo ============================================================
echo   Abrir los 6 tableros E-Catman -- revision de equipo
echo ============================================================
echo.

REM --- Caso A: el repo ya esta completo junto a este .bat -------
if exist "%REPO_ROOT%\Congelados y deli\tablero_insights_com_perecederos\tablero_insights_com_perecederos.html" (
    echo Repo ya extraido junto a este archivo -- abriendo directo,
    echo sin necesidad de descargar nada.
    set "BASE=%REPO_ROOT%"
    goto :abrir
)

REM --- Caso B: .bat suelto -- hay que descargar todo -------------
echo No se encontro el repo junto a este archivo -- se descargara
echo la ultima version completa desde GitHub.
echo.
echo [1/3] Descargando la ultima version desde GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { Invoke-WebRequest -Uri '%REPO_ZIP_URL%' -OutFile '%ZIP_PATH%' -UseBasicParsing } catch { Write-Host ('[ERROR] ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo descargar los tableros.
    echo         Verifica que tengas conexion a internet ^(VPN o Eagle
    echo         WiFi de Walmart^) e intenta de nuevo.
    echo.
    echo         Alternativa si esto sigue fallando: entra a
    echo         https://github.com/albertoflores-rgb/Tableros-E-Catman-s
    echo         boton verde "Code" -^> "Download ZIP", extrae el ZIP
    echo         completo, y vuelve a correr ESTE MISMO .bat desde
    echo         adentro de la carpeta "Pipeline_Compartido_Equipos" ya extraida.
    pause
    exit /b 1
)

echo [2/3] Descomprimiendo...
if exist "%DEST_DIR%" rd /s /q "%DEST_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%DEST_DIR%' -Force } catch { Write-Host ('[ERROR] ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
    echo [ERROR] No se pudo descomprimir el archivo descargado.
    pause
    exit /b 1
)
del /q "%ZIP_PATH%" >nul 2>&1

echo [3/3] Localizando la carpeta del repo dentro de la descarga...
for /d %%D in ("%DEST_DIR%\*") do set "BASE=%%D"
if not defined BASE (
    echo [ERROR] No se pudo localizar el repo dentro del ZIP descargado.
    echo         Avisa a quien mantiene este repo.
    pause
    exit /b 1
)

:abrir
echo Abriendo los 6 tableros en tu navegador ^(uno por pestana^)...
echo.
start "" "%BASE%\Congelados y deli\tablero_insights_com_perecederos\tablero_insights_com_perecederos.html"
start "" "%BASE%\Impulso\tablero_insights_com_impulso\tablero_insights_com_impulso.html"
start "" "%BASE%\Temporada\tablero_insights_com_seasonal\tablero_insights_com_seasonal.html"
start "" "%BASE%\Ropa\tablero_insights_com_apparel\tablero_insights_com_apparel.html"
start "" "%BASE%\Tecnologia\tablero_insights_com_tecnologia\tablero_insights_com_tecnologia.html"
start "" "%BASE%\Salud y Bienestar\tablero_insights_com_salud_bienestar\tablero_insights_com_salud_bienestar.html"

echo ============================================================
echo   Listo! Los 6 tableros ya se abrieron en tu navegador.
echo ============================================================
pause
endlocal

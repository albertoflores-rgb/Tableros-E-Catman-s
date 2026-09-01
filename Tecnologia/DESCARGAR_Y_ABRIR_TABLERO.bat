@echo off
REM ============================================================
REM DESCARGAR_Y_ABRIR_TABLERO.bat -- Tecnologia
REM
REM Punto de entrada para usuarios SIN conocimientos tecnicos.
REM No requiere git, ni Python, ni instalar nada -- solo Windows.
REM
REM Funciona de 2 formas (se detecta solo, no tienes que elegir):
REM   A) Repo ya extraido junto a este .bat -- abre de inmediato.
REM   B) .bat suelto -- descarga el repo completo como ZIP, lo
REM      descomprime aqui mismo, y abre el tablero.
REM
REM Correr con doble-click.
REM ============================================================
setlocal
cd /d "%~dp0"

set "REPO_ZIP_URL=https://github.com/albertoflores-rgb/Tableros-E-Catman-s/archive/refs/heads/main.zip"
set "DEST_DIR=%~dp0Tablero_Descargado"
set "ZIP_PATH=%~dp0_tablero_descarga_temp.zip"
set "HTML_FILE="

echo ============================================================
echo   Tablero Insights .com Tecnologia
echo ============================================================
echo.

REM --- Caso A: el repo ya esta completo junto a este .bat -------
if exist "%~dp0tablero_insights_com_tecnologia\tablero_insights_com_tecnologia.html" (
    echo Repo ya extraido junto a este archivo -- abriendo directo,
    echo sin necesidad de descargar nada.
    set "HTML_FILE=%~dp0tablero_insights_com_tecnologia\tablero_insights_com_tecnologia.html"
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
    echo [ERROR] No se pudo descargar el tablero.
    echo         Verifica que tengas conexion a internet ^(VPN o Eagle
    echo         WiFi de Walmart^) e intenta de nuevo.
    echo.
    echo         Alternativa si esto sigue fallando: entra a
    echo         https://github.com/albertoflores-rgb/Tableros-E-Catman-s
    echo         boton verde "Code" -^> "Download ZIP", extrae el ZIP
    echo         completo, y vuelve a correr ESTE MISMO .bat desde
    echo         adentro de la carpeta "Tecnologia" ya extraida.
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

echo [3/3] Localizando el tablero dentro de la descarga...
REM NOTA: for /r con un nombre de archivo SIN comodin no verifica que
REM el archivo exista de verdad -- por eso se usa un comodin real
REM (*.html) y se filtra el nombre exacto adentro.
for /r "%DEST_DIR%" %%F in (*.html) do (
    if /i "%%~nxF"=="tablero_insights_com_tecnologia.html" set "HTML_FILE=%%F"
)

if not defined HTML_FILE (
    echo [ERROR] No se encontro tablero_insights_com_tecnologia.html dentro del ZIP descargado.
    echo         Avisa a quien mantiene este repo.
    pause
    exit /b 1
)

:abrir
echo Abriendo el tablero en tu navegador...
start "" "%HTML_FILE%"

echo.
echo ============================================================
echo   Listo! El tablero ya se abrio en tu navegador.
echo ============================================================
pause
endlocal

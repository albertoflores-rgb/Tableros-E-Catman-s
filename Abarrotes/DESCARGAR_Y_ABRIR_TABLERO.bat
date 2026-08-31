@echo off
REM ============================================================
REM DESCARGAR_Y_ABRIR_TABLERO.bat
REM
REM Punto de entrada para usuarios SIN conocimientos tecnicos.
REM No requiere git, ni Python, ni instalar nada -- solo Windows.
REM
REM Funciona de 2 formas (se detecta solo, no tienes que elegir):
REM
REM   A) Si ya tienes el repo completo descargado/extraido (ej.
REM      usaste el boton verde "Code > Download ZIP" de GitHub y
REM      extrajiste el ZIP) y corres este .bat desde dentro de la
REM      carpeta Abarrotes -- abre el tablero DE INMEDIATO, sin
REM      tocar internet.
REM
REM   B) Si tienes SOLO este archivo .bat suelto (ej. lo guardaste
REM      aparte desde GitHub) -- descarga el repo completo como
REM      ZIP, lo descomprime aqui mismo, y abre el tablero.
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
echo   Tablero Insights .com Abarrotes
echo ============================================================
echo.

REM --- Caso A: el repo ya esta completo junto a este .bat -------
if exist "%~dp0tablero_insights_com_abarrotes\tablero_insights_com_abarrotes.html" (
    echo Repo ya extraido junto a este archivo -- abriendo directo,
    echo sin necesidad de descargar nada.
    set "HTML_FILE=%~dp0tablero_insights_com_abarrotes\tablero_insights_com_abarrotes.html"
    goto :abrir
)

REM --- Caso B: .bat suelto -- hay que descargar todo -------------
echo No se encontro el repo junto a este archivo -- se descargara
echo la ultima version completa desde GitHub.
echo.
echo [1/4] Descargando la ultima version desde GitHub...
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
    echo         adentro de la carpeta Abarrotes ya extraida.
    pause
    exit /b 1
)

echo [2/4] Descomprimiendo...
if exist "%DEST_DIR%" rd /s /q "%DEST_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%DEST_DIR%' -Force } catch { Write-Host ('[ERROR] ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
    echo [ERROR] No se pudo descomprimir el archivo descargado.
    pause
    exit /b 1
)
del /q "%ZIP_PATH%" >nul 2>&1

echo [3/4] Localizando el tablero dentro de la descarga...
REM NOTA: for /r con un nombre de archivo SIN comodin no verifica
REM que el archivo exista de verdad -- lo "encuentra" en TODAS las
REM carpetas que recorre, aunque no este ahi. Por eso se usa un
REM comodin real (*.html) y se filtra el nombre exacto adentro.
for /r "%DEST_DIR%" %%F in (*.html) do (
    if /i "%%~nxF"=="tablero_insights_com_abarrotes.html" set "HTML_FILE=%%F"
)

if not defined HTML_FILE (
    echo [ERROR] No se encontro tablero_insights_com_abarrotes.html
    echo         dentro del ZIP descargado. Avisa a quien mantiene este
    echo         repo -- puede que se haya movido o renombrado.
    pause
    exit /b 1
)

:abrir
echo [4/4] Abriendo el tablero en tu navegador...
start "" "%HTML_FILE%"

echo.
echo ============================================================
echo   Listo! El tablero ya se abrio en tu navegador.
echo ============================================================
pause
endlocal

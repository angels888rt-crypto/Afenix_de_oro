@echo off
REM ============================================================
REM  Instalador del servicio de impresión térmica — Afenix de Oro
REM  Ejecutar como Administrador en el computador con la impresora
REM ============================================================

setlocal EnableDelayedExpansion
title Instalador Servicio Impresion Afenix

echo.
echo  ===================================================
echo   Servicio de Impresion Termica — Afenix de Oro
echo  ===================================================
echo.

REM ── 1. Verificar Python ──────────────────────────────────────────────────
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado.
    echo Descarga Python 3.10+ desde https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo         %%v encontrado
echo.

REM ── 2. Crear entorno virtual ─────────────────────────────────────────────
echo [2/5] Creando entorno virtual en print_service\venv ...
pushd "%~dp0"

if exist venv (
    echo         Entorno virtual ya existe, omitiendo creacion.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        popd & pause & exit /b 1
    )
    echo         Entorno virtual creado correctamente.
)
echo.

REM ── 3. Instalar dependencias ─────────────────────────────────────────────
echo [3/5] Instalando dependencias desde requirements.txt ...
call venv\Scripts\pip.exe install --upgrade pip --quiet
call venv\Scripts\pip.exe install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    echo Revisa tu conexion a internet e intenta de nuevo.
    popd & pause & exit /b 1
)
echo         Dependencias instaladas correctamente.
echo.

REM ── 4. Crear archivo .env desde .env.example ────────────────────────────
echo [4/5] Configurando archivo .env ...
if not exist .env (
    copy .env.example .env >nul
    echo         Archivo .env creado desde .env.example
    echo.
    echo  IMPORTANTE: Edita print_service\.env antes de continuar.
    echo  Ajusta al menos:
    echo    PRINTER_NAME    = nombre exacto de la impresora en Windows
    echo    API_BASE_URL    = URL del backend (si no es localhost)
    echo    PRINTER_API_KEY = misma clave que en project\.env
    echo    RESTAURANT_NAME = nombre de tu restaurante
    echo    FOOTER_MESSAGE  = mensaje al pie del ticket
    echo.
    echo  Presiona cualquier tecla para abrir .env en el Bloc de notas...
    pause >nul
    notepad .env
) else (
    echo         .env ya existe, no se sobreescribe.
)
echo.

REM ── 5. Aplicar migración a la base de datos ──────────────────────────────
echo [5/5] Aplicando migracion a la base de datos...
echo.
echo  Opciones:
echo    A) Aplicar via Alembic (recomendado si el backend funciona)
echo    B) Aplicar via SQL directo (fallback manual)
echo    S) Saltar este paso (lo hare manualmente)
echo.
set /p MOPT="Elige una opcion [A/B/S]: "

if /i "!MOPT!"=="A" (
    call run_migration.bat
) else if /i "!MOPT!"=="B" (
    echo.
    echo  Ejecuta en MySQL Workbench o consola MySQL:
    echo    mysql -u root -p proyecto_afenix ^< print_service\apply_migration.sql
    echo.
    echo  O copia el contenido de apply_migration.sql en phpMyAdmin.
    pause
) else (
    echo  Migracion saltada. Recuerda aplicarla antes de iniciar el servicio.
)
echo.

REM ── Resumen ──────────────────────────────────────────────────────────────
echo  ===================================================
echo   Instalacion completada
echo  ===================================================
echo.
echo  Para iniciar el servicio de impresion:
echo    Doble clic en:  start_service.bat
echo.
echo  Para detenerlo:
echo    Presiona Ctrl+C en la ventana del servicio, o
echo    cierra la ventana de consola.
echo.
echo  Logs en:  print_service\printer_service.log
echo.

popd
pause

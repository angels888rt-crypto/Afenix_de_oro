@echo off
REM ============================================================
REM  Aplica la migración de impresión via Alembic
REM  Ejecutar desde la raíz del proyecto (donde está esta carpeta)
REM ============================================================

echo.
echo === Aplicando migracion de impresion (Alembic) ===
echo.

REM Cambiar al directorio del backend
pushd "%~dp0..\project"

REM Verificar que Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Asegurate de tener Python 3.10+ instalado.
    popd
    pause
    exit /b 1
)

REM Ejecutar la migración Alembic
echo Ejecutando: alembic upgrade head
python -m alembic upgrade head

if errorlevel 1 (
    echo.
    echo [ERROR] La migracion Alembic fallo.
    echo Alternativa: ejecuta manualmente el archivo print_service\apply_migration.sql
    echo   mysql -u root -p proyecto_afenix ^< print_service\apply_migration.sql
    popd
    pause
    exit /b 1
)

echo.
echo [OK] Migracion aplicada correctamente.
echo Las columnas print_status, print_attempts y printed_at
echo han sido agregadas a la tabla orders.
echo.

popd
pause

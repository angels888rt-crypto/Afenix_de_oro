@echo off
REM ============================================================
REM  Inicia el servicio de impresión térmica — Afenix de Oro
REM  Mantener esta ventana abierta mientras el restaurante opera.
REM  Para detener: Ctrl+C o cerrar la ventana.
REM ============================================================

title Servicio Impresion Termica — Afenix de Oro

pushd "%~dp0"

REM Verificar que el entorno virtual existe
if not exist venv\Scripts\python.exe (
    echo [ERROR] Entorno virtual no encontrado.
    echo Ejecuta primero install.bat
    popd & pause & exit /b 1
)

REM Verificar que .env existe
if not exist .env (
    echo [ERROR] Archivo .env no encontrado.
    echo Ejecuta primero install.bat o copia .env.example como .env
    popd & pause & exit /b 1
)

echo.
echo  ===================================================
echo   Servicio de Impresion Termica — Afenix de Oro
echo   Presiona Ctrl+C para detener
echo  ===================================================
echo.

venv\Scripts\python.exe main.py

REM Si el proceso termina inesperadamente, mostrar pausa para ver el error
echo.
echo [INFO] El servicio se detuvo. Revisa el log: printer_service.log
popd
pause

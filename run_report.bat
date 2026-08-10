@echo off
setlocal
title ETLGITHUB - Reporte completo
cd /d "%~dp0"

echo.
echo ETLGITHUB - Pipeline, notebook y graficos
echo Esta ventana queda abierta al finalizar para que puedas revisar el resultado.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_report_windows.ps1" -PauseOnExit
set "REPORT_EXIT_CODE=%ERRORLEVEL%"

if not "%REPORT_EXIT_CODE%"=="0" (
    echo.
    echo El reporte termino con errores. Codigo: %REPORT_EXIT_CODE%
)

endlocal & exit /b %REPORT_EXIT_CODE%

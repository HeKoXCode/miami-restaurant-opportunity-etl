@echo off
setlocal
title ETLGITHUB - Demo sintetica
cd /d "%~dp0"

echo.
echo ETLGITHUB - Pipeline demo sintetico
echo No requiere el raw privado de clientes.
echo Esta ventana queda abierta al finalizar para que puedas revisar el resultado.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_pipeline_windows.ps1" -Mode demo -Force -PauseOnExit
set "DEMO_EXIT_CODE=%ERRORLEVEL%"

if not "%DEMO_EXIT_CODE%"=="0" (
    echo.
    echo La demo termino con errores. Codigo: %DEMO_EXIT_CODE%
)

endlocal & exit /b %DEMO_EXIT_CODE%

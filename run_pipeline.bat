@echo off
setlocal
title ETLGITHUB - Pipeline
cd /d "%~dp0"

echo.
echo ETLGITHUB - Pipeline
echo Esta ventana queda abierta al finalizar para que puedas revisar el resultado.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_pipeline_windows.ps1" -PauseOnExit
set "PIPELINE_EXIT_CODE=%ERRORLEVEL%"

if not "%PIPELINE_EXIT_CODE%"=="0" (
    echo.
    echo El pipeline termino con errores. Codigo: %PIPELINE_EXIT_CODE%
)

endlocal & exit /b %PIPELINE_EXIT_CODE%

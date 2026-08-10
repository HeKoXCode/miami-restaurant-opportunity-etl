@echo off
setlocal
title ETLGITHUB - Setup
cd /d "%~dp0"

echo.
echo ETLGITHUB - Setup de entorno
echo Esta ventana queda abierta al finalizar para que puedas revisar el resultado.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1" -PauseOnExit
set "SETUP_EXIT_CODE=%ERRORLEVEL%"

if not "%SETUP_EXIT_CODE%"=="0" (
    echo.
    echo El setup termino con errores. Codigo: %SETUP_EXIT_CODE%
)

endlocal & exit /b %SETUP_EXIT_CODE%

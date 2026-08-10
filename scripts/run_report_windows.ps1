param(
    [switch]$PauseOnExit
)

$ErrorActionPreference = "Stop"
$exitCode = 0

function Wait-BeforeClose {
    if (-not $PauseOnExit) {
        return
    }

    Write-Host ""
    Write-Host "Presiona cualquier tecla para cerrar..." -ForegroundColor Yellow

    try {
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } catch {
        $null = Read-Host "Presiona ENTER para cerrar"
    }
}

try {
    $ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectRoot = (Resolve-Path (Join-Path $ScriptRoot "..")).Path
    Set-Location $ProjectRoot

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    $python = if (Test-Path -LiteralPath $venvPython) {
        $venvPython
    } else {
        "python"
    }

    Write-Host ""
    Write-Host "ETLGITHUB - reporte completo" -ForegroundColor Green

    # Primero actualizamos los CSV que alimentan el análisis.
    Write-Host ""
    Write-Host "[1/2] Regenerando pipeline" -ForegroundColor Cyan
    & $python -m src.pipeline
    if ($LASTEXITCODE -ne 0) {
        throw "El pipeline termino con codigo $LASTEXITCODE."
    }

    # Después ejecutamos el notebook y guardamos sus gráficos y resultados.
    Write-Host ""
    Write-Host "[2/2] Ejecutando notebook y graficos" -ForegroundColor Cyan
    & $python "scripts\render_notebook.py"
    if ($LASTEXITCODE -ne 0) {
        throw "El notebook termino con codigo $LASTEXITCODE."
    }

    Write-Host ""
    Write-Host "Reporte actualizado correctamente." -ForegroundColor Green
} catch {
    $exitCode = 1
    Write-Host ""
    Write-Host "No se pudo regenerar el reporte." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    Wait-BeforeClose
    exit $exitCode
}

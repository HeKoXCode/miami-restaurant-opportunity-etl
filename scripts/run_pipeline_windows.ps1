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

    Write-Host ""
    Write-Host "ETLGITHUB - ejecucion del pipeline" -ForegroundColor Green

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

    if (Test-Path -LiteralPath $venvPython) {
        & $venvPython -m src.pipeline
    } else {
        Write-Host "No encontre .venv. Uso el Python disponible en el sistema." -ForegroundColor Yellow
        python -m src.pipeline
    }

    if ($LASTEXITCODE -ne 0) {
        throw "El pipeline termino con codigo $LASTEXITCODE."
    }
} catch {
    $exitCode = 1

    Write-Host ""
    Write-Host "El pipeline no pudo completarse." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    Wait-BeforeClose
    exit $exitCode
}

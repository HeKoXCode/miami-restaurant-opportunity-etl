param(
    [ValidateSet("full", "demo")]
    [string]$Mode = "full",
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
    Write-Host "ETLGITHUB - ejecucion del pipeline ($Mode)" -ForegroundColor Green

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

    if (Test-Path -LiteralPath $venvPython) {
        & $venvPython -m src.pipeline --mode $Mode
    } else {
        Write-Host "No encontre .venv. Uso el Python disponible en el sistema." -ForegroundColor Yellow
        python -m src.pipeline --mode $Mode
    }

    if ($LASTEXITCODE -ne 0) {
        throw "El pipeline termino con codigo $LASTEXITCODE."
    }

    if ($Mode -eq "demo") {
        if (Test-Path -LiteralPath $venvPython) {
            & $venvPython scripts\validate_publication.py --mode demo
        } else {
            python scripts\validate_publication.py --mode demo
        }

        if ($LASTEXITCODE -ne 0) {
            throw "La validacion demo termino con codigo $LASTEXITCODE."
        }
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

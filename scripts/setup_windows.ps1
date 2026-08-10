param(
    [switch]$PauseOnExit
)

$ErrorActionPreference = "Stop"
$exitCode = 0

function Write-Step {
    param(
        [string]$Number,
        [string]$Message
    )

    Write-Host ""
    Write-Host "[$Number] $Message" -ForegroundColor Cyan
}

function Invoke-CheckedCommand {
    param(
        [string]$Description,
        [string]$Command,
        [string[]]$Arguments
    )

    Write-Host $Description -ForegroundColor DarkCyan
    & $Command @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "$Description fallo con codigo $LASTEXITCODE."
    }
}

function Wait-BeforeClose {
    if (-not $PauseOnExit) {
        return
    }

    Write-Host ""
    Write-Host "La ventana queda abierta para que puedas revisar el resultado." -ForegroundColor DarkGray
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
    Write-Host "ETLGITHUB - preparacion del entorno" -ForegroundColor Green
    Write-Host "Carpeta del proyecto: $ProjectRoot"
    Write-Host "Este script crea .venv, instala requirements y registra el kernel de Jupyter."

    Write-Step "1/5" "Buscando Python"
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $python = "py"
        $pythonArgs = @("-3")
    } else {
        $python = "python"
        $pythonArgs = @()
    }

    if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
        throw "No encontre Python. Instala Python 3.12, 3.13 o 3.14 y volve a ejecutar el setup."
    }

    Invoke-CheckedCommand "Verificando version de Python" $python ($pythonArgs + @("-c", "import sys; raise SystemExit(0 if (3, 12) <= sys.version_info[:2] < (3, 15) else 1)"))

    Write-Step "2/5" "Preparando entorno virtual"
    if (-not (Test-Path -LiteralPath ".venv")) {
        Invoke-CheckedCommand "Creando .venv" $python ($pythonArgs + @("-m", "venv", ".venv"))
    } else {
        Write-Host ".venv ya existe, lo reutilizo." -ForegroundColor DarkGray
    }

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "No encontre el Python del entorno virtual en $venvPython."
    }

    Write-Step "3/5" "Actualizando pip"
    Invoke-CheckedCommand "python -m pip install --upgrade pip" $venvPython @("-m", "pip", "install", "--upgrade", "pip")

    Write-Step "4/5" "Instalando dependencias del proyecto"
    Invoke-CheckedCommand "python -m pip install -r requirements.txt" $venvPython @("-m", "pip", "install", "-r", "requirements.txt")

    Write-Step "5/5" "Registrando kernel de Jupyter"
    Invoke-CheckedCommand "python -m ipykernel install" $venvPython @("-m", "ipykernel", "install", "--user", "--name", "etlgithub", "--display-name", "Python (ETLGITHUB)")

    Write-Host ""
    Write-Host "Setup terminado correctamente." -ForegroundColor Green
    Write-Host ""
    Write-Host "Para correr el pipeline:" -ForegroundColor Green
    Write-Host ".\.venv\Scripts\python.exe -m src.pipeline"
    Write-Host ""
    Write-Host "Para correr tests:" -ForegroundColor Green
    Write-Host ".\.venv\Scripts\python.exe -m pytest -q"
} catch {
    $exitCode = 1

    Write-Host ""
    Write-Host "El setup no pudo completarse." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Deje la ventana abierta para que puedas leer el error." -ForegroundColor Yellow
} finally {
    Wait-BeforeClose
    exit $exitCode
}

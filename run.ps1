# PowerShell Runner for BlueBridge (Phone as PC Speaker)
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython (Join-Path $PSScriptRoot "app.py") @args
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py (Join-Path $PSScriptRoot "app.py") @args
} else {
    python (Join-Path $PSScriptRoot "app.py") @args
}

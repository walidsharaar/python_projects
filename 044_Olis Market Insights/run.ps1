# run.ps1 - Windows entry point: creates the virtual environment if missing, installs requirements, runs run_all.py.
# Any arguments are passed on, e.g.  .\run.ps1 --from warehouse   or   .\run.ps1 --dry-run
# If PowerShell blocks the script once:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if ($env:VIRTUAL_ENV -and ($env:VIRTUAL_ENV -ne (Join-Path $PSScriptRoot ".venv"))) {
    Write-Host "Another virtual environment is active ($env:VIRTUAL_ENV). Run 'deactivate' first." -ForegroundColor Red
    exit 1
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment .venv ..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Write-Host "Could not create .venv. Is Python installed?" -ForegroundColor Red; exit 1 }
}

Write-Host "Installing requirements ..." -ForegroundColor Cyan
& $python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "pip install failed." -ForegroundColor Red; exit 1 }

& $python run_all.py @args
exit $LASTEXITCODE

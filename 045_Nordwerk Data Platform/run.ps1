# Nordwerk Data Platform - one click on Windows.
#   .\run.ps1                 everything: venv, packages, database, pipeline, checks, tests, Power BI project
#   .\run.ps1 demo block      any manage.py command, e.g. run, check, status, test unit, demo fix
# Needs: Python 3.12 and Docker Desktop (running).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment ..." -ForegroundColor Cyan
    python -m venv .venv
}
$py = ".venv\Scripts\python.exe"

& $py -m pip install --quiet --disable-pip-version-check -r requirements.txt

if ($args.Count -eq 0) { $args = @("showcase") }
& $py manage.py @args
exit $LASTEXITCODE

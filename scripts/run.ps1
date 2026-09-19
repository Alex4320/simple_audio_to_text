$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Create the environment first: python -m venv .venv; .\.venv\Scripts\pip install -e .  (see INSTALL.md)"
}

& $venvPython -m simple_audio_to_text

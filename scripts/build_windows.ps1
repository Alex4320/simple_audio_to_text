$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Find-Python {
    foreach ($command in @("python", "py")) {
        $item = Get-Command $command -ErrorAction SilentlyContinue
        if (-not $item) {
            continue
        }
        if ($command -eq "py") {
            return @{ File = $item.Source; Args = @("-3") }
        }
        return @{ File = $item.Source; Args = @() }
    }
    throw "Python 3.10+ not found. Install Python and enable Add python.exe to PATH."
}

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in .venv ..."
    $python = Find-Python
    & $python.File @($python.Args + @("-m", "venv", ".venv"))
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create .venv"
    }
}

Write-Host "Installing application and PyInstaller ..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade failed"
}
& $venvPython -m pip install -e . pyinstaller
if ($LASTEXITCODE -ne 0) {
    throw "Dependency install failed"
}

$running = Get-Process SpeechToText -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "Closing running SpeechToText.exe so the build can overwrite it..."
    $running | Stop-Process -Force
    Start-Sleep -Seconds 1
}

Write-Host "Building dist/SpeechToText ..."
& $venvPython -m PyInstaller simple_audio_to_text.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$exe = Join-Path (Get-Location) "dist\SpeechToText\SpeechToText.exe"
if (-not (Test-Path $exe)) {
    throw "Build finished but $exe was not created"
}

Write-Host "Done: $exe"
Write-Host "Copy the whole dist/SpeechToText folder if you move the app."
Write-Host "If Explorer still shows the old icon, restart Explorer or copy the folder to a new path."

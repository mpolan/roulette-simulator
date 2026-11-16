param(
    [string]$Python = ".\venv\Scripts\python.exe",
    [switch]$SkipInstall
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
if ($env:OS -ne "Windows_NT") { throw "Build Windows GUI on Windows." }
Push-Location -LiteralPath $PSScriptRoot
try {
    if (-not $SkipInstall) {
        & $Python -m pip install -r requirements-build-gui.txt
        if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    }
    & $Python -m PyInstaller --noconfirm --clean ObsidianRoyaleGUI.spec
    if ($LASTEXITCODE -ne 0) { throw "GUI build failed." }
    if (-not (Test-Path -LiteralPath "dist\ObsidianRoyaleGUI.exe")) {
        throw "Missing GUI executable."
    }
    Write-Host "Ready: dist\ObsidianRoyaleGUI.exe"
    Write-Host "No database is bundled. User data stays in data\roulette.db beside the EXE."
}
finally { Pop-Location }

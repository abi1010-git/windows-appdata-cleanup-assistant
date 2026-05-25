param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

if (-not $SkipTests) {
    .\.venv\Scripts\python.exe -m pytest -q
}

if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
}
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}

.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm StorageDetective.spec

$PackagePath = "dist\Storage-Detective-Windows.zip"
if (Test-Path $PackagePath) {
    Remove-Item $PackagePath -Force
}

Compress-Archive -Path "dist\Storage Detective\*" -DestinationPath $PackagePath -Force
Write-Host "Built $PackagePath"

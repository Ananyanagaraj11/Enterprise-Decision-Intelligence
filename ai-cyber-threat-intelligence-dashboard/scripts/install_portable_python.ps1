# Install portable Python into the project folder (no system Python needed).
# Run: powershell -ExecutionPolicy Bypass -File scripts\install_portable_python.ps1

$ErrorActionPreference = "Stop"
# Project root = folder that contains the "scripts" folder (parent of $PSScriptRoot)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonVersion = "3.12.10"
$ZipName = "python-$PythonVersion-embed-amd64.zip"
$DownloadUrl = "https://www.python.org/ftp/python/$PythonVersion/$ZipName"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$PortableDir = Join-Path $ProjectRoot "python_portable"
$ZipPath = Join-Path $ProjectRoot $ZipName
$GetPipPath = Join-Path $ProjectRoot "get-pip.py"
$RequirementsPath = Join-Path $ProjectRoot "requirements.txt"

Write-Host "Project folder: $ProjectRoot"
if (-not (Test-Path $RequirementsPath)) {
    Write-Host "ERROR: requirements.txt not found at $RequirementsPath"
    exit 1
}
Write-Host ""

if (Test-Path (Join-Path $PortableDir "python.exe")) {
    Write-Host "Portable Python already exists at python_portable\"
    Write-Host "Installing/updating packages..."
    & (Join-Path $PortableDir "python.exe") -m pip install --upgrade pip -q
    & (Join-Path $PortableDir "python.exe") -m pip install -r $RequirementsPath
    Write-Host "Done. Use run_backend.bat and run_dashboard.bat"
    exit 0
}

Write-Host "Downloading Python $PythonVersion embeddable..."
try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -UseBasicParsing
} catch {
    Write-Host "Download failed. Check internet and try again."
    exit 1
}

Write-Host "Extracting to python_portable\..."
if (Test-Path $PortableDir) { Remove-Item $PortableDir -Recurse -Force }
Expand-Archive -Path $ZipPath -DestinationPath $PortableDir -Force

# Enable site-packages in embeddable Python (uncomment "import site" in ._pth)
$PthFile = Get-ChildItem (Join-Path $PortableDir "python*._pth") | Select-Object -First 1
if ($PthFile) {
    (Get-Content $PthFile.FullName) -replace "^#?\s*import site\s*$", "import site" | Set-Content $PthFile.FullName
    $content = Get-Content $PthFile.FullName -Raw
    if ($content -notmatch "^\s*import site") {
        Add-Content -Path $PthFile.FullName -Value "import site"
    }
}

Write-Host "Installing pip..."
Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPipPath -UseBasicParsing
& (Join-Path $PortableDir "python.exe") $GetPipPath --no-warn-script-location

Write-Host "Installing project dependencies..."
& (Join-Path $PortableDir "python.exe") -m pip install --upgrade pip -q
& (Join-Path $PortableDir "python.exe") -m pip install -r $RequirementsPath

# Cleanup
Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
Remove-Item $GetPipPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Portable Python is ready at python_portable\"
Write-Host "Run: scripts\run_backend.bat  (Terminal 1)"
Write-Host "Run: scripts\run_dashboard.bat (Terminal 2)"

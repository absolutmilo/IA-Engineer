# audit.ps1
# PowerShell Launcher for AI Auditor

param (
    [string]$TargetDir
)

$ErrorActionPreference = "Stop"

function Write-Color {
    param([string]$Text, [ConsoleColor]$Color)
    Write-Host $Text -ForegroundColor $Color
}

# 1. Environment Check
Write-Color "[*] Checking Prerequisites..." Green
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "Python 3\.(1[0-9])") {
        Write-Color "Found $pyVersion" Gray
    }
    else {
        Write-Color "[!] Python 3.10+ is required. Found: $pyVersion" Red
        exit 1
    }
}
catch {
    Write-Color "[!] Python not found in PATH." Red
    exit 1
}

# 2. Venv Setup
$VenvDir = "$PSScriptRoot\.venv"
if (-not (Test-Path $VenvDir)) {
    Write-Color "[*] Creating Virtual Environment..." Yellow
    python -m venv $VenvDir
}

# 3. Dependencies
Write-Color "[*] Checking Dependencies..." Yellow
$Pip = "$VenvDir\Scripts\pip.exe"
$PythonKey = "$VenvDir\Scripts\python.exe"

& $Pip install -r "$PSScriptRoot\requirements.txt" -q --disable-pip-version-check

# 4. Ollama Check
Write-Color "[*] Checking Ollama Service..." Yellow
try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop | Out-Null
    Write-Color "Ollama is Online." Green
}
catch {
    Write-Color "[!] Ollama is NOT reachable at localhost:11434. Please start it." Red
    Write-Host "Proceeding anyway (assuming OpenAI fallback or manual fix)..."
}

# 5. Target Selection
if (-not $TargetDir) {
    Add-Type -AssemblyName System.Windows.Forms
    $FolderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $FolderBrowser.Description = "Select the AI Project to Audit"
    $FolderBrowser.ShowNewFolderButton = $false
    
    $result = $FolderBrowser.ShowDialog()
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $TargetDir = $FolderBrowser.SelectedPath
    }
    else {
        Write-Color "[!] No folder selected. Exiting." Red
        exit 1
    }
}

# 6. Launch
Write-Color "[*] Launching Principal Architect Audit on: $TargetDir" Cyan
& $PythonKey "$PSScriptRoot\main.py" "$TargetDir"

<#
.SYNOPSIS
    Automated update script for PIME's embedded Python and Node.js runtimes.

.DESCRIPTION
    This script downloads and updates the 32-bit (x86) Windows runtimes used by PIME:
      1. Node.js 32-bit binary (node.exe) into node/
      2. Python 32-bit embeddable zip into python/python3/
      3. Python configuration (.pth) and site-packages setup (preserves custom .pth files)
      4. Extra dependencies from requirements.txt into Lib/site-packages/
      5. Node.js dependencies via npm in node/
      6. Cache cleanup (purges all __pycache__ and *.pyc bytecode)
      7. Git staging (automatically stages all modifications, additions, and deleted obsolete files)

.PARAMETER NodeVersion
    The version string of Node.js to download (e.g. "22.14.0").

.PARAMETER PythonVersion
    The version string of Python embeddable to download (e.g. "3.12.9").

.PARAMETER StageGit
    Whether to automatically stage all changes in node/ and python/ with 'git add -A' (default: $true).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\update_runtimes.ps1 -NodeVersion "22.14.0" -PythonVersion "3.12.9"
#>

[CmdletBinding()]
param(
    [string]$NodeVersion = "22.14.0",
    [string]$PythonVersion = "3.12.9",
    [bool]$StageGit = $true
)

# Stop immediately if any command fails (equivalent to 'set -e' in bash)
$ErrorActionPreference = "Stop"

# -----------------------------------------------------------------------------
# Locate Repository Root
# This script lives in: <repo>/.agents/skills/update-runtimes/scripts/
# We resolve the repository root by navigating 4 directory levels up.
# -----------------------------------------------------------------------------
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$PimeRoot = (Resolve-Path (Join-Path $ScriptDir "..\..\..\..")).Path
Write-Host "PIME repository root: $PimeRoot"

# -----------------------------------------------------------------------------
# Create an isolated temporary working directory in Windows %TEMP%
# Using a random name avoids conflicts with previous or concurrent runs.
# -----------------------------------------------------------------------------
$TempDir = Join-Path $env:TEMP "pime_update_$([System.IO.Path]::GetRandomFileName())"
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
Write-Host "Temporary download directory: $TempDir"

# UTF-8 encoding helper without BOM (essential for Python embeddable ._pth parser)
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

try {
    # =========================================================================
    # STEP 1: Download and Update Node.js (32-bit x86)
    # =========================================================================
    Write-Host "`n[1/6] Downloading Node.js v$NodeVersion (32-bit x86)..."
    $NodeUrl = "https://nodejs.org/dist/v$NodeVersion/node-v$NodeVersion-win-x86.zip"
    $NodeZip = Join-Path $TempDir "node.zip"
    Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeZip

    Write-Host "Extracting Node.js zip archive..."
    $NodeExtractDir = Join-Path $TempDir "node_extracted"
    Expand-Archive -Path $NodeZip -DestinationPath $NodeExtractDir -Force

    $NodeDestDir = Join-Path $PimeRoot "node"
    Write-Host "Copying new node.exe into $NodeDestDir..."
    $DownloadedNodeExe = Join-Path $NodeExtractDir "node-v$NodeVersion-win-x86\node.exe"
    Copy-Item -Path $DownloadedNodeExe -Destination (Join-Path $NodeDestDir "node.exe") -Force

    # =========================================================================
    # STEP 2: Download and Extract Python (32-bit x86 Embeddable Package)
    # =========================================================================
    Write-Host "`n[2/6] Downloading Python $PythonVersion (32-bit x86 Embeddable)..."
    $PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-win32.zip"
    $PythonZip = Join-Path $TempDir "python.zip"
    Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonZip

    $PythonDestDir = Join-Path $PimeRoot "python\python3"
    $SitePackagesDir = Join-Path $PythonDestDir "Lib\site-packages"

    # Backup requirements.txt and any customized .pth files before cleaning
    $BackupDir = Join-Path $TempDir "python_custom_backup"
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

    $ReqFile = Join-Path $PythonDestDir "requirements.txt"
    if (Test-Path $ReqFile) {
        Copy-Item -Path $ReqFile -Destination $BackupDir
    }

    # Backup all existing custom *.pth files from Lib/site-packages and python3 root
    if (Test-Path $SitePackagesDir) {
        Get-ChildItem -Path $SitePackagesDir -Filter "*.pth" | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $BackupDir
        }
    }
    $RootPimePth = Join-Path $PythonDestDir "PIME.pth"
    if (Test-Path $RootPimePth) {
        Copy-Item -Path $RootPimePth -Destination (Join-Path $BackupDir "PIME.pth")
    }

    Write-Host "Cleaning out old Python files in $PythonDestDir..."
    # Wipe old binaries and libraries to prevent leftover obsolete DLLs
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $PythonDestDir "*")

    Write-Host "Extracting Python embeddable zip..."
    Expand-Archive -Path $PythonZip -DestinationPath $PythonDestDir -Force

    # =========================================================================
    # STEP 3: Configure Python Pathing (.pth files) and site-packages
    # =========================================================================
    Write-Host "`n[3/6] Configuring Python pathing and site-packages..."

    # Recreate Lib/site-packages/ directory
    New-Item -ItemType Directory -Force -Path $SitePackagesDir | Out-Null

    # Restore requirements.txt
    $BackedReq = Join-Path $BackupDir "requirements.txt"
    if (Test-Path $BackedReq) {
        Copy-Item -Path $BackedReq -Destination $PythonDestDir -Force
    }

    # Restore all custom *.pth files to Lib/site-packages
    Get-ChildItem -Path $BackupDir -Filter "*.pth" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $SitePackagesDir -Force
    }

    # Ensure PIME.pth exists in Lib/site-packages with correct relative path
    $PimePthFile = Join-Path $SitePackagesDir "PIME.pth"
    if (-not (Test-Path $PimePthFile)) {
        $PimePthContent = "# PIME: add parent python project directory to sys.path`r`n../../..`r`n"
        [System.IO.File]::WriteAllText($PimePthFile, $PimePthContent, $Utf8NoBom)
    } else {
        $PthText = [System.IO.File]::ReadAllText($PimePthFile)
        if ($PthText -match '(?m)^\.\.\s*$') {
            Write-Host "Migrating relative path in PIME.pth from '..' to '../../..' for site-packages..."
            $PthText = $PthText -replace '(?m)^\.\.\s*$', '../../..'
            [System.IO.File]::WriteAllText($PimePthFile, $PthText, $Utf8NoBom)
        }
    }

    # Safely edit python3*._pth to uncomment 'import site' without adding a BOM
    $PthFile = Get-ChildItem -Path $PythonDestDir -Filter "python3*._pth" | Select-Object -First 1
    if ($PthFile) {
        Write-Host "Enabling 'import site' in $($PthFile.Name)..."
        $PthContent = [System.IO.File]::ReadAllText($PthFile.FullName)
        if ($PthContent -match '#\s*import site') {
            $PthContent = $PthContent -replace '#\s*import site', 'import site'
        } elseif ($PthContent -notmatch '(?m)^import site\s*$') {
            $PthContent = $PthContent.TrimEnd() + "`r`nimport site`r`n"
        }
        [System.IO.File]::WriteAllText($PthFile.FullName, $PthContent, $Utf8NoBom)
    }

    # If requirements.txt exists, install third-party packages into Lib/site-packages
    if (Test-Path $ReqFile) {
        Write-Host "Installing third-party packages from requirements.txt into Lib\site-packages..."
        $GetPipScript = Join-Path $TempDir "get-pip.py"
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPipScript

        $PythonExe = Join-Path $PythonDestDir "python.exe"
        & $PythonExe $GetPipScript --no-warn-script-location
        & $PythonExe -m pip install --target $SitePackagesDir -r $ReqFile

        Write-Host "Uninstalling pip/setuptools/wheel and cleaning up metadata..."
        & $PythonExe -m pip uninstall -y pip setuptools wheel
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $PythonDestDir "Scripts")
        Get-ChildItem -Path $SitePackagesDir -Directory -Filter "*.dist-info" -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        # Prune test directories packaged with pure wheels
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $SitePackagesDir "tornado\test")
    }

    # =========================================================================
    # STEP 4: Update Node.js Production Modules
    # =========================================================================
    Write-Host "`n[4/6] Updating Node.js modules in $NodeDestDir..."
    $NpmCliJs = Join-Path $NodeExtractDir "node-v$NodeVersion-win-x86\node_modules\npm\bin\npm-cli.js"
    Push-Location $NodeDestDir
    try {
        & ".\node.exe" $NpmCliJs install --production
    }
    finally {
        Pop-Location
    }

    # Clean up any accidental self-referencing links or build artifacts
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $NodeDestDir "node_modules\nime-server")

    # =========================================================================
    # STEP 5: Clean Up Bytecode and Cache Files
    # =========================================================================
    Write-Host "`n[5/6] Purging all __pycache__ directories and .pyc files..."
    $PythonRoot = Join-Path $PimeRoot "python"
    Get-ChildItem -Path $PythonRoot -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $PythonRoot -Recurse -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue

    # =========================================================================
    # STEP 6: Stage All Updated and Deleted Files in Git
    #
    # 'git add -A' inside the node and python directories automatically:
    #   - Stages newly added files (new .pyd binaries, new package files)
    #   - Stages modified binaries and code
    #   - Stages deleted obsolete files (equivalent to 'git rm')
    # Unrelated files outside of node/ and python/ remain untouched.
    # =========================================================================
    if ($StageGit) {
        Write-Host "`n[6/6] Staging updated runtime files in git (git add -A)..."
        Push-Location $PimeRoot
        try {
            & git add -A (Join-Path $PimeRoot "node") (Join-Path $PimeRoot "python")
        }
        finally {
            Pop-Location
        }
    }

    Write-Host "`n========================================================"
    Write-Host " Runtimes update completed successfully!"
    Write-Host "========================================================"
}
finally {
    Write-Host "Cleaning up temporary downloads in $TempDir..."
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $TempDir
}

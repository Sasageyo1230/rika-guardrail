# Rika Phase 3.3 Diagnostic Script
param([switch]$Verbose)

$ScriptDir = $PSScriptRoot
$Phase33Root = Split-Path -Path $ScriptDir -Parent
$RikaRoot = Split-Path -Path $Phase33Root -Parent

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🔍 Rika Phase 3.3 - System Diagnostic" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "📋 System Information:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "  • PowerShell Version: $($PSVersionTable.PSVersion)" -ForegroundColor White

# Check virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Host "  • Virtual Environment: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "  • Virtual Environment: Not active" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🛠️ Tool Versions:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Check Node.js
try {
    $nodeVersion = node --version 2>$null
    Write-Host "  • Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  • Node.js: Not found" -ForegroundColor Yellow
}

# Check Python
try {
    $pythonVersion = python --version 2>$null
    Write-Host "  • Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  • Python: Not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚨 Activation Reference Scan:" -ForegroundColor Red
Write-Host "----------------------------------------" -ForegroundColor Gray

$foundReferences = 0

# Search all PowerShell files
Get-ChildItem -Path $RikaRoot -Recurse -Filter "*.ps1" -ErrorAction SilentlyContinue | ForEach-Object {
    $file = $_
    try {
        $content = Get-Content -Path $file.FullName -ErrorAction SilentlyContinue
        if ($content) {
            $lineNumber = 0
            $content | ForEach-Object {
                $lineNumber++
                if ($_ -match "Activate\.ps1") {
                    Write-Host "    File: $($file.FullName.Replace($RikaRoot, '.')):$lineNumber" -ForegroundColor Yellow
                    Write-Host "    Line: $($_.Trim())" -ForegroundColor Gray
                    $foundReferences++
                }
            }
        }
    } catch {
        # Skip files that can't be read
    }
}

if ($foundReferences -eq 0) {
    Write-Host "  ✓ No Activate.ps1 references found in repository!" -ForegroundColor Green
} else {
    Write-Host "  ✗ Found $foundReferences Activate.ps1 references" -ForegroundColor Red
}

Write-Host ""
Write-Host "📄 Script Verification:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$requiredScripts = @("setup.ps1", "start-dev.ps1", "start-prod.ps1", "test.ps1", "diagnose.ps1")
$allScriptsFound = $true

$requiredScripts | ForEach-Object {
    $scriptPath = Join-Path -Path $ScriptDir -ChildPath $_
    if (Test-Path $scriptPath) {
        $fileSize = (Get-Item $scriptPath).Length
        Write-Host "  ✓ $_ ($fileSize bytes)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $_ (missing)" -ForegroundColor Red
        $allScriptsFound = $false
    }
}

Write-Host ""
Write-Host "🔧 Service Folders:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$serviceFolders = @("core", "overseer", "great_sage", "research_vault", "ui")
$serviceFolders | ForEach-Object {
    $folderPath = Join-Path -Path $RikaRoot -ChildPath $_
    if (Test-Path $folderPath) {
        Write-Host "  ✓ $_/" -ForegroundColor Green
    } else {
        Write-Host "  - $_/ (not found)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan

if ($foundReferences -eq 0 -and $allScriptsFound) {
    Write-Host "🎉 All diagnostic checks passed!" -ForegroundColor Green
    Write-Host "  • No venv activation references found" -ForegroundColor Green
    Write-Host "  • All required scripts present" -ForegroundColor Green
    Write-Host "  • Ready to run setup and start services" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Diagnostic issues found:" -ForegroundColor Red
    if ($foundReferences -gt 0) {
        Write-Host "  • $foundReferences venv activation references found" -ForegroundColor Red
    }
    if (-not $allScriptsFound) {
        Write-Host "  • Some required scripts missing" -ForegroundColor Red
    }
    exit 1
}

Write-Host "======================================================================" -ForegroundColor Cyan
# Rika Phase 3.4 Comprehensive Test Suite - PowerShell 5.1 Compatible
# Tests all components of the system

param(
    [switch]$SkipUI,
    [switch]$SkipAPI,
    [switch]$SkipIntegration,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# ASCII-safe status indicators
$CHECK = "[OK]"
$ERR = "[ERROR]"
$WARN = "[WARNING]"
$INFO = "[INFO]"
$START = "[START]"
$TEST = "[TEST]"

function Write-Status {
    param($Message, $Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Type $Message"
}

function Test-Endpoint {
    param($Url, $Name, $ExpectedStatus = 200)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Status "$Name endpoint test passed" $CHECK
            return $true
        } else {
            Write-Status "$Name endpoint returned status $($response.StatusCode), expected $ExpectedStatus" $ERR
            return $false
        }
    } catch {
        Write-Status "$Name endpoint test failed: $($_.Exception.Message)" $ERR
        return $false
    }
}

function Test-JsonEndpoint {
    param($Url, $Name, $RequiredFields = @())
    
    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec 10 -ErrorAction Stop
        
        foreach ($field in $RequiredFields) {
            if (-not $response.$field) {
                Write-Status "$Name missing required field: $field" $ERR
                return $false
            }
        }
        
        Write-Status "$Name JSON endpoint test passed" $CHECK
        return $true
    } catch {
        Write-Status "$Name JSON endpoint test failed: $($_.Exception.Message)" $ERR
        return $false
    }
}

function Start-TestServer {
    param($Command, $Port, $Name)
    
    Write-Status "Starting $Name for testing..." $INFO
    
    $job = Start-Job -ScriptBlock {
        param($cmd, $workingDir)
        Set-Location $workingDir
        Invoke-Expression $cmd
    } -ArgumentList $Command, (Get-Location).Path
    
    # Wait for server to start
    $attempts = 0
    $maxAttempts = 30
    
    while ($attempts -lt $maxAttempts) {
        try {
            $connection = New-Object System.Net.Sockets.TcpClient
            $connection.Connect("localhost", $Port)
            $connection.Close()
            Write-Status "$Name started successfully" $CHECK
            return $job
        } catch {
            Start-Sleep -Seconds 1
            $attempts++
        }
    }
    
    Write-Status "$Name failed to start within $maxAttempts seconds" $ERR
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -ErrorAction SilentlyContinue
    return $null
}

$testResults = @{
    "Python Tests" = @()
    "API Tests" = @()
    "UI Tests" = @()
    "Integration Tests" = @()
}

Write-Status "Starting Rika Phase 3.4 Comprehensive Test Suite..." $START

# Auto-detect virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Status "Using virtual environment: $env:VIRTUAL_ENV" $CHECK
    $pythonCmd = "python"
} elseif (Test-Path "venv\Scripts\python.exe") {
    Write-Status "Using local virtual environment" $CHECK
    $pythonCmd = "venv\Scripts\python.exe"
} else {
    Write-Status "Using system Python" $INFO
    $pythonCmd = "python"
}

# 1. Python Environment Tests
Write-Status "Running Python environment tests..." $TEST

# Test Python version
try {
    $pythonVersion = & $pythonCmd --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 3 -and $minor -ge 8) {
            Write-Status "Python version check passed: $pythonVersion" $CHECK
            $testResults["Python Tests"] += "Python version: PASS"
        } else {
            Write-Status "Python version too old: $pythonVersion (need 3.8+)" $ERR
            $testResults["Python Tests"] += "Python version: FAIL"
        }
    }
} catch {
    Write-Status "Python version check failed" $ERR
    $testResults["Python Tests"] += "Python version: FAIL"
}

# Test required Python packages
$requiredPackages = @("fastapi", "uvicorn", "pydantic", "anthropic", "openai", "httpx")
foreach ($package in $requiredPackages) {
    try {
        & $pythonCmd -c "import $package" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Package $package import test passed" $CHECK
            $testResults["Python Tests"] += "$package import: PASS"
        } else {
            Write-Status "Package $package import test failed" $ERR
            $testResults["Python Tests"] += "$package import: FAIL"
        }
    } catch {
        Write-Status "Package $package import test failed" $ERR
        $testResults["Python Tests"] += "$package import: FAIL"
    }
}

# 2. Core API Tests
if (-not $SkipAPI) {
    Write-Status "Running Core API tests..." $TEST
    
    # Start API server for testing
    $apiCommand = "cd core && $pythonCmd -m uvicorn main:app --host 0.0.0.0 --port 5318"  # Use different port for testing
    $apiJob = Start-TestServer $apiCommand 5318 "Core API (test)"
    
    if ($apiJob) {
        # Test basic endpoints
        $apiTests = @(
            @{ Url = "http://localhost:5318/health"; Name = "Health check" },
            @{ Url = "http://localhost:5318/"; Name = "Root endpoint" },
            @{ Url = "http://localhost:5318/docs"; Name = "API documentation" }
        )
        
        foreach ($test in $apiTests) {
            $result = Test-Endpoint $test.Url $test.Name
            $testResults["API Tests"] += "$($test.Name): $(if ($result) { 'PASS' } else { 'FAIL' })"
        }
        
        # Test chat endpoint structure
        try {
            $chatResponse = Invoke-RestMethod -Uri "http://localhost:5318/chat/" -Method POST -ContentType "application/json" -Body '{"session_id":"test","message":"hello","stream":false}' -TimeoutSec 10
            if ($chatResponse) {
                Write-Status "Chat endpoint structure test passed" $CHECK
                $testResults["API Tests"] += "Chat endpoint: PASS"
            } else {
                Write-Status "Chat endpoint returned empty response" $ERR
                $testResults["API Tests"] += "Chat endpoint: FAIL"
            }
        } catch {
            Write-Status "Chat endpoint test failed: $($_.Exception.Message)" $ERR
            $testResults["API Tests"] += "Chat endpoint: FAIL"
        }
        
        # Test UI patch endpoint
        try {
            $patchResponse = Invoke-RestMethod -Uri "http://localhost:5318/ui/patches" -TimeoutSec 10
            Write-Status "UI patch endpoint test passed" $CHECK
            $testResults["API Tests"] += "UI patch endpoint: PASS"
        } catch {
            Write-Status "UI patch endpoint test failed: $($_.Exception.Message)" $ERR
            $testResults["API Tests"] += "UI patch endpoint: FAIL"
        }
        
        # Clean up API server
        Stop-Job -Job $apiJob -ErrorAction SilentlyContinue
        Remove-Job -Job $apiJob -ErrorAction SilentlyContinue
    } else {
        Write-Status "Could not start API server for testing" $ERR
        $testResults["API Tests"] += "Server startup: FAIL"
    }
} else {
    Write-Status "Skipping Core API tests" $INFO
}

# 3. UI Tests
if (-not $SkipUI) {
    Write-Status "Running Atlas UI tests..." $TEST
    
    Push-Location "ui"
    try {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Status "Installing UI dependencies for testing..." $INFO
            npm install
        }
        
        # TypeScript compilation test
        Write-Status "Running TypeScript compilation test..." $TEST
        npm run typecheck
        if ($LASTEXITCODE -eq 0) {
            Write-Status "TypeScript compilation test passed" $CHECK
            $testResults["UI Tests"] += "TypeScript compilation: PASS"
        } else {
            Write-Status "TypeScript compilation test failed" $ERR
            $testResults["UI Tests"] += "TypeScript compilation: FAIL"
        }
        
        # ESLint test
        Write-Status "Running ESLint test..." $TEST
        npm run lint
        if ($LASTEXITCODE -eq 0) {
            Write-Status "ESLint test passed" $CHECK
            $testResults["UI Tests"] += "ESLint: PASS"
        } else {
            Write-Status "ESLint test failed" $ERR
            $testResults["UI Tests"] += "ESLint: FAIL"
        }
        
        # Build test
        Write-Status "Running build test..." $TEST
        npm run build
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Build test passed" $CHECK
            $testResults["UI Tests"] += "Build: PASS"
            
            # Check if build artifacts exist
            if (Test-Path "dist\index.html") {
                Write-Status "Build artifacts check passed" $CHECK
                $testResults["UI Tests"] += "Build artifacts: PASS"
            } else {
                Write-Status "Build artifacts check failed" $ERR
                $testResults["UI Tests"] += "Build artifacts: FAIL"
            }
        } else {
            Write-Status "Build test failed" $ERR
            $testResults["UI Tests"] += "Build: FAIL"
        }
        
    } finally {
        Pop-Location
    }
} else {
    Write-Status "Skipping Atlas UI tests" $INFO
}

# 4. Integration Tests
if (-not $SkipIntegration) {
    Write-Status "Running integration tests..." $TEST
    
    # Start both servers for integration testing
    $apiCommand = "cd core && $pythonCmd -m uvicorn main:app --host 0.0.0.0 --port 5319"
    $apiJob = Start-TestServer $apiCommand 5319 "Core API (integration)"
    
    if ($apiJob) {
        Push-Location "ui"
        try {
            # Start UI server
            $uiJob = Start-Job -ScriptBlock {
                param($workingDir)
                Set-Location (Join-Path $workingDir "ui")
                $env:VITE_API_BASE_URL = "http://localhost:5319"
                npm run preview -- --port 5174
            } -ArgumentList (Get-Location).Parent.Path
            
            Start-Sleep -Seconds 10  # Give UI time to start
            
            # Test UI loads
            $result = Test-Endpoint "http://localhost:5174" "UI server"
            $testResults["Integration Tests"] += "UI server: $(if ($result) { 'PASS' } else { 'FAIL' })"
            
            # Test API connectivity from UI perspective
            $result = Test-Endpoint "http://localhost:5319/health" "API connectivity"
            $testResults["Integration Tests"] += "API connectivity: $(if ($result) { 'PASS' } else { 'FAIL' })"
            
            # Clean up
            Stop-Job -Job $uiJob -ErrorAction SilentlyContinue
            Remove-Job -Job $uiJob -ErrorAction SilentlyContinue
            
        } finally {
            Pop-Location
        }
        
        Stop-Job -Job $apiJob -ErrorAction SilentlyContinue
        Remove-Job -Job $apiJob -ErrorAction SilentlyContinue
    } else {
        Write-Status "Could not start API server for integration testing" $ERR
        $testResults["Integration Tests"] += "Server startup: FAIL"
    }
} else {
    Write-Status "Skipping integration tests" $INFO
}

# 5. Configuration Tests
Write-Status "Running configuration tests..." $TEST

# Test .env file
if (Test-Path ".env") {
    Write-Status ".env file exists" $CHECK
    $testResults["Integration Tests"] += ".env file: PASS"
} else {
    Write-Status ".env file missing" $ERR
    $testResults["Integration Tests"] += ".env file: FAIL"
}

# Test config.json
if (Test-Path "config\config.json") {
    try {
        $config = Get-Content "config\config.json" | ConvertFrom-Json
        if ($config.llm -and $config.memory -and $config.tools) {
            Write-Status "config.json structure test passed" $CHECK
            $testResults["Integration Tests"] += "config.json: PASS"
        } else {
            Write-Status "config.json missing required sections" $ERR
            $testResults["Integration Tests"] += "config.json: FAIL"
        }
    } catch {
        Write-Status "config.json is invalid JSON" $ERR
        $testResults["Integration Tests"] += "config.json: FAIL"
    }
} else {
    Write-Status "config.json missing" $ERR
    $testResults["Integration Tests"] += "config.json: FAIL"
}

# Print test results summary
Write-Status "" $INFO
Write-Status "Test Results Summary" $START
Write-Status "===================" $INFO

$totalTests = 0
$passedTests = 0

foreach ($category in $testResults.Keys) {
    Write-Status "" $INFO
    Write-Status "$category" $INFO
    Write-Status ("-" * $category.Length) $INFO
    
    foreach ($test in $testResults[$category]) {
        $totalTests++
        if ($test.EndsWith("PASS")) {
            $passedTests++
            Write-Status "  $test" $CHECK
        } else {
            Write-Status "  $test" $ERR
        }
    }
}

Write-Status "" $INFO
Write-Status "Overall Results: $passedTests/$totalTests tests passed" $INFO

if ($passedTests -eq $totalTests) {
    Write-Status "All tests passed! Rika Phase 3.4 is ready for use." $CHECK
    exit 0
} elseif ($passedTests -gt ($totalTests * 0.8)) {
    Write-Status "Most tests passed. System should be functional with minor issues." $WARN
    exit 0
} else {
    Write-Status "Multiple test failures detected. Please review and fix issues." $ERR
    exit 1
}
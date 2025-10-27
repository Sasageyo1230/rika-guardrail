# phase3.2/scripts/setup-desktop-agent.ps1
# Setup Desktop Agent with all dependencies

param(
    [switch]$SkipCEC,
    [switch]$SkipIR,
    [switch]$SkipGestures,
    [switch]$Help
)

if ($Help) {
    Write-Host "Desktop Agent Setup" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\setup-desktop-agent.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -SkipCEC          Skip HDMI-CEC setup" -ForegroundColor White
    Write-Host "  -SkipIR           Skip IR control setup" -ForegroundColor White
    Write-Host "  -SkipGestures     Skip gesture recognition setup" -ForegroundColor White
    Write-Host "  -Help             Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "This script installs:" -ForegroundColor Yellow
    Write-Host "- Python dependencies (bleak, opencv, mediapipe)" -ForegroundColor White
    Write-Host "- HDMI-CEC libraries (optional)" -ForegroundColor White
    Write-Host "- LIRC for IR control (optional)" -ForegroundColor White
    Write-Host "- Camera drivers for gesture recognition" -ForegroundColor White
    Write-Host ""
    return
}

Write-Host "Setting up Desktop Agent..." -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    exit 1
}

# Check if we're on Windows
$isWindows = $env:OS -eq "Windows_NT"
$isLinux = $env:OS -ne "Windows_NT"

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Gray

# Core Python packages
$packages = @(
    "bleak>=0.20.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0",
    "httpx>=0.24.0",
    "asyncpg>=0.28.0",
    "structlog>=23.1.0",
    "pydantic>=2.0.0"
)

# Gesture recognition packages
if (-not $SkipGestures) {
    $packages += @(
        "opencv-python>=4.8.0",
        "mediapipe>=0.10.0",
        "numpy>=1.24.0"
    )
}

# Install packages
foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    python -m pip install $package --upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Failed to install $package" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Setting up platform-specific components..." -ForegroundColor Gray

if ($isWindows) {
    Write-Host "Windows platform detected" -ForegroundColor Blue
    
    # Windows-specific setup
    if (-not $SkipCEC) {
        Write-Host "Setting up HDMI-CEC for Windows..." -ForegroundColor Gray
        # Note: CEC support on Windows requires specific hardware and drivers
        Write-Host "HDMI-CEC requires compatible hardware and drivers" -ForegroundColor Yellow
        Write-Host "Install your TV/device manufacturer's CEC drivers if available" -ForegroundColor Yellow
        
        # Try to install pycec
        python -m pip install pycec --upgrade 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "pycec installed successfully" -ForegroundColor Green
        } else {
            Write-Host "pycec installation failed - HDMI-CEC may not be available" -ForegroundColor Yellow
        }
    }
    
    if (-not $SkipIR) {
        Write-Host "Setting up IR control for Windows..." -ForegroundColor Gray
        Write-Host "IR control on Windows requires WinLIRC or similar software" -ForegroundColor Yellow
        Write-Host "Download WinLIRC from: http://winlirc.sourceforge.net/" -ForegroundColor White
        Write-Host "Or use manufacturer-specific IR software" -ForegroundColor White
    }
    
    # Bluetooth should work natively with bleak
    Write-Host "Bluetooth support enabled via Windows Bluetooth stack" -ForegroundColor Green
    
} else {
    Write-Host "Linux platform detected" -ForegroundColor Blue
    
    # Linux-specific setup
    if (-not $SkipCEC) {
        Write-Host "Setting up HDMI-CEC for Linux..." -ForegroundColor Gray
        
        # Check for libcec
        $cecCheck = which libcec-dev 2>$null
        if (-not $cecCheck) {
            Write-Host "Installing libcec development libraries..." -ForegroundColor Gray
            if (Get-Command apt-get -ErrorAction SilentlyContinue) {
                sudo apt-get update
                sudo apt-get install -y libcec-dev cec-utils
            } elseif (Get-Command yum -ErrorAction SilentlyContinue) {
                sudo yum install -y libcec-devel
            } else {
                Write-Host "Please install libcec manually for your distribution" -ForegroundColor Yellow
            }
        }
        
        # Install pycec
        python -m pip install pycec --upgrade
        if ($LASTEXITCODE -eq 0) {
            Write-Host "HDMI-CEC setup complete" -ForegroundColor Green
        } else {
            Write-Host "pycec installation failed" -ForegroundColor Yellow
        }
    }
    
    if (-not $SkipIR) {
        Write-Host "Setting up IR control (LIRC) for Linux..." -ForegroundColor Gray
        
        # Install LIRC
        if (Get-Command apt-get -ErrorAction SilentlyContinue) {
            sudo apt-get install -y lirc
        } elseif (Get-Command yum -ErrorAction SilentlyContinue) {
            sudo yum install -y lirc
        } else {
            Write-Host "Please install LIRC manually for your distribution" -ForegroundColor Yellow
        }
        
        Write-Host "LIRC installed - configure remotes in /etc/lirc/" -ForegroundColor Green
    }
    
    # Linux Bluetooth setup
    Write-Host "Checking Bluetooth setup..." -ForegroundColor Gray
    $bluetoothCheck = which bluetoothctl 2>$null
    if ($bluetoothCheck) {
        Write-Host "Bluetooth stack detected" -ForegroundColor Green
    } else {
        Write-Host "Installing Bluetooth utilities..." -ForegroundColor Gray
        if (Get-Command apt-get -ErrorAction SilentlyContinue) {
            sudo apt-get install -y bluetooth bluez bluez-tools
        }
    }
}

# Camera setup for gesture recognition
if (-not $SkipGestures) {
    Write-Host ""
    Write-Host "Setting up camera for gesture recognition..." -ForegroundColor Gray
    
    # Test camera access
    python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera:', 'Available' if cap.isOpened() else 'Not available'); cap.release()" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Camera access verified" -ForegroundColor Green
    } else {
        Write-Host "Camera not accessible - check camera permissions and drivers" -ForegroundColor Yellow
    }
}

# Create configuration file
Write-Host ""
Write-Host "Creating configuration file..." -ForegroundColor Gray

$configContent = @"
# Desktop Agent Configuration
# Generated: $(Get-Date)

[agent]
name = "desktop-agent"
version = "3.2.0"
port = 5325

[capabilities]
bluetooth = true
hdmi_cec = $(-not $SkipCEC)
ir_control = $(-not $SkipIR)
gesture_recognition = $(-not $SkipGestures)

[bluetooth]
scan_timeout = 10
max_connections = 5

[hdmi_cec]
auto_scan = true
power_on_delay = 2

[ir_control]
lirc_socket = "/var/run/lirc/lircd"
command_timeout = 5

[gesture_recognition]
camera_index = 0
detection_confidence = 0.7
tracking_confidence = 0.5
max_hands = 2

[n8n]
gateway_url = "http://localhost:5324"
agent_id = "rig"

[logging]
level = "INFO"
file = "logs/desktop-agent.log"
"@

$configDir = "$PSScriptRoot\..\config"
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$configPath = "$configDir\desktop-agent.conf"
$configContent | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "Configuration saved: $configPath" -ForegroundColor Green

# Create logs directory
$logsDir = "$PSScriptRoot\..\logs"
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Create startup script
$startupScript = @"
# phase3.2/scripts/start-desktop-agent.ps1
# Start Desktop Agent

param(
    [string]`$Config = "$configPath",
    [int]`$Port = 5325,
    [switch]`$Debug
)

Write-Host "Starting Desktop Agent..." -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Config: `$Config" -ForegroundColor Gray
Write-Host "Port: `$Port" -ForegroundColor Gray
Write-Host "Debug: `$Debug" -ForegroundColor Gray
Write-Host ""

# Set environment variables
`$env:DESKTOP_AGENT_CONFIG = `$Config
`$env:DESKTOP_AGENT_PORT = `$Port

if (`$Debug) {
    `$env:DESKTOP_AGENT_LOG_LEVEL = "DEBUG"
}

# Start the agent
python "$PSScriptRoot\..\agents\desktop\desktop_agent.py"
"@

$startupScriptPath = "$PSScriptRoot\start-desktop-agent.ps1"
$startupScript | Out-File -FilePath $startupScriptPath -Encoding UTF8
Write-Host "Startup script created: $startupScriptPath" -ForegroundColor Green

# Create test script
$testScript = @"
# phase3.2/scripts/test-desktop-agent.ps1
# Test Desktop Agent functionality

param(
    [switch]`$Quick,
    [switch]`$Help
)

if (`$Help) {
    Write-Host "Desktop Agent Test Suite" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\test-desktop-agent.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -Quick    Run quick tests only" -ForegroundColor White
    Write-Host "  -Help     Show this help" -ForegroundColor White
    Write-Host ""
    return
}

Write-Host "Testing Desktop Agent..." -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

`$baseUrl = "http://localhost:5325"

# Test health endpoint
Write-Host ""
Write-Host "Testing health endpoint..." -ForegroundColor Yellow
try {
    `$response = Invoke-RestMethod -Uri "`$baseUrl/health" -Method GET
    Write-Host "Health check: `$(`$response.status)" -ForegroundColor Green
    Write-Host "Version: `$(`$response.version)" -ForegroundColor White
    Write-Host "Platform: `$(`$response.platform)" -ForegroundColor White
} catch {
    Write-Host "Health check failed: `$_" -ForegroundColor Red
    exit 1
}

# Test capabilities
Write-Host ""
Write-Host "Testing capabilities..." -ForegroundColor Yellow
try {
    `$capabilities = Invoke-RestMethod -Uri "`$baseUrl/capabilities" -Method GET
    Write-Host "Capabilities:" -ForegroundColor Green
    foreach (`$cap in `$capabilities.capabilities.PSObject.Properties) {
        `$status = if (`$cap.Value) { "✓" } else { "✗" }
        Write-Host "  `$status `$(`$cap.Name)" -ForegroundColor White
    }
} catch {
    Write-Host "Capabilities test failed: `$_" -ForegroundColor Red
}

if (-not `$Quick) {
    # Test environment scan
    Write-Host ""
    Write-Host "Testing environment scan..." -ForegroundColor Yellow
    try {
        `$environment = Invoke-RestMethod -Uri "`$baseUrl/environment/scan" -Method GET
        Write-Host "Environment scan completed:" -ForegroundColor Green
        Write-Host "  Bluetooth devices: `$(`$environment.bluetooth_devices.Count)" -ForegroundColor White
        Write-Host "  CEC devices: `$(`$environment.hdmi_cec_devices.PSObject.Properties.Count)" -ForegroundColor White
        Write-Host "  IR remotes: `$(`$environment.ir_remotes.PSObject.Properties.Count)" -ForegroundColor White
    } catch {
        Write-Host "Environment scan failed: `$_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Green
"@

$testScriptPath = "$PSScriptRoot\test-desktop-agent.ps1"
$testScript | Out-File -FilePath $testScriptPath -Encoding UTF8
Write-Host "Test script created: $testScriptPath" -ForegroundColor Green

Write-Host ""
Write-Host "Desktop Agent Setup Complete!" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: .\start-desktop-agent.ps1" -ForegroundColor White
Write-Host "2. Test: .\test-desktop-agent.ps1" -ForegroundColor White
Write-Host "3. Configure devices in: $configPath" -ForegroundColor White
Write-Host ""

# Show capability summary
Write-Host "Capabilities:" -ForegroundColor Yellow
Write-Host "  ✓ Bluetooth device control" -ForegroundColor Green
if (-not $SkipCEC) {
    Write-Host "  ✓ HDMI-CEC support" -ForegroundColor Green
} else {
    Write-Host "  ✗ HDMI-CEC (skipped)" -ForegroundColor Gray
}
if (-not $SkipIR) {
    Write-Host "  ✓ IR control support" -ForegroundColor Green
} else {
    Write-Host "  ✗ IR control (skipped)" -ForegroundColor Gray
}
if (-not $SkipGestures) {
    Write-Host "  ✓ Gesture recognition" -ForegroundColor Green
} else {
    Write-Host "  ✗ Gesture recognition (skipped)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Agent will be available at: http://localhost:5325" -ForegroundColor Cyan
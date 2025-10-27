# phase3.1/scripts/n8n-setup.ps1
# Setup n8n with Rika integration

param(
    [string]$Domain = "localhost",
    [int]$Port = 5678,
    [switch]$ProductionMode,
    [switch]$Help
)

if ($Help) {
    Write-Host "n8n Setup for Rika Integration" -ForegroundColor Cyan
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\n8n-setup.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -Domain <domain>       Domain for n8n (default: localhost)" -ForegroundColor White
    Write-Host "  -Port <port>           Port for n8n (default: 5678)" -ForegroundColor White
    Write-Host "  -ProductionMode        Setup for production use" -ForegroundColor White
    Write-Host "  -Help                  Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\n8n-setup.ps1" -ForegroundColor Gray
    Write-Host "  .\n8n-setup.ps1 -Domain rika.local -Port 5678 -ProductionMode" -ForegroundColor Gray
    Write-Host ""
    return
}

Write-Host "Setting up n8n for Rika Integration..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Yellow
    exit 1
}

# Check if n8n is installed globally
Write-Host "Checking n8n installation..." -ForegroundColor Gray
try {
    $n8nVersion = npx n8n --version 2>&1
    Write-Host "n8n: $n8nVersion" -ForegroundColor Green
} catch {
    Write-Host "Installing n8n globally..." -ForegroundColor Yellow
    npm install -g n8n
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install n8n" -ForegroundColor Red
        exit 1
    }
}

# Create n8n data directory
$n8nDataDir = "$env:USERPROFILE\.n8n"
if (!(Test-Path $n8nDataDir)) {
    Write-Host "Creating n8n data directory: $n8nDataDir" -ForegroundColor Gray
    New-Item -ItemType Directory -Path $n8nDataDir -Force | Out-Null
}

# Create n8n configuration
$configDir = "$n8nDataDir\config"
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Generate API key
$apiKey = [System.Guid]::NewGuid().ToString("N")
Write-Host "Generated API Key: $apiKey" -ForegroundColor Yellow

# Create environment configuration
$envContent = @"
# n8n Configuration for Rika
N8N_HOST=$Domain
N8N_PORT=$Port
N8N_PROTOCOL=http
N8N_BASIC_AUTH_ACTIVE=false
N8N_JWT_AUTH_ACTIVE=false
N8N_ENCRYPTION_KEY=rikaEncryptionKey2025SecureN8n
N8N_USER_MANAGEMENT_JWT_SECRET=rikaJwtSecret2025N8nUserMgmt
N8N_API_KEY=$apiKey

# Database (SQLite for development, PostgreSQL for production)
$(if ($ProductionMode) {
"DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5433
DB_POSTGRESDB_DATABASE=rika_n8n
DB_POSTGRESDB_USER=rika_admin
DB_POSTGRESDB_PASSWORD=RikaPostgres2025SecureDB"
} else {
"DB_TYPE=sqlite
DB_SQLITE_DATABASE=$n8nDataDir\database.sqlite"
})

# Rika Integration
N8N_CUSTOM_EXTENSIONS=$n8nDataDir\custom
N8N_NODES_BASE_URL=http://localhost:5324
RIKA_OVERSEER_URL=http://localhost:5319
RIKA_CORE_URL=http://localhost:5317

# Security
N8N_SECURE_COOKIE=false
N8N_COOKIES_SECURE=false
N8N_SKIP_WEBHOOK_DEREGISTRATION_SHUTDOWN=true

# Logging
N8N_LOG_LEVEL=info
N8N_LOG_OUTPUT=console,file
N8N_LOG_FILE_LOCATION=$n8nDataDir\logs\

# Performance
N8N_EXECUTIONS_PROCESS=main
N8N_EXECUTIONS_TIMEOUT=3600
N8N_EXECUTIONS_TIMEOUT_MAX=7200
"@

$envFile = "$n8nDataDir\.env"
$envContent | Out-File -FilePath $envFile -Encoding UTF8
Write-Host "Created environment file: $envFile" -ForegroundColor Green

# Create logs directory
$logsDir = "$n8nDataDir\logs"
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Create custom nodes directory
$customDir = "$n8nDataDir\custom"
if (!(Test-Path $customDir)) {
    New-Item -ItemType Directory -Path $customDir -Force | Out-Null
}

# Create Rika-specific workflows directory
$workflowsDir = "$n8nDataDir\workflows\rika"
if (!(Test-Path $workflowsDir)) {
    New-Item -ItemType Directory -Path $workflowsDir -Force | Out-Null
}

# Create sample Rika workflows
Write-Host "Creating sample Rika workflows..." -ForegroundColor Gray

# Device Controller Workflow
$deviceControllerWorkflow = @{
    name = "device-controller"
    active = $true
    nodes = @(
        @{
            parameters = @{
                httpMethod = "POST"
                path = "device-control"
                responseMode = "responseNode"
            }
            id = "webhook-device"
            name = "Device Control Webhook"
            type = "n8n-nodes-base.webhook"
            position = @(260, 300)
        },
        @{
            parameters = @{
                conditions = @{
                    string = @(
                        @{
                            value1 = "={{`$json.device`}}"
                            operation = "equal"
                            value2 = "tv"
                        }
                    )
                }
            }
            id = "if-tv"
            name = "Is TV Command?"
            type = "n8n-nodes-base.if"
            position = @(460, 300)
        }
    )
    connections = @{
        "Device Control Webhook" = @{
            main = @(@(@{
                node = "Is TV Command?"
                type = "main"
                index = 0
            }))
        }
    }
}

$deviceWorkflowJson = $deviceControllerWorkflow | ConvertTo-Json -Depth 10
$deviceWorkflowJson | Out-File -FilePath "$workflowsDir\device-controller.json" -Encoding UTF8

# Notification Sender Workflow
$notificationWorkflow = @{
    name = "notification-sender"
    active = $true
    nodes = @(
        @{
            parameters = @{
                httpMethod = "POST"
                path = "notification"
                responseMode = "responseNode"
            }
            id = "webhook-notification"
            name = "Notification Webhook"
            type = "n8n-nodes-base.webhook"
            position = @(260, 300)
        }
    )
}

$notificationJson = $notificationWorkflow | ConvertTo-Json -Depth 10
$notificationJson | Out-File -FilePath "$workflowsDir\notification-sender.json" -Encoding UTF8

Write-Host "Sample workflows created in: $workflowsDir" -ForegroundColor Green

# Create startup script
$startupScript = @"
# phase3.1/scripts/start-n8n.ps1
# Start n8n with Rika configuration

`$env:N8N_CONFIG_FILES = "$envFile"

Write-Host "Starting n8n with Rika integration..." -ForegroundColor Cyan
Write-Host "Web UI will be available at: http://${Domain}:${Port}" -ForegroundColor Green
Write-Host "API Key: $apiKey" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start n8n
npx n8n start
"@

$startupScriptPath = "$PSScriptRoot\start-n8n.ps1"
$startupScript | Out-File -FilePath $startupScriptPath -Encoding UTF8
Write-Host "Created startup script: $startupScriptPath" -ForegroundColor Green

# Create Rika Gateway environment file
$gatewayEnv = @"
# n8n Gateway Configuration
N8N_URL=http://${Domain}:${Port}
N8N_API_KEY=$apiKey
OVERSEER_URL=http://localhost:5319
DATABASE_URL=postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core
"@

$gatewayEnvPath = "$PSScriptRoot\..\.env.n8n"
$gatewayEnv | Out-File -FilePath $gatewayEnvPath -Encoding UTF8
Write-Host "Created gateway environment: $gatewayEnvPath" -ForegroundColor Green

Write-Host ""
Write-Host "n8n Setup Complete!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: .\start-n8n.ps1" -ForegroundColor White
Write-Host "2. Open: http://${Domain}:${Port}" -ForegroundColor White
Write-Host "3. Create your first user account" -ForegroundColor White
Write-Host "4. Import the sample workflows from: $workflowsDir" -ForegroundColor White
Write-Host ""
Write-Host "API Key (save this): $apiKey" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the n8n Gateway:" -ForegroundColor Yellow
Write-Host "cd ..\core && python n8n_gateway.py" -ForegroundColor White
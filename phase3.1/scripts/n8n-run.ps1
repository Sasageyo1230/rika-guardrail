# phase3.1/scripts/n8n-run.ps1
# Run n8n workflow through Rika Gateway

param(
    [Parameter(Mandatory=$true)]
    [string]$Workflow,
    [string]$InputFile,
    [string]$InputJson,
    [string[]]$Tags = @(),
    [string]$Priority = "normal",
    [string]$Agent = "manual",
    [switch]$Wait,
    [switch]$Help
)

if ($Help) {
    Write-Host "n8n Workflow Runner" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\n8n-run.ps1 -Workflow <name> [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Parameters:" -ForegroundColor Green
    Write-Host "  -Workflow <name>       Workflow name or ID (required)" -ForegroundColor White
    Write-Host "  -InputFile <file>      JSON file with input data" -ForegroundColor White
    Write-Host "  -InputJson <json>      JSON string with input data" -ForegroundColor White
    Write-Host "  -Tags <tag1,tag2>      Tags for the execution" -ForegroundColor White
    Write-Host "  -Priority <level>      Priority: low, normal, high, urgent" -ForegroundColor White
    Write-Host "  -Agent <name>          Agent identity (default: manual)" -ForegroundColor White
    Write-Host "  -Wait                  Wait for completion" -ForegroundColor White
    Write-Host "  -Help                  Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\n8n-run.ps1 -Workflow device-controller -InputJson '{\"device\":\"tv\",\"action\":\"on\"}'" -ForegroundColor Gray
    Write-Host "  .\n8n-run.ps1 -Workflow notification-sender -InputFile notification.json -Wait" -ForegroundColor Gray
    Write-Host "  .\n8n-run.ps1 -Workflow data-processor -Tags analysis,daily -Priority high" -ForegroundColor Gray
    Write-Host ""
    return
}

Write-Host "Running n8n Workflow: $Workflow" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Load gateway URL from environment
$gatewayUrl = $env:N8N_GATEWAY_URL
if (-not $gatewayUrl) {
    $gatewayUrl = "http://localhost:5324"
}

# Prepare input data
$inputData = @{}

if ($InputFile) {
    if (Test-Path $InputFile) {
        try {
            $inputData = Get-Content $InputFile | ConvertFrom-Json -AsHashtable
            Write-Host "Loaded input from: $InputFile" -ForegroundColor Green
        } catch {
            Write-Host "ERROR: Invalid JSON in file: $InputFile" -ForegroundColor Red
            Write-Host "Error: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "ERROR: Input file not found: $InputFile" -ForegroundColor Red
        exit 1
    }
}

if ($InputJson) {
    try {
        $inputData = $InputJson | ConvertFrom-Json -AsHashtable
        Write-Host "Loaded input from JSON string" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Invalid JSON string" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        exit 1
    }
}

# Prepare request payload
$payload = @{
    workflow = $Workflow
    input = $inputData
    tags = $Tags
    requester = $Agent
    priority = $Priority
}

$requestJson = $payload | ConvertTo-Json -Depth 5

Write-Host ""
Write-Host "Request Details:" -ForegroundColor Yellow
Write-Host "  Workflow: $Workflow" -ForegroundColor White
Write-Host "  Agent: $Agent" -ForegroundColor White
Write-Host "  Priority: $Priority" -ForegroundColor White
Write-Host "  Tags: $($Tags -join ', ')" -ForegroundColor White
Write-Host "  Input Keys: $($inputData.Keys -join ', ')" -ForegroundColor White
Write-Host ""

# Execute workflow
try {
    Write-Host "Sending request to: $gatewayUrl/n8n/run" -ForegroundColor Gray
    
    $response = Invoke-RestMethod -Uri "$gatewayUrl/n8n/run" -Method POST -Body $requestJson -ContentType "application/json"
    
    Write-Host "Workflow Execution Started!" -ForegroundColor Green
    Write-Host "===========================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Execution ID: $($response.execution_id)" -ForegroundColor Cyan
    Write-Host "Status: $($response.status)" -ForegroundColor White
    Write-Host "Start Time: $($response.start_time)" -ForegroundColor White
    
    if ($response.error) {
        Write-Host "Error: $($response.error)" -ForegroundColor Red
        exit 1
    }
    
    # Wait for completion if requested
    if ($Wait) {
        Write-Host ""
        Write-Host "Waiting for completion..." -ForegroundColor Yellow
        
        $executionId = $response.execution_id
        $maxWait = 300  # 5 minutes
        $pollInterval = 5
        $elapsed = 0
        
        while ($elapsed -lt $maxWait) {
            Start-Sleep $pollInterval
            $elapsed += $pollInterval
            
            try {
                $statusResponse = Invoke-RestMethod -Uri "$gatewayUrl/n8n/executions?execution_id=$executionId" -Method GET
                $executions = $statusResponse.executions
                
                if ($executions -and $executions.Count -gt 0) {
                    $execution = $executions[0]
                    $status = $execution.status
                    
                    Write-Host "Status: $status (${elapsed}s elapsed)" -ForegroundColor Gray
                    
                    if ($status -in @("success", "failed", "cancelled")) {
                        Write-Host ""
                        Write-Host "Execution Completed!" -ForegroundColor Green
                        Write-Host "===================" -ForegroundColor Green
                        Write-Host ""
                        Write-Host "Final Status: $status" -ForegroundColor $(if ($status -eq "success") { "Green" } else { "Red" })
                        Write-Host "End Time: $($execution.end_time)" -ForegroundColor White
                        
                        if ($execution.output -and $execution.output.Count -gt 0) {
                            Write-Host ""
                            Write-Host "Output:" -ForegroundColor Yellow
                            $execution.output | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor White
                        }
                        
                        if ($execution.error) {
                            Write-Host ""
                            Write-Host "Error Details:" -ForegroundColor Red
                            Write-Host $execution.error -ForegroundColor White
                            exit 1
                        }
                        
                        exit 0
                    }
                }
            } catch {
                Write-Host "Warning: Failed to get status update" -ForegroundColor Yellow
            }
        }
        
        Write-Host ""
        Write-Host "Timeout: Execution exceeded ${maxWait}s" -ForegroundColor Red
        Write-Host "Check execution status manually: $executionId" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host ""
        Write-Host "Execution started in background." -ForegroundColor Green
        Write-Host "Check status with: .\n8n-status.ps1 -ExecutionId $($response.execution_id)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to execute workflow" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        try {
            $errorDetails = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorDetails)
            $errorBody = $reader.ReadToEnd()
            Write-Host "Response: $errorBody" -ForegroundColor Red
        } catch {
            # Ignore errors reading response
        }
    }
    
    exit 1
}
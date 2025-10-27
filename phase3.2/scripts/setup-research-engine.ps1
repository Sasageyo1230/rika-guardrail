# phase3.2/scripts/setup-research-engine.ps1
# Setup Research Engine with MinIO + Qdrant

param(
    [switch]$SkipMinIO,
    [switch]$SkipQdrant,
    [switch]$DockerMode,
    [switch]$Help
)

if ($Help) {
    Write-Host "Research Engine Setup" -ForegroundColor Cyan
    Write-Host "====================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\setup-research-engine.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -SkipMinIO       Skip MinIO object storage setup" -ForegroundColor White
    Write-Host "  -SkipQdrant      Skip Qdrant vector database setup" -ForegroundColor White
    Write-Host "  -DockerMode      Use Docker for storage services" -ForegroundColor White
    Write-Host "  -Help            Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "This script sets up:" -ForegroundColor Yellow
    Write-Host "- Python ML dependencies (sentence-transformers, nltk, etc.)" -ForegroundColor White
    Write-Host "- MinIO object storage for research artifacts" -ForegroundColor White
    Write-Host "- Qdrant vector database for semantic search" -ForegroundColor White
    Write-Host "- Web scraping tools (BeautifulSoup, httpx)" -ForegroundColor White
    Write-Host ""
    return
}

Write-Host "Setting up Research Engine..." -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    exit 1
}

# Check Docker if in Docker mode
if ($DockerMode) {
    try {
        $dockerVersion = docker --version 2>&1
        Write-Host "Docker: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Docker not found!" -ForegroundColor Red
        Write-Host "Please install Docker Desktop from https://docker.com" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Gray

# Core packages
$packages = @(
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0", 
    "httpx>=0.24.0",
    "asyncpg>=0.28.0",
    "structlog>=23.1.0",
    "pydantic>=2.0.0",
    "beautifulsoup4>=4.12.0",
    "nltk>=3.8.1",
    "numpy>=1.24.0"
)

# ML and vector packages
$packages += @(
    "sentence-transformers>=2.2.0",
    "qdrant-client>=1.6.0",
    "scikit-learn>=1.3.0"
)

# Storage packages
if (-not $SkipMinIO) {
    $packages += "minio>=7.1.0"
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

# Setup storage services
if ($DockerMode) {
    Write-Host "Setting up storage services with Docker..." -ForegroundColor Gray
    
    # Create docker-compose file
    $dockerCompose = @"
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: rika-minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    container_name: rika-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

volumes:
  minio_data:
    driver: local
  qdrant_data:
    driver: local
"@

    $composeFile = "$PSScriptRoot\..\docker-compose-storage.yml"
    $dockerCompose | Out-File -FilePath $composeFile -Encoding UTF8
    Write-Host "Created Docker Compose file: $composeFile" -ForegroundColor Green
    
    # Start services
    Write-Host "Starting storage services..." -ForegroundColor Gray
    docker-compose -f $composeFile up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Storage services started successfully" -ForegroundColor Green
        Write-Host "MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)" -ForegroundColor White
        Write-Host "Qdrant Dashboard: http://localhost:6333/dashboard" -ForegroundColor White
    } else {
        Write-Host "Failed to start storage services" -ForegroundColor Red
    }
    
} else {
    # Manual setup instructions
    Write-Host "Manual storage setup required:" -ForegroundColor Yellow
    
    if (-not $SkipMinIO) {
        Write-Host ""
        Write-Host "MinIO Object Storage:" -ForegroundColor White
        Write-Host "1. Download from: https://min.io/download" -ForegroundColor Gray
        Write-Host "2. Run: minio server C:\data --console-address :9001" -ForegroundColor Gray
        Write-Host "3. Access console at: http://localhost:9001" -ForegroundColor Gray
    }
    
    if (-not $SkipQdrant) {
        Write-Host ""
        Write-Host "Qdrant Vector Database:" -ForegroundColor White
        Write-Host "1. Download from: https://qdrant.tech/documentation/quick_start/" -ForegroundColor Gray
        Write-Host "2. Run: qdrant" -ForegroundColor Gray
        Write-Host "3. Access at: http://localhost:6333" -ForegroundColor Gray
    }
}

# Download NLTK data
Write-Host ""
Write-Host "Downloading NLTK data..." -ForegroundColor Gray
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create configuration file
Write-Host ""
Write-Host "Creating configuration file..." -ForegroundColor Gray

$configContent = @"
# Research Engine Configuration
# Generated: $(Get-Date)

[engine]
name = "research-engine"
version = "3.2.0" 
port = 5326

[research]
quick_mode_pages = 5
deep_mode_pages = 15
max_content_length = 10000
similarity_threshold = 0.75
request_delay = 2
max_concurrent_requests = 3

[minio]
endpoint = "localhost:9000"
access_key = "minioadmin"
secret_key = "minioadmin123"
bucket = "rika-research"
secure = false

[qdrant]
host = "localhost"
port = 6333
collection = "research_vectors"

[ml]
embedding_model = "all-MiniLM-L6-v2"
vector_size = 384

[n8n]
gateway_url = "http://localhost:5324"
agent_id = "scout"

[cache]
query_cache_hours = 1
source_cache_size = 1000

[logging]
level = "INFO"
file = "logs/research-engine.log"
"@

$configDir = "$PSScriptRoot\..\config"
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$configPath = "$configDir\research-engine.conf"
$configContent | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "Configuration saved: $configPath" -ForegroundColor Green

# Create logs directory
$logsDir = "$PSScriptRoot\..\logs"
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Create startup script
$startupScript = @"
# phase3.2/scripts/start-research-engine.ps1
# Start Research Engine

param(
    [string]`$Config = "$configPath",
    [int]`$Port = 5326,
    [switch]`$Debug
)

Write-Host "Starting Research Engine..." -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Config: `$Config" -ForegroundColor Gray
Write-Host "Port: `$Port" -ForegroundColor Gray
Write-Host "Debug: `$Debug" -ForegroundColor Gray
Write-Host ""

# Wait for storage services to be ready
Write-Host "Checking storage services..." -ForegroundColor Gray

# Check MinIO
try {
    `$minioHealth = Invoke-RestMethod -Uri "http://localhost:9000/minio/health/live" -TimeoutSec 5
    Write-Host "MinIO: Ready" -ForegroundColor Green
} catch {
    Write-Host "MinIO: Not available - object storage disabled" -ForegroundColor Yellow
}

# Check Qdrant  
try {
    `$qdrantHealth = Invoke-RestMethod -Uri "http://localhost:6333/health" -TimeoutSec 5
    Write-Host "Qdrant: Ready" -ForegroundColor Green
} catch {
    Write-Host "Qdrant: Not available - vector search disabled" -ForegroundColor Yellow
}

# Set environment variables
`$env:RESEARCH_ENGINE_CONFIG = `$Config
`$env:RESEARCH_ENGINE_PORT = `$Port

if (`$Debug) {
    `$env:RESEARCH_ENGINE_LOG_LEVEL = "DEBUG"
}

Write-Host ""
Write-Host "Starting engine on port `$Port..." -ForegroundColor Gray

# Start the engine
python "$PSScriptRoot\..\core\research_engine.py"
"@

$startupScriptPath = "$PSScriptRoot\start-research-engine.ps1"
$startupScript | Out-File -FilePath $startupScriptPath -Encoding UTF8
Write-Host "Startup script created: $startupScriptPath" -ForegroundColor Green

# Create test script
$testScript = @"
# phase3.2/scripts/test-research-engine.ps1
# Test Research Engine functionality

param(
    [string]`$Query = "artificial intelligence trends 2025",
    [string]`$Mode = "quick",
    [switch]`$Help
)

if (`$Help) {
    Write-Host "Research Engine Test Suite" -ForegroundColor Cyan
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\test-research-engine.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -Query <text>    Research query to test" -ForegroundColor White
    Write-Host "  -Mode <mode>     Research mode (quick/deep)" -ForegroundColor White
    Write-Host "  -Help            Show this help" -ForegroundColor White
    Write-Host ""
    return
}

Write-Host "Testing Research Engine..." -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

`$baseUrl = "http://localhost:5326"

# Test health endpoint
Write-Host ""
Write-Host "Testing health endpoint..." -ForegroundColor Yellow
try {
    `$response = Invoke-RestMethod -Uri "`$baseUrl/health" -Method GET
    Write-Host "Health check: `$(`$response.status)" -ForegroundColor Green
    Write-Host "Version: `$(`$response.version)" -ForegroundColor White
} catch {
    Write-Host "Health check failed: `$_" -ForegroundColor Red
    exit 1
}

# Test research endpoint
Write-Host ""
Write-Host "Testing research endpoint..." -ForegroundColor Yellow
Write-Host "Query: `$Query" -ForegroundColor Gray
Write-Host "Mode: `$Mode" -ForegroundColor Gray

try {
    `$payload = @{
        query = `$Query
        mode = `$Mode
    } | ConvertTo-Json

    Write-Host "Starting research (this may take a while)..." -ForegroundColor Gray
    
    `$result = Invoke-RestMethod -Uri "`$baseUrl/research" -Method POST -Body `$payload -ContentType "application/json" -TimeoutSec 120
    
    Write-Host "Research completed!" -ForegroundColor Green
    Write-Host "Research ID: `$(`$result.research_id)" -ForegroundColor White
    Write-Host "Duration: `$(`$result.duration_seconds) seconds" -ForegroundColor White
    Write-Host "Sources found: `$(`$result.statistics.new_sources_scraped)" -ForegroundColor White
    Write-Host "Insights extracted: `$(`$result.insights.Count)" -ForegroundColor White
    Write-Host ""
    Write-Host "Summary:" -ForegroundColor Yellow
    Write-Host `$result.summary -ForegroundColor White
    
    if (`$result.insights.Count -gt 0) {
        Write-Host ""
        Write-Host "Top Insights:" -ForegroundColor Yellow
        for (`$i = 0; `$i -lt [Math]::Min(3, `$result.insights.Count); `$i++) {
            Write-Host "`$(`$i + 1). `$(`$result.insights[`$i])" -ForegroundColor White
        }
    }
    
} catch {
    Write-Host "Research test failed: `$_" -ForegroundColor Red
    Write-Host "Make sure MinIO and Qdrant are running" -ForegroundColor Yellow
}

# Test daily digest
Write-Host ""
Write-Host "Testing daily digest..." -ForegroundColor Yellow
try {
    `$digest = Invoke-RestMethod -Uri "`$baseUrl/digest/daily" -Method GET
    Write-Host "Daily digest generated for: `$(`$digest.date)" -ForegroundColor Green
} catch {
    Write-Host "Daily digest test failed: `$_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Green
"@

$testScriptPath = "$PSScriptRoot\test-research-engine.ps1"
$testScript | Out-File -FilePath $testScriptPath -Encoding UTF8
Write-Host "Test script created: $testScriptPath" -ForegroundColor Green

Write-Host ""
Write-Host "Research Engine Setup Complete!" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow

if ($DockerMode) {
    Write-Host "1. Storage services are starting up..." -ForegroundColor White
    Write-Host "2. Wait 30 seconds, then run: .\start-research-engine.ps1" -ForegroundColor White
} else {
    Write-Host "1. Start MinIO: minio server C:\data --console-address :9001" -ForegroundColor White
    Write-Host "2. Start Qdrant: qdrant" -ForegroundColor White
    Write-Host "3. Run: .\start-research-engine.ps1" -ForegroundColor White
}

Write-Host "4. Test: .\test-research-engine.ps1" -ForegroundColor White
Write-Host ""

Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  Research Engine: http://localhost:5326" -ForegroundColor Cyan
Write-Host "  MinIO Console: http://localhost:9001" -ForegroundColor White
Write-Host "  Qdrant Dashboard: http://localhost:6333/dashboard" -ForegroundColor White
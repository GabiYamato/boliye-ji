# Hindi Voice Agent Setup Script
# PowerShell script to set up environment variables and test the service

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Hindi Voice Agent - Environment Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "🔍 Checking Prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check Python
if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found! Please install Python 3.11" -ForegroundColor Red
    exit 1
}

# Check ffmpeg
if (Test-Command ffmpeg) {
    Write-Host "✅ ffmpeg: Installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  ffmpeg not found! Install with: choco install ffmpeg" -ForegroundColor Yellow
}

# Check CUDA
if (Test-Path "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA") {
    Write-Host "✅ CUDA: Installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  CUDA not detected. GPU acceleration may not work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Environment Variables Configuration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow

# Prompt for service URLs
Write-Host ""
Write-Host "Enter your service URLs (press Enter for defaults):" -ForegroundColor Yellow
Write-Host ""

$xttsUrl = Read-Host "XTTS Service URL [http://localhost:8001]"
if ([string]::IsNullOrWhiteSpace($xttsUrl)) {
    $xttsUrl = "http://localhost:8001"
}

$llmUrl = Read-Host "LLM Service URL [http://localhost:8000/v1]"
if ([string]::IsNullOrWhiteSpace($llmUrl)) {
    $llmUrl = "http://localhost:8000/v1"
}

$llmModel = Read-Host "LLM Model [meta-llama/Meta-Llama-3.1-8B-Instruct]"
if ([string]::IsNullOrWhiteSpace($llmModel)) {
    $llmModel = "meta-llama/Meta-Llama-3.1-8B-Instruct"
}

# Set the environment variables
$env:XTTS_SERVICE_URL = $xttsUrl
$env:OPENAI_SERVICE_URL = $llmUrl
$env:OPENAI_API_KEY = "n/a"
$env:LLM_MODEL = $llmModel

Write-Host ""
Write-Host "✅ Environment variables set:" -ForegroundColor Green
Write-Host "   XTTS_SERVICE_URL      = $xttsUrl" -ForegroundColor Cyan
Write-Host "   OPENAI_SERVICE_URL    = $llmUrl" -ForegroundColor Cyan
Write-Host "   LLM_MODEL             = $llmModel" -ForegroundColor Cyan
Write-Host "   OPENAI_API_KEY        = n/a" -ForegroundColor Cyan

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Installation Options" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Install Python dependencies" -ForegroundColor White
Write-Host "2. Test function calling (no external services needed)" -ForegroundColor White
Write-Host "3. Run BentoML service" -ForegroundColor White
Write-Host "4. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select an option [1-4]"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
        pip install -r requirements-hindi-bot.txt
        Write-Host ""
        Write-Host "✅ Installation complete!" -ForegroundColor Green
    }
    "2" {
        Write-Host ""
        Write-Host "🧪 Running function tests..." -ForegroundColor Yellow
        python test_functions.py
    }
    "3" {
        Write-Host ""
        Write-Host "🚀 Starting BentoML service..." -ForegroundColor Yellow
        Write-Host "   Service will be available at: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
        Write-Host ""
        bentoml serve hindi_voice_service:HindiSchemeBot
    }
    "4" {
        Write-Host ""
        Write-Host "👋 Goodbye!" -ForegroundColor Cyan
        exit 0
    }
    default {
        Write-Host ""
        Write-Host "❌ Invalid option" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Quick Reference" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Manual commands:" -ForegroundColor Yellow
Write-Host "  Test functions:  python test_functions.py" -ForegroundColor White
Write-Host "  Start service:   bentoml serve hindi_voice_service:HindiSchemeBot" -ForegroundColor White
Write-Host "  Health check:    http://localhost:3000/" -ForegroundColor White
Write-Host ""
Write-Host "For more details, see README-HINDI-BOT.md" -ForegroundColor Cyan
Write-Host ""

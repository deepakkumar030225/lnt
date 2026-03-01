# Start Backend Server
Write-Host "🚀 Starting Precast AI Optimizer Backend..." -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-Not (Test-Path ".\main.py")) {
    Write-Host "❌ Error: main.py not found. Please run this script from the backend directory." -ForegroundColor Red
    Write-Host "   cd backend" -ForegroundColor Yellow
    Write-Host "   .\start_backend.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if models exist
if (-Not (Test-Path ".\models\precast_pipeline.pkl")) {
    Write-Host "⚠️  Warning: Model files not found in backend\models\" -ForegroundColor Yellow
    Write-Host "   Run precast_phase_01.ipynb to train models, then copy to backend\models\" -ForegroundColor Yellow
    Write-Host ""
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11 or higher." -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Cyan

try {
    python -c "import fastapi, uvicorn, pandas, joblib" 2>&1 | Out-Null
    Write-Host "✓ All dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some dependencies missing. Installing..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Backend API will be available at:" -ForegroundColor White
Write-Host "  http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "  API Documentation:" -ForegroundColor White
Write-Host "  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting server... (Press Ctrl+C to stop)" -ForegroundColor Green
Write-Host ""

# Start the server
python main.py

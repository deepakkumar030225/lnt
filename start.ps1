# Start Full Stack (Backend + Frontend)
Write-Host "🚀 Starting Precast AI Optimizer (Full Stack)..." -ForegroundColor Green
Write-Host ""

# Check if backend exists
if (-Not (Test-Path ".\backend\main.py")) {
    Write-Host "❌ Error: Backend not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

# Check if app.py exists
if (-Not (Test-Path ".\app.py")) {
    Write-Host "❌ Error: app.py not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Starting Backend API..." -ForegroundColor Cyan
Write-Host ""

# Start backend in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; Write-Host '🔧 Backend API Server' -ForegroundColor Cyan; Write-Host ''; python main.py"

Write-Host "✓ Backend started in new window" -ForegroundColor Green
Write-Host "  Waiting for backend to initialize..." -ForegroundColor Yellow

# Wait for backend to be ready
Start-Sleep -Seconds 3

# Check if backend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 2>&1
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend is healthy and ready!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Backend may still be starting... continuing anyway" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 2: Starting Frontend (Streamlit)..." -ForegroundColor Cyan
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🎯 Quick Access:" -ForegroundColor White
Write-Host ""
Write-Host "  Frontend UI:   http://localhost:8501" -ForegroundColor Yellow
Write-Host "  Backend API:   http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs:      http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Start frontend
streamlit run app.py

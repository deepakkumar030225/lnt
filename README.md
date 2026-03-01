# Precast AI Optimizer

AI-powered optimization system for precast concrete production, featuring a FastAPI backend for ML model serving and a Streamlit frontend for interactive analysis.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Streamlit Frontend (app.py)             │
│  • Interactive UI                                        │
│  • Optimization dashboard                               │
│  • Pareto analysis                                       │
│  • AI report generation                                 │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP REST API
                   ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (backend/main.py)          │
│  • /predict/single - Single predictions                 │
│  • /predict/batch - Batch predictions                   │
│  • /health - Health checks                              │
│  • /meta - Model metadata                               │
└──────────────────┬──────────────────────────────────────┘
                   │ Loads ML models
                   ▼
┌─────────────────────────────────────────────────────────┐
│                   ML Models (backend/models/)           │
│  • precast_pipeline.pkl                                 │
│  • model_Time_to_demould.pkl                            │
│  • model_Cycle_time.pkl                                 │
│  • model_Total_cost.pkl                                 │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
lnt/
├── app.py                      # Streamlit frontend application
├── precast_phase_01.ipynb     # Model training notebook
├── precast_phase_02.ipynb     # Model evaluation notebook
├── models/                     # Original model files (legacy)
├── backend/                    # FastAPI backend
│   ├── main.py                # API server
│   ├── requirements.txt       # Backend dependencies
│   ├── models/                # ML model artifacts
│   │   ├── precast_pipeline.pkl
│   │   ├── precast_meta.json
│   │   └── model_*.pkl
│   └── README.md              # Backend documentation
├── .streamlit/
│   └── secrets.toml           # API keys (Gemini API)
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Virtual environment (recommended)

### Step 1: Install Backend Dependencies

Open a terminal and navigate to the backend directory:

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start the Backend Server

From the `backend/` directory:

```bash
python main.py
```

The API will start on **http://localhost:8000**

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
✓ Loaded 3 models successfully
```

### Step 3: Install Frontend Dependencies

Open a **new terminal** in the project root directory:

```bash
pip install streamlit pandas numpy plotly google-generativeai requests
```

### Step 4: Configure API Key (Optional - for AI Reports)

Create `.streamlit/secrets.toml`:

```toml
GOOGLE_API_KEY = "your-gemini-api-key-here"
```

### Step 5: Start the Streamlit App

From the project root:

```bash
streamlit run app.py
```

The app will open in your browser at **http://localhost:8501**

## 🔧 Configuration

### Backend API URL

By default, the frontend connects to `http://localhost:8000`. To change this, set environment variable:

```bash
# Windows PowerShell
$env:API_BASE_URL = "http://your-api-url:8000"

# Linux/Mac
export API_BASE_URL=http://your-api-url:8000
```

### Port Configuration

**Backend:**
Edit `backend/main.py` and change the port in the `uvicorn.run()` call, or:

```bash
cd backend
uvicorn main:app --port 8080
```

**Frontend:**
```bash
streamlit run app.py --server.port 8502
```

## 📊 Features

### Frontend (Streamlit)

- **Interactive Dashboard**: Configure yard parameters via sidebar
- **Multi-Value Sweeps**: Test multiple values simultaneously
- **Optimization Engine**: Evaluate thousands of combinations
- **Pareto Analysis**: Identify optimal trade-offs
- **SOP Generation**: Auto-generate production procedures
- **Debug Explorer**: Random scenario testing
- **AI Reports**: Gemini-powered insights and recommendations

### Backend (FastAPI)

- **Single Predictions**: Fast inference for individual configs
- **Batch Processing**: Efficient vectorized predictions
- **Health Monitoring**: Built-in health checks
- **Auto Documentation**: Interactive API docs at `/docs`
- **CORS Support**: Ready for frontend integration
- **Pydantic Validation**: Type-safe request/response

## 📚 Usage Guide

### 1. Basic Prediction

1. Start both backend and frontend
2. Use the sidebar to configure parameters
3. View baseline performance
4. Click "✨ Run Optimiser" to find optimal configurations

### 2. Batch Optimization

The optimizer automatically:
- Generates combinations from your input ranges
- Sends batch requests to the API
- Analyzes results using weighted scoring
- Displays Pareto-optimal solutions

### 3. AI Analysis (Requires Gemini API Key)

1. Navigate to "🤖 AI Report" tab
2. Select report focus areas
3. Click "🚀 Generate AI Report"
4. Ask follow-up questions in the chat interface

## 🔬 API Documentation

With the backend running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example API Call

```python
import requests

response = requests.post(
    "http://localhost:8000/predict/single",
    json={
        "Ambient_temp_C": 30,
        "Cement_type": "OPC",
        "Cement_content_kgm3": 380,
        "Water_cement_ratio": 0.40,
        "Curing_method": "steam",
        "Steam_temp_C": 60,
        "Steam_duration_hr": 6,
        # ... other parameters
    }
)

result = response.json()
print(f"Cycle Time: {result['Cycle_Time_hr']} hours")
print(f"Total Cost: ₹{result['Total_Cost_INR']:,.0f}")
```

## 🛠️ Development

### Running Both Services Together

**Option 1: Two Terminals**

Terminal 1 (Backend):
```bash
cd backend
python main.py
```

Terminal 2 (Frontend):
```bash
streamlit run app.py
```

**Option 2: PowerShell Script**

Create `start.ps1`:

```powershell
# Start backend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend
streamlit run app.py
```

Run:
```bash
.\start.ps1
```

### Model Training

If you need to retrain models:

1. Open `precast_phase_01.ipynb`
2. Run all cells to train and save models
3. Models will be saved to `models/` directory
4. Copy to `backend/models/` if needed:
   ```bash
   Copy-Item -Path "models\*" -Destination "backend\models\" -Recurse -Force
   ```

## 🐛 Troubleshooting

### "Cannot connect to API backend"

**Solution:**
1. Ensure backend is running on http://localhost:8000
2. Check terminal for backend errors
3. Try accessing http://localhost:8000/health in browser

### "Models not loaded" (503 error)

**Solution:**
1. Run `precast_phase_01.ipynb` to generate model files
2. Ensure all .pkl files are in `backend/models/`:
   - `precast_pipeline.pkl`
   - `precast_meta.json`
   - `model_Time_to_demould.pkl`
   - `model_Cycle_time.pkl`
   - `model_Total_cost.pkl`

### Port Already in Use

**Backend:**
```bash
# Find process on port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <PID> /F
```

**Frontend:**
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### Slow Batch Predictions

**Solution:**
- Reduce number of combinations in sidebar
- Limit sweep values to essential ranges
- Use fewer parameter variations

## 📈 Performance Tips

1. **Use Batch Endpoint**: Always use `/predict/batch` for multiple predictions
2. **Limit Combinations**: Start with 100-1000 combinations, scale up as needed
3. **Backend Workers**: For production, use multiple uvicorn workers
4. **Cache Results**: Frontend caches API health checks automatically

## 🚢 Deployment

### Docker Deployment

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port", "8501"]
```

### Cloud Deployment

- **Backend**: Deploy to AWS Lambda, Google Cloud Run, Azure Functions
- **Frontend**: Deploy to Streamlit Cloud, Heroku, Railway
- **Full Stack**: Use Docker Compose or Kubernetes

## 📄 License

© 2026 LNT Precast AI Optimizer

## 🤝 Contributing

1. Train models using `precast_phase_01.ipynb`
2. Test API endpoints via `/docs`
3. Validate frontend functionality
4. Submit improvements

## 📞 Support

- **Backend Issues**: See `backend/README.md`
- **Model Training**: Check Jupyter notebooks
- **Frontend Problems**: Review `app.py` logs

---

**Happy Optimizing! 🏭✨**

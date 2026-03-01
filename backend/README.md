# Precast AI Optimizer - FastAPI Backend

This is the FastAPI backend for the Precast AI Optimizer application. It serves ML models for predicting demould time, cycle time, and total cost for precast concrete production.

## Architecture

```
┌─────────────────┐         HTTP/REST          ┌──────────────────┐
│                 │  ◄─────────────────────────►│                  │
│  Streamlit App  │    JSON predictions        │  FastAPI Backend │
│   (Frontend)    │                             │    (ML Server)   │
│                 │                             │                  │
└─────────────────┘                             └──────────────────┘
                                                        │
                                                        │ Loads
                                                        ▼
                                                ┌───────────────┐
                                                │  ML Models    │
                                                │  - Pipeline   │
                                                │  - XGBoost    │
                                                └───────────────┘
```

## Features

- **RESTful API** for ML model inference
- **Single prediction** endpoint for individual configurations
- **Batch prediction** endpoint for optimizing multiple scenarios
- **Health checks** and metadata endpoints
- **CORS enabled** for frontend integration
- **Auto-reload** during development
- **Pydantic validation** for request/response schemas

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── models/              # ML artifacts
│   ├── precast_pipeline.pkl
│   ├── precast_meta.json
│   ├── model_Time_to_demould.pkl
│   ├── model_Cycle_time.pkl
│   └── model_Total_cost.pkl
└── README.md           # This file
```

## Installation

### 1. Navigate to backend directory

```bash
cd backend
```

### 2. Create virtual environment (optional but recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Server

### Development Mode (with auto-reload)

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: **http://localhost:8000**

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### 1. Health Check

**GET** `/health`

Returns the health status of the API and loaded models.

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "available_targets": ["Time_to_demould", "Cycle_time", "Total_cost"]
}
```

### 2. Get Metadata

**GET** `/meta`

Returns model metadata including feature names and column types.

**Response:**
```json
{
  "features": [...],
  "numerical_cols": [...],
  "categorical_cols": [...],
  "target_names_map": {...},
  "model_count": 3
}
```

### 3. Single Prediction

**POST** `/predict/single`

Predicts demould time, cycle time, and total cost for a single configuration.

**Request Body:**
```json
{
  "Ambient_temp_C": 30,
  "Relative_humidity_pct": 60,
  "Wind_speed_mps": 2.0,
  "Season": "summer",
  "Cement_type": "OPC",
  "Cement_content_kgm3": 380,
  "Water_cement_ratio": 0.40,
  "Curing_method": "steam",
  "Steam_temp_C": 60,
  "Steam_duration_hr": 6,
  ...
}
```

**Response:**
```json
{
  "Demould_Time_hr": 8.5,
  "Cycle_Time_hr": 12.3,
  "Total_Cost_INR": 45000.0,
  "input_params": {...}
}
```

### 4. Batch Prediction

**POST** `/predict/batch`

Predicts for multiple configurations at once (more efficient for optimization).

**Request Body:**
```json
{
  "inputs": [
    {
      "Ambient_temp_C": 30,
      "Cement_content_kgm3": 380,
      ...
    },
    {
      "Ambient_temp_C": 35,
      "Cement_content_kgm3": 400,
      ...
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "Demould_Time_hr": 8.5,
      "Cycle_Time_hr": 12.3,
      "Total_Cost_INR": 45000.0,
      "input_params": {...}
    },
    ...
  ],
  "count": 2
}
```

## Example Usage

### Using Python `requests`

```python
import requests

# Single prediction
response = requests.post(
    "http://localhost:8000/predict/single",
    json={
        "Ambient_temp_C": 30,
        "Cement_type": "OPC",
        "Cement_content_kgm3": 380,
        "Water_cement_ratio": 0.40,
        "Curing_method": "steam",
        "Steam_temp_C": 60,
        # ... other required fields
    }
)
result = response.json()
print(f"Cycle Time: {result['Cycle_Time_hr']} hours")
```

### Using cURL

```bash
curl -X POST "http://localhost:8000/predict/single" \
  -H "Content-Type: application/json" \
  -d '{
    "Ambient_temp_C": 30,
    "Cement_type": "OPC",
    "Cement_content_kgm3": 380,
    "Water_cement_ratio": 0.40,
    "Curing_method": "steam",
    "Steam_temp_C": 60
  }'
```

## Configuration

### Environment Variables

You can configure the API using environment variables:

- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `WORKERS`: Number of worker processes (production)
- `LOG_LEVEL`: Logging level (default: `info`)

### CORS Configuration

The API is configured to allow all origins for development. For production, modify the CORS settings in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Optimization

### Batch Processing

For evaluating multiple scenarios (like in the optimizer), always use the `/predict/batch` endpoint instead of multiple `/predict/single` calls. This is significantly faster due to:

- Single HTTP request overhead
- Vectorized numpy operations
- Efficient DataFrame processing

### Caching

The models are loaded once at startup and cached in memory, ensuring fast response times.

### Scaling

For production deployments with high load:

```bash
# Multiple workers
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000

# Or use Gunicorn with uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### Models not loading

**Error:** `Models not loaded` (503 error)

**Solution:** Ensure the `models/` directory contains all required files:
- `precast_pipeline.pkl`
- `precast_meta.json`
- `model_Time_to_demould.pkl`
- `model_Cycle_time.pkl`
- `model_Total_cost.pkl`

Run `precast_phase_01.ipynb` to generate these files if missing.

### Port already in use

**Error:** `Address already in use`

**Solution:** Change the port or kill the existing process:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Connection refused from Streamlit

**Error:** `Cannot connect to API backend`

**Solution:**
1. Ensure the backend is running: `python main.py`
2. Check the URL in Streamlit app matches the backend URL
3. Verify no firewall is blocking the connection

## Testing

### Manual Testing

Visit http://localhost:8000/docs to use the interactive Swagger UI for testing all endpoints.

### Automated Testing

Create a `test_api.py` file:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["models_loaded"] == True

def test_single_prediction():
    response = client.post("/predict/single", json={
        "Ambient_temp_C": 30,
        "Cement_type": "OPC",
        # ... complete input
    })
    assert response.status_code == 200
    assert "Cycle_Time_hr" in response.json()
```

Run tests:
```bash
pytest test_api.py
```

## Deployment

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t precast-api .
docker run -p 8000:8000 precast-api
```

### Cloud Deployment

The API can be deployed to:
- **AWS Lambda** (with Mangum adapter)
- **Google Cloud Run**
- **Azure Container Instances**
- **Heroku**
- **Railway**
- **Render**

## License

Part of the Precast AI Optimizer project.

## Support

For issues or questions, please refer to the main project documentation.

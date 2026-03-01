from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import joblib
import json
import os
from pathlib import Path

# ─────────────────────────────────────────────
# FASTAPI APP SETUP
# ─────────────────────────────────────────────
app = FastAPI(
    title="Precast AI Optimizer API",
    description="Machine Learning API for precast concrete production optimization",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
MODEL_DIR = Path(__file__).parent / "models"

# ─────────────────────────────────────────────
# GLOBAL MODEL STORAGE
# ─────────────────────────────────────────────
pipeline = None
meta = None
models = {}

# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────
class PredictionInput(BaseModel):
    """Single prediction input"""
    Ambient_temp_C: float = Field(default=30, ge=10, le=45)
    Relative_humidity_pct: float = Field(default=60, ge=20, le=90)
    Wind_speed_mps: float = Field(default=2.0, ge=0.0, le=10.0)
    Season: str = Field(default="summer")
    Daytime_hours: int = Field(default=12, ge=6, le=16)
    No_of_moulds: int = Field(default=10, ge=1, le=30)
    Cement_type: str = Field(default="OPC")
    Cement_content_kgm3: float = Field(default=380, ge=300, le=450)
    Water_cement_ratio: float = Field(default=0.40, ge=0.30, le=0.55)
    Flyash_percent: float = Field(default=0, ge=0, le=30)
    Target_grade_MPa: float = Field(default=40, ge=20, le=50)
    Curing_method: str = Field(default="steam")
    Steam_temp_C: float = Field(default=60, ge=0, le=80)
    Steam_duration_hr: float = Field(default=6, ge=0, le=14)
    Curing_start_delay_hr: float = Field(default=2, ge=0, le=8)
    Chamber_humidity_pct: float = Field(default=80, ge=40, le=100)
    Cleaning_time_min: float = Field(default=20, ge=5, le=60)
    Reset_time_min: float = Field(default=15, ge=5, le=60)
    Equipment_downtime_min: float = Field(default=10, ge=0, le=120)
    Energy_cost_rate_INR_per_kWh: float = Field(default=10.0, ge=5.0, le=20.0)
    Early_strength_requirement_MPa: float = Field(default=20.0, ge=10.0, le=40.0)
    Initial_strength_12hr_MPa: float = Field(default=0.0)
    Maturity_index: float = Field(default=0.0)
    Automation_level: int = Field(default=1, ge=0, le=2)

    class Config:
        json_schema_extra = {
            "example": {
                "Ambient_temp_C": 30,
                "Relative_humidity_pct": 60,
                "Wind_speed_mps": 2.0,
                "Season": "summer",
                "Daytime_hours": 12,
                "No_of_moulds": 10,
                "Cement_type": "OPC",
                "Cement_content_kgm3": 380,
                "Water_cement_ratio": 0.40,
                "Flyash_percent": 0,
                "Target_grade_MPa": 40,
                "Curing_method": "steam",
                "Steam_temp_C": 60,
                "Steam_duration_hr": 6,
                "Curing_start_delay_hr": 2,
                "Chamber_humidity_pct": 80,
                "Cleaning_time_min": 20,
                "Reset_time_min": 15,
                "Equipment_downtime_min": 10,
                "Energy_cost_rate_INR_per_kWh": 10.0,
                "Early_strength_requirement_MPa": 20.0,
                "Initial_strength_12hr_MPa": 0.0,
                "Maturity_index": 0.0,
                "Automation_level": 1
            }
        }


class BatchPredictionInput(BaseModel):
    """Batch prediction input"""
    inputs: List[Dict[str, Any]]


class PredictionOutput(BaseModel):
    """Prediction output"""
    Demould_Time_hr: float
    Cycle_Time_hr: float
    Total_Cost_INR: float
    input_params: Dict[str, Any]


class BatchPredictionOutput(BaseModel):
    """Batch prediction output"""
    results: List[PredictionOutput]
    count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: bool
    available_targets: List[str]


# ─────────────────────────────────────────────
# MODEL LOADING
# ─────────────────────────────────────────────
def load_models():
    """Load ML models and pipeline on startup"""
    global pipeline, meta, models
    
    try:
        pipeline = joblib.load(MODEL_DIR / "precast_pipeline.pkl")
        with open(MODEL_DIR / "precast_meta.json", "r") as f:
            meta = json.load(f)
        
        for short_name in meta["target_names_map"].keys():
            models[short_name] = joblib.load(MODEL_DIR / f"model_{short_name}.pkl")
        
        print(f"✓ Loaded {len(models)} models successfully")
        return True
    except Exception as e:
        print(f"✗ Error loading models: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Load models when the API starts"""
    success = load_models()
    if not success:
        print("WARNING: Models failed to load. API will return errors.")


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def _make_row(inputs: dict) -> pd.DataFrame:
    """Build a single-row DataFrame compatible with the trained pipeline."""
    features_ordered = meta["features"]
    numerical_cols = meta["numerical_cols"]
    categorical_cols = meta["categorical_cols"]
    
    # Initialize numerical columns with 0, categorical with empty string
    row = {}
    for col in features_ordered:
        if col in categorical_cols:
            row[col] = ""  # Empty string for categorical
        else:
            row[col] = 0  # Zero for numerical
    
    row.update(inputs)
    
    # Sensible default for energy cost
    if row.get("Energy_cost_rate_INR_per_kWh", 0) == 0:
        row["Energy_cost_rate_INR_per_kWh"] = 10.0
    
    df = pd.DataFrame([row])[features_ordered]
    
    # Ensure categorical columns are strings
    for col in categorical_cols:
        df[col] = df[col].astype(str)
    
    # Ensure numerical columns are numeric
    for col in numerical_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    return df


def _batch_make_rows(inputs_list: List[dict]) -> pd.DataFrame:
    """Build multiple rows DataFrame for batch prediction."""
    if not inputs_list:
        return pd.DataFrame()
    
    features_ordered = meta["features"]
    numerical_cols = meta["numerical_cols"]
    categorical_cols = meta["categorical_cols"]
    
    # Build list of properly formatted rows
    processed_rows = []
    for r in inputs_list:
        # Initialize row with proper defaults
        row_dict = {}
        for col in features_ordered:
            if col in categorical_cols:
                row_dict[col] = ""
            else:
                row_dict[col] = 0.0
        
        # Update with actual values
        row_dict.update(r)
        
        # Ensure energy cost default
        if row_dict.get("Energy_cost_rate_INR_per_kWh", 0) == 0:
            row_dict["Energy_cost_rate_INR_per_kWh"] = 10.0
        
        processed_rows.append(row_dict)
    
    # Create DataFrame with explicit column order
    df = pd.DataFrame(processed_rows, columns=features_ordered)
    
    # Explicitly set dtypes
    for col in categorical_cols:
        df[col] = df[col].astype(str)
    
    for col in numerical_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    
    return df


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    if pipeline is None or not models:
        return HealthResponse(
            status="unhealthy",
            models_loaded=False,
            available_targets=[]
        )
    
    return HealthResponse(
        status="healthy",
        models_loaded=True,
        available_targets=list(models.keys())
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if pipeline is None or not models:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    return HealthResponse(
        status="healthy",
        models_loaded=True,
        available_targets=list(models.keys())
    )


@app.post("/predict/single", response_model=PredictionOutput)
async def predict_single(input_data: PredictionInput):
    """
    Single prediction endpoint
    
    Returns predictions for demould time, cycle time, and total cost based on input parameters.
    """
    if pipeline is None or not models:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Convert input to dict
        inputs = input_data.model_dump()
        
        # Create DataFrame and transform
        df = _make_row(inputs)
        X = pipeline.transform(df)
        
        # Make predictions
        predictions = {
            "Demould_Time_hr": float(models["Time_to_demould"].predict(X)[0]),
            "Cycle_Time_hr": float(models["Cycle_time"].predict(X)[0]),
            "Total_Cost_INR": float(models["Total_cost"].predict(X)[0])
        }
        
        return PredictionOutput(
            **predictions,
            input_params=inputs
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionOutput)
async def predict_batch(batch_input: BatchPredictionInput):
    """
    Batch prediction endpoint
    
    Returns predictions for multiple configurations at once.
    Accepts a list of input dictionaries and returns predictions for each.
    """
    if pipeline is None or not models:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        inputs_list = batch_input.inputs
        
        if not inputs_list:
            return BatchPredictionOutput(results=[], count=0)
        
        # Create DataFrame for all inputs
        df = _batch_make_rows(inputs_list)
        
        # Transform using pipeline
        X = pipeline.transform(df)
        
        # Make predictions
        demould_times = models["Time_to_demould"].predict(X)
        cycle_times = models["Cycle_time"].predict(X)
        total_costs = models["Total_cost"].predict(X)
        
        # Build results
        results = []
        for i, (inputs, demould, cycle, cost) in enumerate(
            zip(inputs_list, demould_times, cycle_times, total_costs)
        ):
            results.append(
                PredictionOutput(
                    Demould_Time_hr=float(demould),
                    Cycle_Time_hr=float(cycle),
                    Total_Cost_INR=float(cost),
                    input_params=inputs
                )
            )
        
        return BatchPredictionOutput(
            results=results,
            count=len(results)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")


@app.get("/meta")
async def get_metadata():
    """
    Get model metadata including feature names and ranges
    """
    if meta is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    return {
        "features": meta.get("features", []),
        "numerical_cols": meta.get("numerical_cols", []),
        "categorical_cols": meta.get("categorical_cols", []),
        "target_names_map": meta.get("target_names_map", {}),
        "model_count": len(models)
    }


# ─────────────────────────────────────────────
# RUN SERVER
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

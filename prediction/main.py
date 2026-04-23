import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# 1. Initialize FastAPI
app = FastAPI(title="Building Energy Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Load the model from your specific path
# Make sure the folder 'models' exists relative to this script
MODEL_PATH = 'models/xgboost_model_final.pkl'
try:
    model = joblib.load(MODEL_PATH)
    print(f"Successfully loaded model from {MODEL_PATH}")
except FileNotFoundError:
    print(f"ERROR: Model not found at {MODEL_PATH}. Check your file path!")

# 3. Define Input Schema
class BuildingData(BaseModel):
    temperature_f: float
    apparent_temperature_f: float
    temp_roll_3h: float
    hour: int
    day_week: int
    month: int
    sqft: float
    primary_space_usage: str
    sub_type: str
    year_built: float
    number_of_floors: float

@app.post("/predict")
def predict_energy(data: BuildingData):
    # Convert Pydantic model to dict
    payload = data.model_dump()
    input_df = pd.DataFrame([payload])

    # Calculate Derived Features (CDH/HDH)
    input_df['CDH'] = (input_df['temperature_f'] - 65).clip(lower=0)
    input_df['HDH'] = (65 - input_df['temperature_f']).clip(lower=0)

    # Convert strings to Category types
    input_df['primary_space_usage'] = input_df['primary_space_usage'].astype('category')
    input_df['sub_type'] = input_df['sub_type'].astype('category')

    # Enforce Feature Order (Matches the 13 features from your error)
    expected_order = [
        'temperature_f', 'apparent_temperature_f', 'CDH', 'HDH', 
        'temp_roll_3h', 'hour', 'day_week', 'month', 'sqft', 
        'primary_space_usage', 'sub_type', 'year_built', 'number_of_floors'
    ]
    input_df = input_df[expected_order]

    # Predict and Denormalize
    preds_eui = model.predict(input_df)[0]
    preds_raw = preds_eui * data.sqft

    return {
        "predicted_eui": float(preds_eui),
        "predicted_kwh": float(preds_raw)
    }

# 4. The Server Runner
if __name__ == "__main__":
    # This runs the server on http://127.0.0.1:8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uvicorn

# Import our custom weather module
import weather_service

app = FastAPI(title="Campus Energy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL MODEL VARIABLES ---
xgb_model = None
lr_model = None

# --- LOAD MODELS ---
try:
    xgb_model = joblib.load('models/xgboost_model_final.pkl')
    lr_model = joblib.load('models/linear_regression_final.pkl')
    print("Successfully loaded XGBoost and Linear Regression models.")
except Exception as e:
    print(f"CRITICAL ERROR loading models: {e}")

class BuildingData(BaseModel):
    prediction_time: str 
    sqft: float
    primary_space_usage: str
    sub_type: str
    year_built: float
    number_of_floors: float

def prepare_row(base_data, dt, weather_at_hour, model_type="xgboost"):
    row = {
        'sqft': base_data.sqft,
        'primary_space_usage': base_data.primary_space_usage,
        'sub_type': base_data.sub_type,
        'year_built': base_data.year_built,
        'number_of_floors': base_data.number_of_floors,
        'temperature_f': weather_at_hour['temp'],
        'apparent_temperature_f': weather_at_hour['app_temp'],
        'temp_roll_3h': weather_at_hour['roll_3h'],
        'hour': dt.hour,
        'day_week': dt.weekday(),
        'month': dt.month
    }
    df = pd.DataFrame([row])
    df['CDH'] = (df['temperature_f'] - 65).clip(lower=0)
    df['HDH'] = (65 - df['temperature_f']).clip(lower=0)

    if model_type == "xgboost":
        df['primary_space_usage'] = df['primary_space_usage'].astype('category')
        df['sub_type'] = df['sub_type'].astype('category')
    else:
        df['primary_space_usage'] = pd.Categorical(df['primary_space_usage']).codes
        df['sub_type'] = pd.Categorical(df['sub_type']).codes
        df = df.fillna(0)

    expected_order = [
        'temperature_f', 'apparent_temperature_f', 'CDH', 'HDH', 
        'temp_roll_3h', 'hour', 'day_week', 'month', 'sqft', 
        'primary_space_usage', 'sub_type', 'year_built', 'number_of_floors'
    ]
    return df[expected_order]

# --- XGBOOST ROUTES ---
@app.post("/predict/xgboost")
def predict_hour_xgb(data: BuildingData):
    # Slice to 16 chars to ignore UTC offset and keep local hour
    dt = datetime.fromisoformat(data.prediction_time[:16])
    day_weather = weather_service.get_day_weather(dt)
    h = dt.hour
    weather_at_hour = {"temp": day_weather['temps'][h], "app_temp": day_weather['app_temps'][h], "roll_3h": day_weather['roll_3h'][h]}
    input_df = prepare_row(data, dt, weather_at_hour, model_type="xgboost")
    preds_eui = xgb_model.predict(input_df)[0]
    return {"hour": h, "time": dt.strftime("%I %p"), "kwh": float(preds_eui * data.sqft), "temp": weather_at_hour['temp']}

@app.post("/predict_day/xgboost")
def predict_day_xgb(data: BuildingData):
    base_dt = datetime.fromisoformat(data.prediction_time[:16]).replace(hour=0)
    day_weather = weather_service.get_day_weather(base_dt)
    results = []
    for h in range(24):
        current_dt = base_dt + timedelta(hours=h)
        weather_at_hour = {"temp": day_weather['temps'][h], "app_temp": day_weather['app_temps'][h], "roll_3h": day_weather['roll_3h'][h]}
        input_df = prepare_row(data, current_dt, weather_at_hour, model_type="xgboost")
        preds_eui = xgb_model.predict(input_df)[0]
        results.append({"hour": h, "time": current_dt.strftime("%I %p"), "kwh": float(preds_eui * data.sqft), "temp": weather_at_hour['temp']})
    return results

# --- LINEAR REGRESSION ROUTES ---
@app.post("/predict/linear")
def predict_hour_lr(data: BuildingData):
    dt = datetime.fromisoformat(data.prediction_time[:16])
    day_weather = weather_service.get_day_weather(dt)
    h = dt.hour
    weather_at_hour = {"temp": day_weather['temps'][h], "app_temp": day_weather['app_temps'][h], "roll_3h": day_weather['roll_3h'][h]}
    input_df = prepare_row(data, dt, weather_at_hour, model_type="linear")
    preds_eui = lr_model.predict(input_df)[0]
    return {"hour": h, "time": dt.strftime("%I %p"), "kwh": float(preds_eui * data.sqft), "temp": weather_at_hour['temp']}

@app.post("/predict_day/linear")
def predict_day_lr(data: BuildingData):
    base_dt = datetime.fromisoformat(data.prediction_time[:16]).replace(hour=0)
    day_weather = weather_service.get_day_weather(base_dt)
    results = []
    for h in range(24):
        current_dt = base_dt + timedelta(hours=h)
        weather_at_hour = {"temp": day_weather['temps'][h], "app_temp": day_weather['app_temps'][h], "roll_3h": day_weather['roll_3h'][h]}
        input_df = prepare_row(data, current_dt, weather_at_hour, model_type="linear")
        preds_eui = lr_model.predict(input_df)[0]
        results.append({"hour": h, "time": current_dt.strftime("%I %p"), "kwh": float(preds_eui * data.sqft), "temp": weather_at_hour['temp']})
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
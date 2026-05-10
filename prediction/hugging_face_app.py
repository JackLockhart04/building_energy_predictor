import requests
from datetime import datetime, timedelta

# Constants for Tuscaloosa, AL
LAT = 33.2103
LON = -87.5659

def get_day_weather(target_dt: datetime):
    """
    Fetches the full 24-hour weather data for a specific date.
    Returns lists for temp, app_temp, and calculated rolling_3h.
    """
    now = datetime.now()
    # Using 13 days as a buffer for the 14-day forecast limit
    delta_days = (target_dt.date() - now.date()).days
    
    fetch_dt = target_dt
    is_archive = False

    if delta_days > 13:
        # Far future: Fallback to 1 year ago
        fetch_dt = target_dt - timedelta(days=365)
        is_archive = True
    elif delta_days < 0:
        # Past: Use Archive
        is_archive = True
    
    base_url = "https://archive-api.open-meteo.com/v1/archive" if is_archive else "https://api.open-meteo.com/v1/forecast"
    
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": fetch_dt.strftime("%Y-%m-%d"),
        "end_date": fetch_dt.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m,apparent_temperature",
        "temperature_unit": "fahrenheit",
        "timezone": "America/Chicago"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get("hourly", {})
        temps = hourly.get("temperature_2m", [])
        app_temps = hourly.get("apparent_temperature", [])

        # Pre-calculate rolling 3h averages for the whole day
        # window of [current, current-1, current-2]
        rolling_3h = []
        for i in range(len(temps)):
            window = temps[max(0, i-2) : i+1]
            rolling_3h.append(sum(window) / len(window))
            
        return {
            "temps": temps,
            "app_temps": app_temps,
            "roll_3h": rolling_3h
        }
    except Exception as e:
        print(f"Weather API Error: {e}")
        # Default fallback (24 hours of neutral weather)
        return {"temps": [72]*24, "app_temps": [75]*24, "roll_3h": [70]*24}
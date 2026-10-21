import os
import requests
import pandas as pd 
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

EIA_API_KEY = os.getenv("EIA_API_KEY", "DEMO_KEY")

def fetch_ercot_grid_load(days_back=7):
    """Fetches hourly grid load data for ERCOT region from EIA API v2."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

    url = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": "ERCO",
        "facets[type][]": "D",  # Demand
        "start": start_date.strftime("%Y-%m-%dT00"),
        "end": end_date.strftime("%Y-%m-%dT23"),
        "sort[0][column]": "period",
        "sort[0][direction]": "desc"
    }

    print("[Ingestion] Fetching ERCOT Grid Load telemetry...")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json().get("response", {}).get("data", [])
        return pd.DataFrame(data)
    else:
        print(f"[Error] Failed EIA API Request: Status {response.status_code}")
        return pd.DataFrame()

def fetch_texas_weather(lat=32.7767, lon=-96.7970, days_back=7):
    """Fetches hourly temperature & weather data for Dallas demand center."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature",
        "past_days": days_back,
        "forecast_days": 1,
        "temperature_unit": "fahrenheit"
    }
    
    print("[Ingestion] Fetching Texas Regional Weather metrics...")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        hourly_data = response.json().get("hourly", {})
        return pd.DataFrame(hourly_data)
    else:
        print(f"[Error] Failed Weather API Request: Status {response.status_code}")
        return pd.DataFrame()

def run_ingestion():
    os.makedirs("data/raw", exist_ok=True)
    
    # Fetch data
    grid_df = fetch_ercot_grid_load()
    weather_df = fetch_texas_weather()
    
    # Save static raw landing files for local Bronze layer
    if not grid_df.empty:
        grid_file = "data/raw/ercot_grid_raw.csv"
        grid_df.to_csv(grid_file, index=False)
        print(f"[Success] Saved {len(grid_df)} grid records to {grid_file}")
        
    if not weather_df.empty:
        weather_file = "data/raw/texas_weather_raw.csv"
        weather_df.to_csv(weather_file, index=False)
        print(f"[Success] Saved {len(weather_df)} weather records to {weather_file}")

if __name__ == "__main__":
    run_ingestion() 

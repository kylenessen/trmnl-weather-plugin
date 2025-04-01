import requests
import os
import json
from datetime import datetime

# --- Configuration ---
STATION_ID = "157960"
# Get token from environment variable (set as GitHub Secret)
API_TOKEN = os.environ.get("WF_TOKEN")
OUTPUT_FILE = "weather_data.json"
API_URL = f"https://swd.weatherflow.com/swd/rest/observations/station/{STATION_ID}?token={API_TOKEN}"

# --- Helper Functions ---
def get_wind_direction_cardinal(degrees):
    """Converts wind direction degrees to cardinal direction."""
    if degrees is None:
        return "N/A"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(degrees / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def celsius_to_fahrenheit(celsius):
    """Converts Celsius to Fahrenheit."""
    if celsius is None:
        return None
    return round((celsius * 9/5) + 32, 1)

def mps_to_mph(mps):
    """Converts meters per second to miles per hour."""
    if mps is None:
        return None
    return round(mps * 2.23694, 1)

def mm_to_inches(mm):
    """Converts millimeters to inches."""
    if mm is None:
        return None
    return round(mm / 25.4, 2)

def mb_to_inhg(mb):
    """Converts millibars to inches of mercury."""
    if mb is None:
        return None
    return round(mb * 0.02953, 2)

# --- Main Script ---
if not API_TOKEN:
    print("Error: WeatherFlow API token (WF_TOKEN) not found in environment variables.")
    exit(1)

print(f"Fetching weather data for station {STATION_ID}...")

try:
    response = requests.get(API_URL, timeout=15)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    data = response.json()

    if not data or 'obs' not in data or not data['obs']:
        print("Error: No observations found in API response.")
        print(f"Response: {data}")
        exit(1)

    # Access the first observation dictionary directly
    latest_obs = data['obs'][0]
    print("Using observation data from data['obs'][0]")

    # --- Extract Data (Using keys from the API response) ---
    timestamp_epoch = latest_obs.get('timestamp')
    wind_lull_mps = latest_obs.get('wind_lull')
    wind_avg_mps = latest_obs.get('wind_avg')
    wind_gust_mps = latest_obs.get('wind_gust')
    wind_direction_deg = latest_obs.get('wind_direction')
    # Use station_pressure, fall back to barometric_pressure if needed
    pressure_mb = latest_obs.get('station_pressure', latest_obs.get('barometric_pressure'))
    temp_c = latest_obs.get('air_temperature')
    humidity_pct = latest_obs.get('relative_humidity')
    illuminance_lux = latest_obs.get('brightness')
    uv_index = latest_obs.get('uv')
    solar_radiation_wm2 = latest_obs.get('solar_radiation')
    # 'precip' seems to be instantaneous rate in mm/min based on API docs
    rain_accum_last_min_mm = latest_obs.get('precip', 0.0) # Default to 0 if missing
    # The target API structure doesn't provide a direct real-time precip_type (0, 1, 2). Defaulting to 0 (none).
    precip_type = 0
    # Use final daily rain if available, otherwise use current daily rain
    daily_rain_accum_mm = latest_obs.get('precip_accum_local_day_final', latest_obs.get('precip_accum_local_day'))
    # Battery voltage is not available in this API response structure

    # Check if essential data is missing
    if timestamp_epoch is None or temp_c is None or pressure_mb is None:
        print(f"Error: Essential data (timestamp, temperature, pressure) missing from observation: {latest_obs}")
        exit(1)

    # --- Format Output Data ---
    output_data = {
        "timestamp_utc": datetime.utcfromtimestamp(timestamp_epoch).isoformat() + "Z" if timestamp_epoch else None,
        "temperature_f": celsius_to_fahrenheit(temp_c),
        "humidity_percent": round(humidity_pct, 1) if humidity_pct is not None else None,
        "wind_speed_mph": mps_to_mph(wind_avg_mps),
        "wind_gust_mph": mps_to_mph(wind_gust_mps),
        "wind_direction_cardinal": get_wind_direction_cardinal(wind_direction_deg),
        "wind_direction_degrees": wind_direction_deg,
        "uv_index": round(uv_index, 1) if uv_index is not None else None,
        "rain_rate_in_hr": mm_to_inches(rain_accum_last_min_mm * 60) if rain_accum_last_min_mm is not None else 0.0, # Approximate hourly rate
        "daily_rain_in": mm_to_inches(daily_rain_accum_mm),
        "pressure_inhg": mb_to_inhg(pressure_mb),
        "illuminance_lux": illuminance_lux,
        "solar_radiation_wm2": solar_radiation_wm2,
        # Battery voltage removed as it's not in the API response
        "precip_type": "rain" if precip_type == 1 else ("hail" if precip_type == 2 else "none") # Will always be "none" based on current logic
    }

    # --- Write to JSON File ---
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Successfully fetched data and wrote to {OUTPUT_FILE}")
    print(json.dumps(output_data, indent=2)) # Print data to Action log

except requests.exceptions.RequestException as e:
    print(f"Error fetching data from WeatherFlow API: {e}")
    exit(1)
except (KeyError, IndexError, TypeError) as e:
    print(f"Error parsing API response: {e}")
    print(f"Raw response data: {response.text}") # Print raw text in case of JSON parsing error
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

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

    # Get the latest 'obs_st' observation (Tempest device)
    latest_obs_st = None
    for obs_data in data['obs']:
         if obs_data.get('type') == 'obs_st':
              latest_obs_st = obs_data
              break # Use the first (most recent) one found

    if not latest_obs_st or 'obs' not in latest_obs_st or not latest_obs_st['obs']:
         print("Error: No 'obs_st' type observation found in the station data.")
         # Fallback or alternative handling could go here if needed
         # For now, let's try finding *any* observation if obs_st isn't present
         if data['obs'] and data['obs'][0].get('obs'):
             print("Falling back to first available observation set.")
             obs_values = data['obs'][0]['obs'][0] # Use the first observation set available
             obs_type = data['obs'][0].get('type', 'unknown')
             print(f"Using observation type: {obs_type}")
         else:
             print("Error: No usable observation data found at all.")
             exit(1)
    else:
        obs_values = latest_obs_st['obs'][0] # obs_st has a nested obs array
        print("Using 'obs_st' observation data.")


    # --- Extract Data (Index based on obs_st documentation) ---
    # obs_st: [epoch, lull, avg, gust, dir, interval, pressure, temp, rh, lux, uv, solar, rain_min, precip_type, strike_dist, strike_count, battery, interval, daily_rain, rain_final, daily_rain_final, precip_analysis]
    timestamp_epoch = obs_values[0]
    wind_lull_mps = obs_values[1]
    wind_avg_mps = obs_values[2]
    wind_gust_mps = obs_values[3]
    wind_direction_deg = obs_values[4]
    pressure_mb = obs_values[6]
    temp_c = obs_values[7]
    humidity_pct = obs_values[8]
    illuminance_lux = obs_values[9]
    uv_index = obs_values[10]
    solar_radiation_wm2 = obs_values[11]
    rain_accum_last_min_mm = obs_values[12]
    precip_type = obs_values[13] # 0=none, 1=rain, 2=hail
    # strike_dist_km = obs_values[14] # Not requested
    # strike_count = obs_values[15] # Not requested
    battery_v = obs_values[16]
    daily_rain_accum_mm = obs_values[18]
    # Use final rain values if available (from Rain Check)
    if len(obs_values) > 19 and obs_values[19] is not None:
        rain_accum_last_min_mm = obs_values[19]
    if len(obs_values) > 20 and obs_values[20] is not None:
        daily_rain_accum_mm = obs_values[20]

    # --- Format Output Data ---
    output_data = {
        "timestamp_utc": datetime.utcfromtimestamp(timestamp_epoch).isoformat() + "Z",
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
        "battery_volts": round(battery_v, 2) if battery_v is not None else None,
        "precip_type": "rain" if precip_type == 1 else ("hail" if precip_type == 2 else "none")
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
    print(f"Raw response data: {data}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

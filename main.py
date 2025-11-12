from arduino.app_utils import *

import requests
from datetime import datetime
 

def get_temperature():
    api_key = "033e4af2c403c176f2a262ad63af4565"
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": "Neratovice", "appid": api_key}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Error fetching weather data: {exc}") from exc

    # Extract temperature in Kelvin and convert to Celsius
    main = data.get("main") or {}
    temp_k = main.get("temp")
    if temp_k is None:
        raise RuntimeError("Temperature not found in API response")

    temp_c = round(temp_k - 273.15)
    
    # Log the temperature
    print(f"Current temperature: {temp_c}°C")
  
    return temp_c


def get_conditions():
    api_key = "033e4af2c403c176f2a262ad63af4565"
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": "Neratovice", "appid": api_key}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Error fetching weather data: {exc}") from exc

    # Extract weather conditions
    weather = data.get("weather")
    if not weather or len(weather) == 0:
        raise RuntimeError("Weather conditions not found in API response")
    
    condition = weather[0].get("main", "Unknown")
    description = weather[0].get("description", "")
    
    # Log the conditions
    print(f"Current conditions: {condition} ({description})")
    
    return condition


def get_time():
    # Get timezone offset and calculate local time
    timezone_offset = 3600
    utc_now = datetime.utcnow()
    
    # Add timezone offset
    from datetime import timedelta
    local_time = utc_now + timedelta(seconds=timezone_offset)
    
    # Format as HH:MM (24-hour format)
    time_str = local_time.strftime("%H:%M")
    
    print(f"Current time: {time_str}")
    
    return time_str


if __name__ == "__main__":
    temperature = get_temperature()
    print(f"Temperature in Neratovice: {temperature}°C")
    
    conditions = get_conditions()
    print(f"Weather conditions in Neratovice: {conditions}")
    
    current_time = get_time()
    print(f"Current time in Neratovice: {current_time}")

Bridge.provide("get_temperature", get_temperature)
Bridge.provide("get_conditions", get_conditions)
Bridge.provide("get_time", get_time)

App.run()
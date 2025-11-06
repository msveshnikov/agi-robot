
from arduino.app_utils import *

import requests
 

def get_temperature():
    api_key = "ea134c3b959845c1383c4125eb380b2f"
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


# Allow the microcontroller to call the "get_air_quality" function to show AQI level on led matrix
Bridge.provide("get_temperature", get_temperature)

App.run()

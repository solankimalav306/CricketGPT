from datetime import date

import requests


# ==================================================
# GEOCODING
# ==================================================

def get_coordinates(city):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    response = requests.get(
        url,
        params={
            "name": city,
            "count": 1
        },
        timeout=10
    )
    print(f"[Weather] Requesting coordinates for {city}")
    response.raise_for_status()

    results = response.json().get("results", [])
    print(f"[Weather] lat: {results[0]['latitude']}, lon: {results[0]['longitude']} for {city}")
    if not results:
        raise ValueError(f"City not found: {city}")

    place = results[0]

    return (
        place["latitude"],
        place["longitude"]
    )


# ==================================================
# WEATHER
# ==================================================

def get_weather(weather_request):

    city = weather_request["city"]
    date = weather_request["date"]

    lat, lon = get_coordinates(city)

    url = "https://api.open-meteo.com/v1/forecast"

    WEATHER_PARAMETERS = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "wind_speed_10m",
        "precipitation_probability",
        "precipitation",
        "weather_code",
    ]

    response = requests.get(
        url,
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(WEATHER_PARAMETERS),
            "start_date": date,
            "end_date": date,
            "timezone": "auto"
        },
        timeout=10
    )
    print(f"[Weather] Requesting weather for {city} on {date} (lat: {lat}, lon: {lon})")
    response.raise_for_status()

    data = response.json()["hourly"]

    # Midday representative conditions
    idx = 12
    print(f"[Weather] Weather data for {city} on {date}: {data['temperature_2m'][idx]}°C, {data['weather_code'][idx]}, {data['precipitation'][idx]}mm, {data['wind_speed_10m'][idx]}m/s, {data['relative_humidity_2m'][idx]}% humidity, {data['dew_point_2m'][idx]}°C dew point, {data['precipitation_probability'][idx]}% chance of rain")
    return {
        "city": city,
        "date": date,
        "temperature": data["temperature_2m"][idx],
        "humidity": data["relative_humidity_2m"][idx],
        "dew_point": data["dew_point_2m"][idx],
        "wind_speed": data["wind_speed_10m"][idx],
        "rain_probability": data["precipitation_probability"][idx],
        "rain_mm": data["precipitation"][idx],
        "weather_code": data["weather_code"][idx]
    }
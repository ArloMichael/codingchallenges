import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tooling import Tool, ToolError


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 5
MAX_LOCATION_LENGTH = 120
MAX_FORECAST_DAYS = 7

class WeatherToolError(ToolError):
    pass


def _get_json(url, params):
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={"User-Agent": "local-voice-assistant/1.0"},
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise WeatherToolError(
            f"The weather service returned HTTP {error.code}."
        ) from error
    except (URLError, TimeoutError) as error:
        raise WeatherToolError(
            "The weather service is currently unavailable."
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WeatherToolError(
            "The weather service returned an invalid response."
        ) from error

    if not isinstance(payload, dict):
        raise WeatherToolError("The weather service returned an invalid response.")

    if payload.get("error"):
        reason = str(payload.get("reason") or "The request was rejected.")
        raise WeatherToolError(reason[:200])

    return payload


def _weather_description(code):
    descriptions = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "freezing fog",
        51: "light drizzle",
        53: "drizzle",
        55: "heavy drizzle",
        56: "light freezing drizzle",
        57: "heavy freezing drizzle",
        61: "light rain",
        63: "rain",
        65: "heavy rain",
        66: "light freezing rain",
        67: "heavy freezing rain",
        71: "light snow",
        73: "snow",
        75: "heavy snow",
        77: "snow grains",
        80: "light rain showers",
        81: "rain showers",
        82: "heavy rain showers",
        85: "light snow showers",
        86: "heavy snow showers",
        95: "thunderstorms",
        96: "thunderstorms with light hail",
        99: "thunderstorms with heavy hail",
    }

    try:
        return descriptions.get(int(code), "unknown conditions")
    except (TypeError, ValueError):
        return "unknown conditions"


def _format_location(place):
    parts = [place.get("name"), place.get("admin1"), place.get("country")]
    unique_parts = []

    for part in parts:
        if part and part not in unique_parts:
            unique_parts.append(str(part))

    return ", ".join(unique_parts)


def get_weather(location, days=3):
    if not isinstance(location, str):
        raise WeatherToolError("Location must be text.")

    location = " ".join(location.split())
    if not location:
        raise WeatherToolError("A location is required.")
    if len(location) > MAX_LOCATION_LENGTH:
        raise WeatherToolError("The location is too long.")

    if isinstance(days, bool) or not isinstance(days, int):
        raise WeatherToolError("Forecast days must be a whole number.")
    if not 1 <= days <= MAX_FORECAST_DAYS:
        raise WeatherToolError(
            f"Forecast days must be between 1 and {MAX_FORECAST_DAYS}."
        )

    geocoding = _get_json(
        GEOCODING_URL,
        {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json",
        },
    )
    matches = geocoding.get("results") or []

    if not matches:
        raise WeatherToolError(f"No location was found for {location}.")

    place = matches[0]
    forecast = _get_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "timezone": "auto",
            "forecast_days": days,
            "current": ",".join(
                [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                ]
            ),
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                ]
            ),
        },
    )

    current = forecast.get("current") or {}
    current_units = forecast.get("current_units") or {}
    daily = forecast.get("daily") or {}
    forecast_days = []

    for index, date in enumerate(daily.get("time") or []):
        forecast_days.append(
            {
                "date": date,
                "conditions": _weather_description(
                    _item_at(daily.get("weather_code"), index)
                ),
                "minimum_temperature": _measurement(
                    _item_at(daily.get("temperature_2m_min"), index),
                    (forecast.get("daily_units") or {}).get("temperature_2m_min"),
                ),
                "maximum_temperature": _measurement(
                    _item_at(daily.get("temperature_2m_max"), index),
                    (forecast.get("daily_units") or {}).get("temperature_2m_max"),
                ),
                "maximum_precipitation_probability": _measurement(
                    _item_at(daily.get("precipitation_probability_max"), index),
                    (forecast.get("daily_units") or {}).get(
                        "precipitation_probability_max"
                    ),
                ),
            }
        )

    return {
        "location": _format_location(place),
        "timezone": forecast.get("timezone"),
        "current": {
            "time": current.get("time"),
            "conditions": _weather_description(current.get("weather_code")),
            "temperature": _measurement(
                current.get("temperature_2m"),
                current_units.get("temperature_2m"),
            ),
            "feels_like": _measurement(
                current.get("apparent_temperature"),
                current_units.get("apparent_temperature"),
            ),
            "relative_humidity": _measurement(
                current.get("relative_humidity_2m"),
                current_units.get("relative_humidity_2m"),
            ),
            "precipitation": _measurement(
                current.get("precipitation"),
                current_units.get("precipitation"),
            ),
            "wind_speed": _measurement(
                current.get("wind_speed_10m"),
                current_units.get("wind_speed_10m"),
            ),
        },
        "forecast": forecast_days,
    }


def _item_at(values, index):
    if isinstance(values, list) and index < len(values):
        return values[index]
    return None


def _measurement(value, unit):
    if value is None:
        return None
    return {"value": value, "unit": unit}


WEATHER_TOOL = Tool(
    name="get_weather",
    description=(
        "Get live current conditions and a daily weather forecast for a named "
        "location. Use this for all current or future weather questions."
    ),
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": (
                    "A city with its state or country when known, "
                    "for example Sydney, Australia."
                ),
            },
            "days": {
                "type": "integer",
                "description": (
                    "Number of forecast days to return, from 1 to 7. "
                    "Use 2 for tomorrow and 7 for the coming week."
                ),
                "minimum": 1,
                "maximum": MAX_FORECAST_DAYS,
            },
        },
        "required": ["location"],
    },
    handler=get_weather,
)

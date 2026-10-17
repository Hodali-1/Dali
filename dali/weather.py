"""Current weather from OpenWeatherMap.

Reads the API key from the OPENWEATHER_API_KEY environment variable, never from code.
Returns None on any failure so the briefing can say the weather is unavailable.
"""

import json
import os
import time
import urllib.parse
import urllib.request

from .briefing import Weather

API_URL = "https://api.openweathermap.org/data/2.5/weather"
CACHE_SECONDS = 30 * 60  # refresh at most every 30 minutes

_cache: dict = {"at": 0.0, "location": None, "value": None}


def _summarise(condition: str) -> str:
    """Turn OpenWeatherMap's main condition into a plain phrase for speech."""
    mapping = {
        "Clear": "clear",
        "Clouds": "cloudy",
        "Rain": "rainy",
        "Drizzle": "drizzly",
        "Thunderstorm": "stormy",
        "Mist": "misty",
        "Fog": "foggy",
        "Haze": "hazy",
    }
    return mapping.get(condition, condition.lower())


def parse_response(payload: dict) -> Weather:
    """Build a Weather object from an OpenWeatherMap JSON response."""
    condition = payload["weather"][0]["main"]
    temp = round(payload["main"]["temp"])
    return Weather(summary=_summarise(condition), temperature_c=temp)


def fetch_weather(location: str = "Kigali,RW", api_key: str | None = None) -> Weather | None:
    key = api_key or os.environ.get("OPENWEATHER_API_KEY", "")
    if not key:
        return None

    now = time.time()
    if (
        _cache["value"] is not None
        and _cache["location"] == location
        and now - _cache["at"] < CACHE_SECONDS
    ):
        return _cache["value"]

    query = urllib.parse.urlencode({"q": location, "units": "metric", "appid": key})
    try:
        with urllib.request.urlopen(f"{API_URL}?{query}", timeout=10) as resp:
            weather = parse_response(json.loads(resp.read().decode("utf-8")))
    except Exception:
        return None

    _cache.update({"at": now, "location": location, "value": weather})
    return weather

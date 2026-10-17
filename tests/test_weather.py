from dali.weather import fetch_weather, parse_response


SAMPLE = {
    "weather": [{"main": "Clouds", "description": "scattered clouds"}],
    "main": {"temp": 23.6},
}


def test_parse_response_maps_condition_and_rounds_temperature():
    w = parse_response(SAMPLE)
    assert w.summary == "cloudy"
    assert w.temperature_c == 24


def test_unknown_condition_falls_back_to_lowercase():
    payload = {"weather": [{"main": "Squall"}], "main": {"temp": 18}}
    assert parse_response(payload).summary == "squall"


def test_no_key_returns_none_without_network(monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    assert fetch_weather("Kigali,RW") is None

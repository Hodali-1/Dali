"""Builds the spoken morning briefing."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Event:
    start: datetime
    title: str
    important: bool = False
    location: str | None = None


@dataclass(frozen=True)
class Weather:
    summary: str          # e.g. "sunny"
    temperature_c: int


def _time_phrase(dt: datetime) -> str:
    hour = dt.hour % 12 or 12
    minute = dt.minute
    suffix = "AM" if dt.hour < 12 else "PM"
    if minute == 0:
        return f"{hour} {suffix}"
    return f"{hour}:{minute:02d} {suffix}"


def build_briefing(
    today: date,
    weather: Weather | None,
    events: list[Event],
    owner_name: str = "",
) -> str:
    """Return the text DALI speaks. Important events come first, then the rest in time order."""
    greeting = f"Wakey wakey{', ' + owner_name if owner_name else ''}. "
    date_line = f"It's {today.strftime('%A, %B')} {today.day}. "

    if weather:
        weather_line = f"The weather today is {weather.summary}, around {weather.temperature_c} degrees. "
    else:
        weather_line = "I couldn't get the weather right now. "

    if not events:
        schedule_line = "You have nothing scheduled today. "
    else:
        ordered = sorted(events, key=lambda e: (not e.important, e.start))
        count = len(events)
        parts = []
        for e in ordered:
            where = f" at {e.location}" if e.location else ""
            flag = "This one is important: " if e.important else ""
            parts.append(f"{flag}{e.title} at {_time_phrase(e.start)}{where}.")
        noun = "thing" if count == 1 else "things"
        schedule_line = f"You have {count} {noun} today. " + " ".join(parts) + " "

    closing = "Press 1 on your keypad to confirm you're awake."
    return greeting + date_line + weather_line + schedule_line + closing

"""Wake-up call scheduling logic.

Pure functions only: no network, no clock reads inside the logic.
The caller passes `now` explicitly, which keeps this easy to test.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .config import WakeConfig


@dataclass
class WakeState:
    day: date
    confirmed_at: datetime | None = None
    attempts: list[datetime] = field(default_factory=list)

    @property
    def confirmed(self) -> bool:
        return self.confirmed_at is not None


def attempt_times(config: WakeConfig, day: date) -> list[datetime]:
    """All scheduled call times for one day, in the owner's timezone."""
    times = []
    current = datetime.combine(day, config.first_call, tzinfo=config.tz)
    stop = datetime.combine(day, config.stop_at, tzinfo=config.tz)
    step = timedelta(minutes=config.retry_every_minutes)
    while current < stop:
        times.append(current)
        current += step
    return times


def next_call(config: WakeConfig, state: WakeState, now: datetime) -> datetime | None:
    """Return the next call time that is due, or None if no more calls are needed.

    A call is due when its scheduled time has passed and it has not been placed yet.
    Returns None once the owner has confirmed, or after the window closes.
    """
    if state.confirmed:
        return None
    for scheduled in attempt_times(config, state.day):
        if scheduled not in state.attempts and scheduled <= now:
            return scheduled
    return None


def record_attempt(state: WakeState, scheduled: datetime) -> None:
    if scheduled not in state.attempts:
        state.attempts.append(scheduled)


def confirm(state: WakeState, at: datetime) -> None:
    """Owner proved they are awake (key press or valid photo). Stops all further calls."""
    if state.confirmed_at is None:
        state.confirmed_at = at


def window_closed(config: WakeConfig, state: WakeState, now: datetime) -> bool:
    stop = datetime.combine(state.day, config.stop_at, tzinfo=config.tz)
    return now >= stop

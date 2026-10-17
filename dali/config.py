"""Owner and timing settings for DALI."""

from dataclasses import dataclass, field
from datetime import time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class WakeConfig:
    timezone: str = "Africa/Kigali"
    first_call: time = time(7, 0)
    retry_every_minutes: int = 10
    stop_at: time = time(8, 0)  # exclusive: no call is placed at or after this time
    weather_location: str = "Kigali, Rwanda"
    ambience_file: str = "audio/morning_birds.mp3"
    photo_prompts: tuple = field(
        default=(
            "Take a photo of the weather outside your window.",
            "Take a photo of your kitchen.",
            "Take a photo of the room you're in right now.",
        )
    )

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

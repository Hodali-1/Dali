"""Photo-proof confirmation: choosing a prompt and checking the uploaded image.

`looks_like_match` is a stub that only checks the file is a real image.
The real check should send the photo and the requested subject to a vision model.
"""

import random

from .config import WakeConfig

_IMAGE_SIGNATURES = (
    b"\xff\xd8\xff",          # JPEG
    b"\x89PNG\r\n\x1a\n",     # PNG
    b"RIFF",                  # WebP (checked further below)
)


def pick_photo_prompt(config: WakeConfig, rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    return rng.choice(config.photo_prompts)


def is_image_bytes(data: bytes) -> bool:
    if data.startswith(_IMAGE_SIGNATURES[0]) or data.startswith(_IMAGE_SIGNATURES[1]):
        return True
    return data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def looks_like_match(data: bytes, prompt: str) -> bool:
    """Placeholder check: accepts any real image. Replace with a vision-model check."""
    return len(data) > 1024 and is_image_bytes(data)

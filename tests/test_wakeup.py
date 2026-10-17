import random
from datetime import date, datetime, timedelta

from dali.audio import ambience_mix_command
from dali.briefing import Event, Weather, build_briefing
from dali.config import WakeConfig
from dali.confirm import is_image_bytes, looks_like_match, pick_photo_prompt
from dali.scheduler import (
    WakeState,
    attempt_times,
    confirm,
    next_call,
    record_attempt,
    window_closed,
)

CFG = WakeConfig()
DAY = date(2026, 10, 20)  # a Tuesday


def at(h, m=0):
    return datetime(DAY.year, DAY.month, DAY.day, h, m, tzinfo=CFG.tz)


def test_attempts_every_10_minutes_from_7_until_8():
    times = attempt_times(CFG, DAY)
    assert times[0] == at(7, 0)
    assert times[-1] == at(7, 50)
    assert len(times) == 6
    assert at(8, 0) not in times


def test_no_call_before_first_time():
    state = WakeState(day=DAY)
    assert next_call(CFG, state, at(6, 59)) is None


def test_first_call_due_at_7():
    state = WakeState(day=DAY)
    assert next_call(CFG, state, at(7, 0)) == at(7, 0)


def test_retry_only_after_previous_attempt_recorded():
    state = WakeState(day=DAY)
    record_attempt(state, at(7, 0))
    assert next_call(CFG, state, at(7, 5)) is None
    assert next_call(CFG, state, at(7, 10)) == at(7, 10)


def test_confirmation_stops_all_calls():
    state = WakeState(day=DAY)
    record_attempt(state, at(7, 0))
    confirm(state, at(7, 3))
    assert next_call(CFG, state, at(7, 20)) is None


def test_window_closes_at_8():
    state = WakeState(day=DAY)
    assert not window_closed(CFG, state, at(7, 59))
    assert window_closed(CFG, state, at(8, 0))


def test_timezone_is_kigali_utc_plus_2():
    # 07:00 Kigali is 05:00 UTC
    assert at(7, 0).utcoffset() == timedelta(hours=2)
    assert at(7, 0).astimezone(CFG.tz).hour == 7


def test_briefing_puts_important_first_and_counts():
    events = [
        Event(at(9, 0), "Team sync"),
        Event(at(14, 30), "Call with investor", important=True, location="Zoom"),
    ]
    text = build_briefing(DAY, Weather("sunny", 24), events, owner_name="Basile")
    assert "Wakey wakey, Basile." in text
    assert "Tuesday, October 20" in text
    assert "2 things today" in text
    assert text.index("Call with investor") < text.index("Team sync")
    assert "This one is important" in text
    assert "Press 1" in text


def test_briefing_empty_schedule_and_no_weather():
    text = build_briefing(DAY, None, [])
    assert "nothing scheduled" in text
    assert "couldn't get the weather" in text


def test_photo_prompt_comes_from_config():
    prompt = pick_photo_prompt(CFG, random.Random(1))
    assert prompt in CFG.photo_prompts


def test_image_detection():
    jpeg = b"\xff\xd8\xff" + b"\x00" * 2000
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 2000
    text = b"hello world" * 300
    assert is_image_bytes(jpeg)
    assert is_image_bytes(png)
    assert not is_image_bytes(text)
    assert looks_like_match(jpeg, "Take a photo of your kitchen.")
    assert not looks_like_match(b"\xff\xd8\xff", "Take a photo of your kitchen.")


def test_ambience_command_loops_and_mixes():
    cmd = ambience_mix_command("voice.mp3", "birds.mp3", "out.mp3")
    assert cmd[0] == "ffmpeg"
    assert "-stream_loop" in cmd
    assert "amix=inputs=2" in " ".join(cmd)

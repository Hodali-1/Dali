"""DALI server: Render web service + Plivo voice.

Responsibilities:
- A background scheduler places wake-up calls (07:00, then every 10 min until 08:00)
  until the owner presses 1.
- Plivo calls these endpoints during a call: /plivo/answer (speak briefing)
  and /plivo/digits (handle the key press).

Single-instance design: state lives in memory, so run ONE gunicorn worker.
"""

import os
import threading
import time
from datetime import date, datetime
from xml.sax.saxutils import escape

from flask import Flask, Response, request

from dali.briefing import Weather, build_briefing
from dali.config import WakeConfig
from dali.scheduler import WakeState, confirm, next_call, record_attempt, window_closed

app = Flask(__name__)
CONFIG = WakeConfig()

PLIVO_AUTH_ID = os.environ.get("PLIVO_AUTH_ID", "")
PLIVO_AUTH_TOKEN = os.environ.get("PLIVO_AUTH_TOKEN", "")
PLIVO_FROM = os.environ.get("PLIVO_FROM", "")        # your Plivo number, e.g. +1xxxxxxxxxx
OWNER_PHONE = os.environ.get("OWNER_PHONE", "")      # your phone, e.g. +250xxxxxxxxx
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")  # e.g. https://dali.onrender.com
OWNER_NAME = os.environ.get("OWNER_NAME", "")
ENABLE_SCHEDULER = os.environ.get("ENABLE_SCHEDULER", "1") == "1"

_state_lock = threading.Lock()
_state: WakeState | None = None


def _today_state(now: datetime) -> WakeState:
    """Return today's wake state, creating a fresh one at the start of each day."""
    global _state
    local_day = now.astimezone(CONFIG.tz).date()
    if _state is None or _state.day != local_day:
        _state = WakeState(day=local_day)
    return _state


def _now() -> datetime:
    return datetime.now(CONFIG.tz)


def _fetch_weather() -> Weather | None:
    """Placeholder until an OpenWeatherMap key is added. Returns None so the briefing says so."""
    return None


def _fetch_events(day: date) -> list:
    """Placeholder until Google Calendar is connected. Returns no events."""
    return []


def _place_call() -> None:
    import plivo

    if not (PLIVO_AUTH_ID and PLIVO_AUTH_TOKEN and PLIVO_FROM and OWNER_PHONE and PUBLIC_BASE_URL):
        app.logger.error("Plivo settings missing; cannot place call")
        return
    client = plivo.RestClient(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN)
    client.calls.create(
        from_=PLIVO_FROM,
        to_=OWNER_PHONE,
        answer_url=f"{PUBLIC_BASE_URL}/plivo/answer",
        answer_method="POST",
    )


def _scheduler_loop() -> None:
    while True:
        try:
            now = _now()
            with _state_lock:
                state = _today_state(now)
                due = next_call(CONFIG, state, now)
                if due is not None:
                    record_attempt(state, due)
                    app.logger.info("Placing wake-up call scheduled for %s", due)
                    _place_call()
        except Exception:
            app.logger.exception("Scheduler error")
        time.sleep(30)


def _start_scheduler() -> None:
    if ENABLE_SCHEDULER:
        threading.Thread(target=_scheduler_loop, daemon=True).start()


def _xml(body: str) -> Response:
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>',
                    mimetype="text/xml")


@app.get("/health")
def health():
    return {"status": "ok", "time": _now().isoformat()}


@app.route("/plivo/answer", methods=["POST", "GET"])
def plivo_answer():
    now = _now()
    with _state_lock:
        state = _today_state(now)
        if state.confirmed or window_closed(CONFIG, state, now):
            return _xml("<Speak>Okay, I'll leave you alone. Have a good day.</Speak><Hangup/>")

    today = now.date()
    text = build_briefing(today, _fetch_weather(), _fetch_events(today), owner_name=OWNER_NAME)
    action = f"{PUBLIC_BASE_URL}/plivo/digits"
    return _xml(
        f'<GetDigits action="{escape(action)}" method="POST" numDigits="1" timeout="15">'
        f"<Speak>{escape(text)}</Speak></GetDigits>"
        "<Speak>I didn't hear you. I'll call you again soon.</Speak><Hangup/>"
    )


@app.route("/plivo/digits", methods=["POST", "GET"])
def plivo_digits():
    digits = request.values.get("Digits", "")
    now = _now()
    if digits == "1":
        with _state_lock:
            confirm(_today_state(now), now)
        return _xml("<Speak>Good morning. Have a great day.</Speak><Hangup/>")
    return _xml("<Speak>Please press 1 to confirm you're awake.</Speak><Hangup/>")


_start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))

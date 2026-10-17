# DALI — Personal Assistant (living spec)

Status: Module 1 (morning wake-up) in progress. Living document; update as features are added.

## Goal

DALI is a personal voice assistant. It calls the owner in the morning, reads the day's plan, keeps calling until the owner proves they are awake, and later will take on-demand requests (schedule meetings, find files, answer email with approval).

## Module 1: Morning wake-up

### Timing
- Timezone: Africa/Kigali (UTC+2, no daylight saving).
- First call: 07:00.
- Retry every 10 minutes: 07:10, 07:20, … 07:50.
- Last attempt window closes at 08:00 (08:00 itself is not called).
- Any confirmation stops all further calls immediately.

### Call script
1. Background ambience plays first (birdsong / soft morning sound) mixed under the voice, so waking feels gentle.
2. Greeting, e.g. "Wakey wakey. It's Tuesday, October 20."
3. Weather for the owner's location (default Kigali unless changed).
4. Today's schedule, most important items first.
5. Confirmation request.

### Confirming awake (two options, either one stops the calls)
- Key press: press 1 on the phone during the call. Most reliable.
- Photo proof: DALI asks for a photo of something specific (for example the weather outside, the kitchen, or a room). The owner uploads it through a simple phone web page. A vision check confirms the photo matches the request. A photo that does not match asks again.

Retries stop on the first valid confirmation. If nothing confirms by 08:00, DALI sends one text message summarising the day and logs the miss.

### Channel
Adapter pattern: the calling channel is pluggable. Default target is a regular phone call through Twilio, because WhatsApp Business calling has business-initiated limits that could block repeated wake-up calls. WhatsApp can be added as a second adapter later.

### Components
- `dali/config.py` — timing and owner settings.
- `dali/scheduler.py` — pure logic: which call attempts are due, and when to stop.
- `dali/briefing.py` — builds the spoken briefing text from date, weather and events.
- `dali/confirm.py` — photo request wording and photo validation.
- `dali/audio.py` — builds the ffmpeg command that mixes ambience under the voice.
- `tests/` — unit tests for timing, stop conditions, briefing and confirmation.

### Open items
- Weather provider and API key.
- Telephony provider account (Twilio) and phone number.
- Text-to-speech voice choice.
- Google Calendar OAuth setup (needed for real schedule data; demo uses sample events).

## Backlog (ideas to add later)
- On-demand inbound calls: "Dali, schedule this meeting."
- Find files on laptop or phone by description.
- Email drafting with approval before sending.
- Important-item highlighting across the full day.

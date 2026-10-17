"""Builds the ffmpeg command that mixes the spoken briefing over background ambience."""

from pathlib import Path


def ambience_mix_command(
    voice_file: str | Path,
    ambience_file: str | Path,
    output_file: str | Path,
    ambience_volume: float = 0.25,
) -> list[str]:
    """Return an ffmpeg argument list. Ambience loops under the voice and stops with it.

    Run with subprocess.run(cmd, check=True).
    """
    return [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", str(ambience_file),
        "-i", str(voice_file),
        "-filter_complex",
        f"[0:a]volume={ambience_volume}[bg];"
        "[bg][1:a]amix=inputs=2:duration=second:dropout_transition=0[out]",
        "-map", "[out]",
        str(output_file),
    ]

"""Parse clip start times from form values and YouTube links."""

import math
import re
from urllib.parse import parse_qs, urlsplit

INVALID_TIME = "Use seconds, mm:ss, or hh:mm:ss for the start time."


def parse_seconds(text: str) -> float:
    """Read a non-negative number of seconds."""
    if not re.fullmatch(r"\d+(?:\.\d+)?", text):
        raise ValueError(INVALID_TIME)
    return float(text)


def parse_clock_time(text: str) -> float:
    """Read mm:ss or hh:mm:ss with valid minute and second fields."""
    if not re.fullmatch(r"\d+(?::\d{1,2}){1,2}(?:\.\d+)?", text):
        raise ValueError(INVALID_TIME)
    parts = [float(part) for part in text.split(":")]
    if any(part >= 60 for part in parts[1:]):
        raise ValueError(INVALID_TIME)
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def parse_youtube_time(text: str) -> float:
    """Read YouTube's optional h, m, and s suffixes."""
    match = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", text)
    if not match or not any(match.groups()):
        raise ValueError(INVALID_TIME)
    hours, minutes, seconds = (float(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def validate_seconds(seconds: float) -> float:
    """Reject non-finite input and keep millisecond precision."""
    if not math.isfinite(seconds):
        raise ValueError("Enter a finite, non-negative start time.")
    return round(seconds, 3)


def parse_start_time(value: str | float | None) -> float:
    """Convert a supported timestamp to seconds; empty input starts at zero."""
    text = str(value).strip() if value is not None else ""
    if not text:
        return 0.0
    if ":" in text:
        return validate_seconds(parse_clock_time(text))
    if text.endswith(("h", "m", "s")):
        return validate_seconds(parse_youtube_time(text))
    return validate_seconds(parse_seconds(text))


def clip_start(data: dict, source: str, url: str) -> float:
    """Prefer an explicit form value over the YouTube link timestamp."""
    if data.get("startSeconds") not in (None, ""):
        return parse_start_time(data["startSeconds"])
    if source != "youtube":
        return 0.0
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    fragment = parse_qs(parsed.fragment)
    timestamp = query.get("t") or query.get("start") or fragment.get("t")
    return parse_start_time(timestamp[0]) if timestamp else 0.0

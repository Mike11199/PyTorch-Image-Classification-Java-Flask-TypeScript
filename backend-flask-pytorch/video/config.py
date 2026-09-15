"""Video limits and server-provided examples."""

import os
from .quality import DEFAULT_MASK_QUALITY, MASK_QUALITIES

MAX_SECONDS = 10
MAX_FRAME_EDGE = 640
CHUNK_FRAMES = 10
PREVIEW_INTERVAL_SECONDS = 2
TERMINAL = {"completed", "failed", "cancelled"}

EXAMPLES = [
    {
        "id": "youtube-VjmUlxRamwg-7572",
        "name": "New York City in rain",
        "url": "https://youtu.be/VjmUlxRamwg?t=7572",
        "source": "youtube",
    },
    {
        "id": "youtube-eGr0Fm3X5YE-1845",
        "name": "Chicago in winter",
        "url": "https://youtu.be/eGr0Fm3X5YE?t=1845",
        "source": "youtube",
    },
]


def youtube_enabled() -> bool:
    """Allow fresh YouTube imports only when configured."""
    return os.getenv("VIDEO_YOUTUBE_ENABLED", "true") == "true"


def allowed_url_hosts() -> list[str]:
    """Read the operator's allowed direct-download hosts."""
    return os.getenv("VIDEO_URL_HOSTS", "assets.machine-learning-projects.com").split(
        ","
    )


def video_config() -> dict:
    """Expose supported inputs and limits to the form."""
    return {
        "maxSeconds": MAX_SECONDS,
        "maxFrameEdge": MAX_FRAME_EDGE,
        "defaultMaskQuality": DEFAULT_MASK_QUALITY,
        "maskQualities": MASK_QUALITIES,
        "examples": EXAMPLES,
        "youtubeEnabled": youtube_enabled(),
        "urlHosts": allowed_url_hosts(),
    }

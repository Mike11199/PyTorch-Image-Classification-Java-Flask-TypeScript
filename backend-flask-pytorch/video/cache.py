"""Public URL cache identity. Bump the recipe whenever inference/output changes."""

import hashlib
import re
from urllib.parse import parse_qs, urlsplit, urlunsplit

from .sources.youtube import validate_youtube_url
from .quality import job_mask_quality

RECIPE = "mask-rcnn-v3:clip10:playback-original:model-native:score0.9:mask0.5:top20:atlas10"


def youtube_video_id(url):
    """Treat watch, share, and shorts links to the same video as one source."""
    parsed = validate_youtube_url(url)
    parts = parsed.path.strip("/").split("/")
    if parsed.hostname == "youtu.be":
        video_id = parts[0]
    elif len(parts) == 2 and parts[0] in {"shorts", "embed", "live"}:
        video_id = parts[1]
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    else:
        video_id = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Enter a YouTube video link, not a playlist or channel.")
    return video_id


def cache_key(source, url, start_seconds=0, mask_quality="detailed"):
    """Identify a public URL and recipe; uploads never share the URL cache."""
    if source == "upload":
        return None
    if source == "youtube":
        identity = "youtube:" + youtube_video_id(url)
    else:
        parsed = urlsplit(url)
        identity = (
            source
            + ":"
            + urlunsplit(
                (
                    parsed.scheme.lower(),
                    parsed.netloc.lower(),
                    parsed.path,
                    parsed.query,
                    "",
                )
            )
        )
    # Preserve existing zero-start cache entries; other sections get distinct keys.
    if start_seconds:
        identity += f":start={start_seconds:.3f}"
    recipe = f"{RECIPE}:quality={mask_quality}"
    return "cache-" + hashlib.sha256((recipe + ":" + identity).encode()).hexdigest()


def cached_result(store, job):
    """Find a completed result with the same URL, start time, and recipe."""
    key = job.get("cacheKey") or cache_key(
        job["source"],
        job.get("url", ""),
        job.get("startSeconds", 0),
        job_mask_quality(job),
    )
    return store.get(key) if key else None


def completion(cached):
    """Copy completed result fields into a visitor's private job record."""
    return dict(
        state="completed",
        manifest=cached["manifest"],
        progress=cached["total"],
        total=cached["total"],
        cached=True,
        expiresAt=None,
    )

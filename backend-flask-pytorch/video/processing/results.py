"""Save playback assets and publish a completed result."""

import json

from ..cache import cache_key
from ..quality import job_mask_quality
from .media import create_poster


def result_prefix(job):
    """Keep each attempt's output separate, including cached URL results."""
    identity = job.get("cacheKey") or cache_key(
        job["source"],
        job.get("url", ""),
        job.get("startSeconds", 0),
        job_mask_quality(job),
    )
    return f"videos/{identity or job['id']}/{job['attempt']}"


def save_playback(assets, prepared, prefix, directory):
    """Store full-resolution playback and its first-frame poster."""
    video_key = f"{prefix}/video.mp4"
    poster_key = f"{prefix}/poster.jpg"
    assets.put_file(video_key, prepared.path, "video/mp4")
    poster = directory / "poster.jpg"
    create_poster(prepared.path, poster)
    assets.put_file(poster_key, poster, "image/jpeg")
    return {"videoKey": video_key, "posterKey": poster_key}


def publish_result(store, job, manifest, prefix, directory, update):
    """Expose a result only after every output file has been saved."""
    key = f"{prefix}/manifest.json"
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    store.assets.put_file(key, path, "application/json")
    total = len(manifest["frames"])
    update(
        state="completed", progress=total, manifest=key, expiresAt=None, cached=False
    )
    identity = job.get("cacheKey") or cache_key(
        job["source"],
        job.get("url", ""),
        job.get("startSeconds", 0),
        job_mask_quality(job),
    )
    if identity:
        store.save({"id": identity, "kind": "cache", "manifest": key, "total": total})

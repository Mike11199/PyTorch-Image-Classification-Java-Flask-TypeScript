"""Create, authorize, start, and cancel private video jobs."""

import hmac
import secrets
import time
import uuid

from ..cache import cache_key, completion
from ..config import EXAMPLES, TERMINAL
from ..sources.source import resolve_source, validate_source
from ..sources.start_time import clip_start
from ..types import VideoJob
from ..quality import DEFAULT_MASK_QUALITY, validate_mask_quality


def authorize_job(store, job_id, token) -> VideoJob:
    """Require a matching bearer token and an unexpired job."""
    job = store.get(job_id)
    if (
        not job
        or job.get("kind") != "job"
        or not hmac.compare_digest(job["token"], token)
    ):
        raise PermissionError("Video job not found.")
    if job.get("expiresAt") is not None and job["expiresAt"] <= time.time():
        raise PermissionError("This video job has expired.")
    return job


def new_job(source, url, start_seconds, identity) -> VideoJob:
    """Build initial fields for a new visitor's job."""
    now = int(time.time())
    example = next(
        (item for item in EXAMPLES if item["url"] == url and item["source"] == source),
        None,
    )
    return {
        "kind": "job",
        "id": uuid.uuid4().hex,
        "token": secrets.token_urlsafe(32),
        "state": "uploading" if source == "upload" else "queued",
        "source": source,
        "url": url,
        "startSeconds": start_seconds,
        "cacheKey": identity,
        "exampleId": example["id"] if example else None,
        "createdAt": now,
        "expiresAt": now + 86400,
        "progress": 0,
        "total": 0,
        "attempts": 0,
    }


def create_job(store, data) -> VideoJob:
    """Reuse a completed result or reserve a slot for new work."""
    source, url = resolve_source(data)
    start_seconds = clip_start(data, source, url)
    quality = validate_mask_quality(data.get("maskQuality", DEFAULT_MASK_QUALITY))
    identity = cache_key(source, url, start_seconds, quality)
    cached = store.get(identity) if identity else None
    validate_source(source, url, data, bool(cached))
    record = dict(new_job(source, url, start_seconds, identity), maskQuality=quality)
    if cached:
        return store.save(dict(record, **completion(cached)))
    return store.reserve(record)


def start_job(store, job):
    """Queue an upload after storage confirms the file is non-empty."""
    if job["state"] != "uploading":
        return job["state"], False
    try:
        size = store.assets.size(f"jobs/{job['id']}/input")
    except Exception as error:
        raise ValueError("The upload has not finished. Please retry.") from error
    if size <= 0:
        raise ValueError("Please upload a non-empty video file.")
    saved = store.save(dict(job, state="queued"), job["version"])
    if not saved:
        raise ValueError("Job changed while uploading. Please retry.")
    return "queued", True


def cancel_job(store, job_id, token):
    """Cancel unfinished work without overwriting concurrent state changes."""
    for _ in range(5):
        job = authorize_job(store, job_id, token)
        if job["state"] in TERMINAL:
            return job["state"]
        if store.save(dict(job, state="cancelled"), job["version"]):
            return "cancelled"
    return None

"""Translate stored jobs into progress and playback responses."""

import math
import time

from ..quality import job_mask_quality


def playback_result(store, job):
    """Replace stored object keys with authorized video and mask URLs."""
    if job["state"] != "completed":
        raise ValueError("The video is not ready yet.")
    assets = store.assets
    manifest = assets.read_json(job["manifest"])
    if manifest.get("maskFormat") != "ids-gzip":
        raise ValueError("This result uses an older mask format. Run the video again.")
    manifest["videoUrl"] = assets.url(job, manifest.pop("videoKey"))
    if "posterKey" in manifest:
        manifest["posterUrl"] = assets.url(job, manifest.pop("posterKey"))
    manifest["maskUrls"] = [assets.url(job, key) for key in manifest.pop("maskKeys")]
    return manifest


def estimated_seconds(job):
    """Estimate remaining analysis time after at least three completed frames."""
    started = job.get("analysisStartedAt")
    completed = job.get("progress", 0)
    if job.get("stage") != "analyzing" or not started or completed < 3:
        return None
    elapsed = max(0, time.time() - started)
    remaining = max(0, job.get("total", 0) - completed)
    return round(elapsed / completed * remaining)


def recovery_status(store, job):
    """Show a restart wait for abandoned attempts, respecting remote leases."""
    if job["state"] != "running":
        return {}
    if job.get("attempt") and job["attempt"] == store.active_attempt:
        return {}
    remaining = max(0, math.ceil(job.get("leaseUntil", 0) - time.time()))
    local_worker = store.worker_enabled and not store.bucket
    if not local_worker and remaining:
        return {}
    return {
        "state": "queued",
        "stage": None,
        "progress": 0,
        "total": 0,
        "interrupted": True,
        "restartWaitSeconds": remaining,
    }


def job_status(store, job):
    """Include the latest preview and an analysis-only ETA for running jobs."""
    fields = (
        "id",
        "source",
        "url",
        "startSeconds",
        "state",
        "stage",
        "progress",
        "total",
        "error",
        "expiresAt",
        "cached",
    )
    status = {field: job.get(field) for field in fields}
    status["maskQuality"] = job_mask_quality(job)
    status.update(recovery_status(store, job))
    status["etaSeconds"] = None
    if status["state"] != "running":
        return status
    status["etaSeconds"] = estimated_seconds(job)
    if job.get("previewKey"):
        status.update(
            previewUrl=store.assets.url(job, job["previewKey"]),
            previewFrame=job.get("previewFrame"),
            previewTime=job.get("previewTime"),
            previewWidth=job.get("previewWidth"),
            previewHeight=job.get("previewHeight"),
        )
        if job.get("previewMaskKey"):
            status["previewMaskUrl"] = store.assets.url(job, job["previewMaskKey"])
            status["previewDetections"] = job.get("previewDetections", [])
    return status

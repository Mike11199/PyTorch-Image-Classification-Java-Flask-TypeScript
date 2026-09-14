"""Sequential queue processing with leases, bounded retries, and cancellation."""

import logging
import time
import uuid

from .cache import cached_result, completion
from .processing.pipeline import process_video
from .config import TERMINAL

log = logging.getLogger(__name__)
LEASE_SECONDS = 300
MAX_ATTEMPTS = 2
MAX_PROCESSING_SECONDS = 7200


def job_is_ready(store, job, now):
    """Expire abandoned uploads and find queued or interrupted work."""
    if job["state"] == "uploading" and now - job["createdAt"] > 3600:
        store.save(
            dict(job, state="failed", error="Upload expired. Please submit again."),
            job["version"],
        )
        return False
    expired = job.get("expiresAt") is not None and job["expiresAt"] <= now
    if job["state"] in TERMINAL or expired:
        return False

    abandoned = job["state"] == "running" and job.get("leaseUntil", 0) < now
    return job["state"] == "queued" or abandoned


def claim_job(store, job, now):
    """Claim eligible work, reusing completed results before running inference."""
    if not job_is_ready(store, job, now):
        return None
    cached = cached_result(store, job)
    if cached:
        store.save(dict(job, **completion(cached)), job["version"])
        return None
    if job["attempts"] >= MAX_ATTEMPTS:
        store.save(
            dict(
                job,
                state="failed",
                error="Processing was interrupted twice. Please retry.",
            ),
            job["version"],
        )
        return None

    record = new_attempt(job, now)
    return store.save(record, job["version"])


def new_attempt(job, now):
    """Reset progress and previews so a retry cannot display an earlier attempt."""
    stale_fields = {"analysisStartedAt", "error"}
    record = {
        key: value
        for key, value in job.items()
        if key not in stale_fields and not key.startswith("preview")
    }
    return dict(
        record,
        state="running",
        stage="importing",
        progress=0,
        total=0,
        attempt=uuid.uuid4().hex,
        attempts=job["attempts"] + 1,
        leaseUntil=now + LEASE_SECONDS,
    )


def update_job(store, claimed, **changes):
    """Refresh the lease only while this attempt still owns the running job."""
    current = store.get(claimed["id"])
    if (
        not current
        or current["state"] != "running"
        or current.get("attempt") != claimed["attempt"]
    ):
        raise InterruptedError("Job was cancelled or reclaimed.")
    now = time.time()
    if (
        current["expiresAt"] <= now
        or now - claimed["createdAt"] > MAX_PROCESSING_SECONDS
    ):
        raise ValueError(
            "The processing time limit was reached. Please use a shorter clip."
        )
    saved = store.save(
        dict(current, **changes, leaseUntil=int(now) + LEASE_SECONDS),
        current["version"],
    )
    if not saved:
        raise InterruptedError("Job changed while processing.")
    if "stage" in changes:
        log.info("Video job %s: %s", claimed["id"], changes["stage"])


def process_claimed_job(store, claimed):
    """Handle processing errors without overwriting a cancellation or newer attempt."""

    def update(**changes):
        update_job(store, claimed, **changes)

    store.active_attempt = claimed["attempt"]
    try:
        process_video(store, claimed, update)
    except InterruptedError:
        pass
    except Exception as error:
        log.exception("Video job failed: %s", claimed["id"])
        fail_owned_job(store, claimed, error)
    finally:
        store.active_attempt = None


def fail_owned_job(store, claimed, error):
    """Record a failure only if this attempt still owns the job."""
    current = store.get(claimed["id"])
    if (
        not current
        or current["state"] != "running"
        or current.get("attempt") != claimed["attempt"]
    ):
        return
    message = (
        str(error)
        if isinstance(error, ValueError)
        else "Video processing failed. Try a smaller MP4 clip."
    )
    store.save(dict(current, state="failed", error=message), current["version"])


def run_worker(store):
    """Process one job at a time; image requests share the same model lock."""
    while True:
        try:
            store.cleanup()
            now = int(time.time())
            for job in store.jobs():
                claimed = claim_job(store, job, now)
                if claimed:
                    process_claimed_job(store, claimed)
        except Exception:
            log.exception("Video worker iteration failed")
        time.sleep(5)

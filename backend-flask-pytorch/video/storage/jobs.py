"""Queue admission and job records shared by local and AWS storage."""

import os
import time
from pathlib import Path

from ..config import TERMINAL
from .assets import VideoAssets
from .dynamodb_records import DynamoDbRecords
from .sqlite_records import SqliteRecords


class JobStore:
    """Reserve queue slots and protect updates with record versions."""

    def __init__(self):
        """Choose the persistence backend once at startup."""
        self.root = Path(os.getenv("VIDEO_DATA_DIR", "/tmp/mask-video"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.bucket = os.getenv("VIDEO_BUCKET")
        table_name = os.getenv("VIDEO_TABLE")
        if bool(self.bucket) != bool(table_name):
            raise RuntimeError(
                "VIDEO_BUCKET and VIDEO_TABLE must be configured together"
            )
        self.assets = VideoAssets(self.root, self.bucket)
        self.worker_enabled = os.getenv("VIDEO_WORKER_ENABLED", "true") == "true"
        self.active_attempt = None
        self.records = (
            DynamoDbRecords(table_name) if self.bucket else SqliteRecords(self.root)
        )

    def get(self, key):
        return self.records.get(key)

    def save(self, record, expected=None):
        """Advance a record's version only when its previous version matches."""
        record = dict(record, version=0 if expected is None else expected + 1)
        return self.records.save(record, expected)

    def jobs(self):
        jobs = [record for record in self.records.all() if record.get("kind") == "job"]
        return sorted(jobs, key=lambda job: job["createdAt"])

    def slot_available(self, slot, now):
        """Reuse expired slots or slots belonging to finished jobs."""
        if not slot or slot["expiresAt"] <= now:
            return True
        owner = self.get(slot["owner"])
        return bool(owner and owner["state"] in TERMINAL)

    def reserve(self, job):
        """Atomically claim one of the bounded queue's admission slots."""
        now = int(time.time())
        for index in range(int(os.getenv("VIDEO_QUEUE_SIZE", "3"))):
            key = f"slot-{index}"
            old = self.get(key)
            if not self.slot_available(old, now):
                continue
            slot = {"id": key, "owner": job["id"], "expiresAt": job["expiresAt"]}
            if self.save(slot, old["version"] if old else None):
                return self.save(job)
        raise ValueError("The video queue is full. Please try again later.")

    def cleanup(self):
        """Remove expired local inputs; AWS uses S3 lifecycle and DynamoDB TTL."""
        if self.bucket:
            return
        now = int(time.time())
        for job in self.jobs():
            if job.get("expiresAt") is not None and job["expiresAt"] <= now:
                self.assets.remove_temporary(job["id"])
                self.records.delete(job["id"])

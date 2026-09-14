"""Shared job records and prepared video data."""

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict


class VideoJob(TypedDict, total=False):
    """Persisted job fields; processing adds progress and output locations."""

    kind: str
    id: str
    token: str
    state: str
    source: str
    url: str
    startSeconds: float
    maskQuality: str
    cacheKey: str | None
    exampleId: str | None
    createdAt: int
    expiresAt: int | None
    version: int
    attempts: int
    attempt: str
    leaseUntil: int
    stage: str
    progress: int
    total: int
    analysisStartedAt: float
    previewKey: str
    previewMaskKey: str
    previewDetections: list[dict]
    previewWidth: int
    previewHeight: int
    previewFrame: int
    previewTime: float
    manifest: str
    cached: bool
    error: str


@dataclass
class PreparedVideo:
    """Full-resolution playback and a smaller, synchronized model input."""

    path: Path
    model_path: Path
    timestamps: list[float]
    width: int
    height: int

"""Publish full-resolution frames with separate adjustable mask layers."""

import time

import numpy as np
from PIL import Image

from ..config import PREVIEW_INTERVAL_SECONDS
from .media import command


def save_preview(assets, prepared, overlay, timestamp, key, directory):
    """Store an original-sized JPEG and a separate small transparent mask."""
    mask_path = directory / "preview-mask.png"
    preview_path = directory / "preview.jpg"
    overlay.save(mask_path)
    command(
        ["ffmpeg", "-v", "error", "-nostdin", "-threads", "1", "-ss", str(timestamp)]
        + ["-i", str(prepared.path)]
        + ["-frames:v", "1", "-threads", "1", "-q:v", "2", "-y", str(preview_path)],
        timeout=60,
    )
    assets.put_file(key, preview_path, "image/jpeg")
    mask_key = key.removesuffix(".jpg") + ".png"
    assets.put_file(mask_key, mask_path, "image/png")
    return mask_key


class PreviewPublisher:
    """Publish first, recent, and final frames at playback resolution."""

    def __init__(self, assets, prepared, prefix, directory, update):
        """Keep original playback available while inference uses its smaller copy."""
        self.assets = assets
        self.prepared = prepared
        self.prefix = prefix
        self.directory = directory
        self.update = update
        self.last_published = None

    def publish(self, mask_ids, detections, index, timestamp, last_frame):
        """Update the preview when its interval passes or the clip ends."""
        now = time.monotonic()
        due = (
            self.last_published is None
            or now - self.last_published >= PREVIEW_INTERVAL_SECONDS
        )
        if not (due or last_frame):
            return
        key = f"{self.prefix}/{index:04d}.jpg"
        palette = np.array([[0, 0, 0, 0]] + [
            detection["color"] + [255] for detection in detections
        ], dtype=np.uint8)
        with Image.fromarray(palette[mask_ids]) as overlay:
            mask_key = save_preview(
                self.assets, self.prepared, overlay, timestamp, key, self.directory
            )
        self.update(
            progress=index + 1,
            previewKey=key,
            previewMaskKey=mask_key,
            previewDetections=detections,
            previewWidth=self.prepared.width,
            previewHeight=self.prepared.height,
            previewFrame=index + 1,
            previewTime=timestamp,
        )
        self.last_published = time.monotonic()

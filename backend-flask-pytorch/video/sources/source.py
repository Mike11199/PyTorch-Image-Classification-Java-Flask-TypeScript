"""Resolve submitted sources and copy them into a working directory."""

import os
import shutil
from pathlib import Path

from ..config import EXAMPLES
from .urls import download_url, validate_url
from .youtube import download_youtube, validate_youtube


def resolve_source(data):
    """Replace a selected example ID with its source and URL."""
    source = data.get("source", "upload")
    if source not in {"upload", "url", "youtube", "example"}:
        raise ValueError("Choose an upload, example, or supported video URL.")
    if source != "example":
        return source, str(data.get("url", ""))
    for example in EXAMPLES:
        if example["id"] == data.get("exampleId"):
            return example["source"], example["url"]
    raise ValueError("Unknown example.")


def validate_source(source, url, data, cached):
    """Validate new inputs while allowing completed URLs to use the cache."""
    if source == "url":
        validate_url(url, resolve=not cached)
    if source == "youtube" and not cached:
        validate_youtube(url)
    if source == "upload":
        size = data.get("size", 0)
        if not isinstance(size, (int, float)) or size <= 0:
            raise ValueError("Please select a non-empty video file.")


def copy_example(store, path):
    """Keep older queued site-demo jobs readable after removing the preset."""
    if store.bucket:
        store.assets.s3.download_file(
            os.environ["VIDEO_MEDIA_BUCKET"], "videos/ml-video.mp4", str(path)
        )
        return
    bundled = Path(os.getenv("VIDEO_EXAMPLE_PATH", "/app/examples/ml-video.mp4"))
    if not bundled.exists():
        bundled = (
            Path(__file__).resolve().parents[3] / "frontend/src/assets/ml_video.mp4"
        )
    shutil.copyfile(bundled, path)


def obtain_input(store, job, path):
    """Import the selected source without buffering the full video in memory."""
    if job["source"] == "example":
        copy_example(store, path)
    elif job["source"] == "upload":
        store.assets.download(f"jobs/{job['id']}/input", path)
    elif job["source"] == "youtube":
        download_youtube(job["url"], path, job.get("startSeconds", 0))
    else:
        download_url(job["url"], path)
    if not path.is_file() or not path.stat().st_size:
        raise ValueError("The video download did not produce a file. Please retry.")

"""Coordinate video import, preparation, analysis, and publication."""

import tempfile
import time
from pathlib import Path

from ..cache import cached_result, completion, upload_cache_key
from ..sources.source import obtain_input
from ..types import PreparedVideo, VideoJob
from ..quality import job_mask_quality, model_frame_edge
from .media import (
    frame_timestamps,
    prepare_playback,
    prepare_model_video,
    prepare_example,
    probe,
    validate_probe,
)
from .results import publish_result, result_prefix, save_playback


def prepare_video(source: Path, directory: Path, job: VideoJob, update) -> PreparedVideo:
    """Prepare playback and model copies without seeking a YouTube excerpt twice."""
    if job["source"] == "example":
        source = prepare_example(source, directory)
    info = probe(source)
    stream = validate_probe(info)
    seek_seconds = 0 if job["source"] == "youtube" else job.get("startSeconds", 0)
    duration = float(info.get("format", {}).get("duration", stream.get("duration", 0)))
    if seek_seconds >= duration:
        raise ValueError("The start time is past the end of this video.")
    update(stage="encoding")
    playback = directory / "video.mp4"
    prepare_playback(source, playback, seek_seconds)
    update(stage="resizing")
    model_path = directory / "model.mp4"
    prepare_model_video(playback, model_path, model_frame_edge(job))
    update(stage="indexing")
    playback_stream = validate_probe(probe(playback))
    return PreparedVideo(
        playback,
        model_path,
        frame_timestamps(model_path),
        int(playback_stream["width"]),
        int(playback_stream["height"]),
    )


def process_video(store, job: VideoJob, update):
    """Run each stage with one temporary directory and one active model user."""
    with tempfile.TemporaryDirectory(prefix="work-", dir=store.root) as work:
        directory = Path(work)
        source = directory / "input"
        update(stage="importing")
        obtain_input(store, job, source)

        if job["source"] == "upload":
            identity = upload_cache_key(
                source, job.get("startSeconds", 0), job_mask_quality(job)
            )
            job = dict(job, cacheKey=identity)
            update(cacheKey=identity)
            cached = cached_result(store, job)
            if cached:
                update(**completion(cached))
                return

        from .frames import analyze_video

        update(stage="preparing", progress=0)
        prepared = prepare_video(source, directory, job, update)
        prefix = result_prefix(job)
        update(stage="saving_playback")
        playback = save_playback(store.assets, prepared, prefix, directory)

        update(
            total=len(prepared.timestamps),
            stage="analyzing",
            analysisStartedAt=time.time(),
        )
        previews = f"jobs/{job['id']}/{job['attempt']}/previews"
        manifest = analyze_video(
            store.assets, prepared, prefix, directory, update, previews
        )
        manifest.update(playback)
        manifest["maskQuality"] = job_mask_quality(job)
        update(stage="saving_result")
        publish_result(store, job, manifest, prefix, directory, update)

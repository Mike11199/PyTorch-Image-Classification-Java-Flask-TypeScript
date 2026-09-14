"""Analyze frames sequentially and collect playback metadata."""

import time
from contextlib import closing

import cv2

from ..config import ATLAS_COLUMNS, CHUNK_FRAMES
from .inference import analyze_frame
from .mask_atlas import MaskAtlas
from .previews import PreviewPublisher


def read_frames(playback, timestamps):
    """Yield decoded frames with their presentation timestamps."""
    capture = cv2.VideoCapture(str(playback))
    try:
        for index, timestamp in enumerate(timestamps):
            ok, frame = capture.read()
            if not ok:
                raise ValueError(
                    "Video decoding ended before all frames were analyzed."
                )
            yield index, timestamp, frame
    finally:
        capture.release()


def analyze_video(assets, prepared, prefix, directory, update, preview_prefix):
    """Process one frame at a time, publishing masks and progress as it finishes."""
    atlas = MaskAtlas(assets, prefix, directory)
    previews = PreviewPublisher(assets, prepared, preview_prefix, directory, update)
    frames = []
    try:
        with closing(read_frames(prepared.model_path, prepared.timestamps)) as decoded:
            for index, timestamp, frame in decoded:
                update(progress=index)
                overlay, detections = analyze_frame(frame)
                last_frame = index == len(prepared.timestamps) - 1
                with overlay:
                    atlas.add(overlay, index, last_frame)
                    previews.publish(overlay, detections, index, timestamp, last_frame)
                frames.append({"time": timestamp, "detections": detections})
                time.sleep(0.02)
    finally:
        atlas.close()
    return {
        "version": 1,
        "width": atlas.width,
        "height": atlas.height,
        "videoWidth": prepared.width,
        "videoHeight": prepared.height,
        "chunkFrames": CHUNK_FRAMES,
        "columns": ATLAS_COLUMNS,
        "frames": frames,
        "maskKeys": atlas.keys,
    }

"""Analyze frames sequentially and collect playback metadata."""

import time
from contextlib import closing

import cv2

from ..config import CHUNK_FRAMES
from .inference import analyze_frame
from .mask_ids import MaskIds
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
    masks = MaskIds(assets, prefix, directory, CHUNK_FRAMES)
    previews = PreviewPublisher(assets, prepared, preview_prefix, directory, update)
    frames = []
    with closing(read_frames(prepared.model_path, prepared.timestamps)) as decoded:
        for index, timestamp, frame in decoded:
            update(progress=index)
            mask_ids, detections = analyze_frame(frame)
            last_frame = index == len(prepared.timestamps) - 1
            masks.add(mask_ids, index, last_frame)
            previews.publish(mask_ids, detections, index, timestamp, last_frame)
            frames.append({"time": timestamp, "detections": detections})
            time.sleep(0.02)
    return {
        "version": 2,
        "maskFormat": "ids-gzip",
        "width": masks.width,
        "height": masks.height,
        "videoWidth": prepared.width,
        "videoHeight": prepared.height,
        "chunkFrames": CHUNK_FRAMES,
        "frames": frames,
        "maskKeys": masks.keys,
    }

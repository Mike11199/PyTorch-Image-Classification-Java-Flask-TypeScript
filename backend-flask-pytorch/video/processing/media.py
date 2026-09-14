"""Prepare full-resolution playback and a small copy for PyTorch."""

import json
import logging
import subprocess

from ..config import MAX_SECONDS, MAX_FRAME_EDGE

log = logging.getLogger(__name__)


def command(args, timeout=120):
    """Run a media tool with a deadline and translate decoder failures."""
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        log.warning(
            "Video tool failed: %s", result.stderr[-1000:].decode(errors="replace")
        )
        raise ValueError("Unable to decode this video. Try an MP4/H.264 file.")
    return result.stdout


def probe(path):
    """Read stream dimensions, duration, and codec metadata."""
    return json.loads(
        command(
            [
                "ffprobe",
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ],
            30,
        )
    )


def validate_probe(info):
    """Require a video stream with a usable duration and dimensions."""
    stream = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "video"), None
    )
    if not stream:
        raise ValueError("The file has no video stream.")
    duration = float(info.get("format", {}).get("duration", stream.get("duration", 0)))
    if duration <= 0:
        raise ValueError("The video has no available duration.")
    if int(stream.get("width", 0)) <= 0 or int(stream.get("height", 0)) <= 0:
        raise ValueError("The video has no available frame dimensions.")
    return stream


def prepare_example(source, directory):
    """Preserve the five-second excerpt used by previously queued site-demo jobs."""
    excerpt = directory / "example.mp4"
    command(
        ["ffmpeg", "-v", "error", "-nostdin", "-threads", "1", "-i", str(source)]
        + ["-t", "5", "-vf", "scale=640:-2", "-fps_mode", "passthrough"]
        + ["-c:v", "libx264", "-threads", "1", "-preset", "veryfast", "-c:a", "aac"]
        + ["-y", str(excerpt)]
    )
    return excerpt


def prepare_playback(source, playback, start_seconds=0):
    """Trim to ten seconds at source resolution with browser-compatible H.264."""
    command(
        ["ffmpeg", "-v", "error", "-nostdin", "-threads", "1", "-filter_threads", "1"]
        + [
            "-protocol_whitelist",
            "file,pipe",
            "-ss",
            str(start_seconds),
            "-i",
            str(source),
        ]
        + [
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-vf",
            "pad=ceil(iw/2)*2:ceil(ih/2)*2,setsar=1",
        ]
        + ["-fps_mode", "passthrough", "-t", str(MAX_SECONDS)]
        + ["-c:v", "libx264", "-threads", "1", "-preset", "veryfast", "-crf", "18"]
        + ["-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart"]
        + ["-y", str(playback)]
    )


def prepare_model_video(playback, model_path, max_edge=MAX_FRAME_EDGE):
    """Downsample only the inference copy, preserving each frame's timestamp."""
    scale = (
        f"scale=w='min({max_edge},iw)':h='min({max_edge},ih)':"
        "force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1"
    )
    command(
        ["ffmpeg", "-v", "error", "-nostdin", "-threads", "1", "-filter_threads", "1"]
        + ["-protocol_whitelist", "file,pipe", "-i", str(playback)]
        + ["-map", "0:v:0", "-an", "-vf", scale, "-fps_mode", "passthrough"]
        + ["-c:v", "libx264", "-threads", "1", "-preset", "veryfast", "-crf", "18"]
        + ["-pix_fmt", "yuv420p", "-y", str(model_path)]
    )
    stream = validate_probe(probe(model_path))
    if max(int(stream["width"]), int(stream["height"])) > max_edge:
        raise ValueError("The model input could not be resized safely.")


def frame_timestamps(playback):
    """Read presentation times from the normalized video, including variable FPS."""
    metadata = json.loads(
        command(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames"]
            + [
                "-show_entries",
                "frame=best_effort_timestamp_time",
                "-of",
                "json",
                str(playback),
            ]
        )
    )
    times = [float(frame["best_effort_timestamp_time"]) for frame in metadata["frames"]]
    if not times:
        raise ValueError("The video has no decodable frames.")
    return times


def create_poster(playback, poster):
    """Save the first frame for the player's initial preview."""
    command(
        ["ffmpeg", "-v", "error", "-nostdin", "-threads", "1", "-i", str(playback)]
        + ["-frames:v", "1", "-q:v", "2", "-threads", "1", "-y", str(poster)]
    )

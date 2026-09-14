"""Read YouTube metadata and download only the requested clip."""

import json
import subprocess
import sys
from urllib.parse import urlparse

from ..config import MAX_SECONDS, youtube_enabled
from ..processing.media import command

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def validate_youtube_url(url):
    """Require a supported HTTPS YouTube host."""
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in YOUTUBE_HOSTS
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("Enter a valid HTTPS YouTube link.")
    return parsed


def validate_youtube(url):
    """Check importer availability before fetching a new source."""
    if not youtube_enabled():
        raise ValueError(
            "YouTube import is not enabled on this server. Please upload the video file."
        )
    validate_youtube_url(url)


def downloader_command(arguments, url, timeout):
    """Run yt-dlp with bounded retries and public-video settings."""
    base = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ignore-config",
        "--no-plugin-dirs",
        "--no-playlist",
        "--js-runtimes",
        "node",
        "--socket-timeout",
        "15",
        "--retries",
        "2",
    ]
    return command(base + arguments + ["--", url], timeout)


def clip_end(metadata, start_seconds):
    """Validate recorded-video metadata and bound the requested end time."""
    if metadata.get("is_live") or metadata.get("live_status") in {
        "is_live",
        "is_upcoming",
    }:
        raise ValueError(
            "Please use a recorded YouTube video rather than a live stream."
        )
    duration = float(metadata.get("duration") or 0)
    if duration <= 0:
        raise ValueError("This YouTube video has no available duration.")
    if start_seconds >= duration:
        raise ValueError("The start time is past the end of this video.")
    return min(start_seconds + MAX_SECONDS, duration)


def download_section(url, output, start_seconds, end_seconds):
    """Fetch the selected section at the highest available source resolution."""
    arguments = [
        "--download-sections",
        f"*{start_seconds:g}-{end_seconds:g}",
        "--format",
        "bv*+ba/b",
        "--format-sort",
        "res",
        "--merge-output-format",
        "mp4",
        "--no-progress",
        "--downloader-args",
        "ffmpeg_o:-threads 1",
        "--output",
        str(output),
    ]
    downloader_command(arguments, url, 180)
    if not output.is_file():
        raise ValueError(
            "YouTube import finished without producing a video file. Please retry."
        )


def download_youtube(url, path, start_seconds=0):
    """Import a ten-second clip and translate downloader failures."""
    validate_youtube(url)
    output = path.with_suffix(".mp4")
    try:
        metadata = json.loads(
            downloader_command(["--dump-single-json", "--skip-download"], url, 60)
        )
        end_seconds = clip_end(metadata, start_seconds)
        download_section(url, output, start_seconds, end_seconds)
        if output != path:
            output.replace(path)
    except (subprocess.TimeoutExpired, FileNotFoundError) as error:
        raise ValueError(
            "YouTube import timed out or its downloader is unavailable. Please try again or upload a video."
        ) from error
    except ValueError as error:
        if str(error).startswith("Unable to decode"):
            raise ValueError(
                "YouTube could not provide this video. Please try another public link or upload the file."
            ) from error
        raise

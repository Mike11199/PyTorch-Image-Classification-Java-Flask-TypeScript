"""Read YouTube metadata and download only the requested clip."""

import json
import logging
import os
import signal
import shlex
import subprocess
import sys
import tempfile
import time
from contextlib import nullcontext
from pathlib import Path
from urllib.parse import urlparse

import certifi

from ..config import MAX_SECONDS, youtube_enabled

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
log = logging.getLogger(__name__)


class DownloadFailure(ValueError):
    def __init__(self, reason, retryable=True):
        super().__init__(reason)
        self.retryable = retryable


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


def downloader_command(arguments, url, timeout, proxy="", progress=lambda: None):
    """Run yt-dlp with bounded retries and public-video settings."""
    base = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ignore-config",
        "--no-playlist",
        "--extractor-args",
        "youtube:player_client=mweb",
        "--js-runtimes",
        "node",
        "--socket-timeout",
        "25" if proxy else "15",
        "--retries",
        "0" if proxy else "2",
    ]
    if proxy:
        base += ["--proxy", proxy]
    # Stop ffmpeg as well as yt-dlp if the job is cancelled or times out.
    with subprocess.Popen(
        base + arguments + ["--", url], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True,
    ) as process:
        deadline = time.monotonic() + timeout
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise DownloadFailure("download timed out")
                try:
                    stdout, stderr = process.communicate(timeout=min(10, remaining))
                    break
                except subprocess.TimeoutExpired:
                    progress()
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise
    if process.returncode:
        detail = stderr.decode(errors="replace").lower()
        permanent = any(message in detail for message in (
            "private video", "video unavailable", "video has been removed",
            "members-only", "confirm your age",
        ))
        raise DownloadFailure("video unavailable" if permanent else "YouTube rejected the download", not permanent)
    return stdout


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


def download_section(url, output, start_seconds, end_seconds, timeout=180, proxy="", progress=lambda: None):
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
        f"ffmpeg_i:-tls_verify 1 -ca_file {shlex.quote(certifi.where())}",
        "--downloader-args",
        "ffmpeg_o:-threads 1",
        "--output",
        str(output),
    ]
    downloader_command(arguments, url, timeout, proxy, progress)
    if not output.is_file():
        raise ValueError(
            "YouTube import finished without producing a video file. Please retry."
        )


def download_youtube(url, path, start_seconds=0, on_progress=lambda: None):
    """Import a ten-second clip and translate downloader failures."""
    validate_youtube(url)
    use_tor = os.getenv("VIDEO_YOUTUBE_TOR", "false") == "true"
    deadline = time.monotonic() + 300

    def progress():
        on_progress()
        if time.monotonic() >= deadline:
            raise ValueError("YouTube import timed out. Please try again or upload the file.")

    if use_tor:
        from .tor import change_exit, tor_connection
    connection = tor_connection(progress) if use_tor else nullcontext(None)
    proxy = f"http://{os.getenv('VIDEO_TOR_HOST', '127.0.0.1')}:9080" if use_tor else ""
    attempts = 3 if use_tor else 1
    try:
        with connection as controller:
            for attempt in range(attempts):
                progress()
                if attempt:
                    change_exit(controller, progress)
                try:
                    # Each attempt starts fresh; never reuse a partial file from another exit.
                    with tempfile.TemporaryDirectory(dir=path.parent) as directory:
                        output = Path(directory) / "clip.mp4"
                        try:
                            metadata = json.loads(downloader_command(
                                ["--dump-single-json", "--skip-download"], url,
                                min(60, deadline - time.monotonic()), proxy, progress,
                            ))
                        except json.JSONDecodeError as error:
                            raise DownloadFailure(
                                "YouTube returned invalid video metadata"
                            ) from error
                        end_seconds = clip_end(metadata, start_seconds)
                        download_section(
                            url, output, start_seconds, end_seconds,
                            min(180, deadline - time.monotonic()), proxy, progress,
                        )
                        output.replace(path)
                        return
                except DownloadFailure as error:
                    log.warning("YouTube import attempt %s/%s: %s", attempt + 1, attempts, error)
                    if not error.retryable or attempt == attempts - 1:
                        raise ValueError(
                            "YouTube could not provide this video. Please try another public link or upload the file."
                        ) from error
    except InterruptedError:
        raise
    except OSError as error:
        raise ValueError(
            "The YouTube connection is unavailable. Please try again or upload the file."
        ) from error

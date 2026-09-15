"""Read YouTube metadata and download only the requested clip."""

import json
import logging
import os
import re
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
log.setLevel(logging.INFO)


class DownloadFailure(ValueError):
    def __init__(self, reason, retryable=True):
        super().__init__(reason)
        self.retryable = retryable


def download_diagnostic(detail):
    """Allow only fixed failure labels and HTTP codes into server logs."""
    reasons = [label for label, markers in (
        ("bot verification required", ("not a bot", "confirm you're not", "confirm you’re not")),
        ("rate limited", ("too many requests", "rate limit")),
        ("connection timed out", ("timed out", "timeout")),
        ("connection failed", ("connection refused", "connection reset", "network is unreachable", "unable to connect")),
        ("DNS lookup failed", ("name resolution", "name or service not known")),
        ("TLS verification failed", ("certificate verify failed", "certificate verification failed")),
        ("private or unavailable video", ("private video", "video unavailable", "video has been removed")),
        ("restricted video", ("members-only", "confirm your age")),
        ("requested format unavailable", ("requested format is not available",)),
    ) if any(marker in detail for marker in markers)]
    codes = sorted(set(re.findall(r"\bhttp(?: error| error code| status(?: code)?)?[:\s]+([45]\d{2})\b", detail)))
    reasons.extend(f"HTTP {code}" for code in codes)
    return "; ".join(reasons) or "unclassified downloader failure"


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
        "--format-sort",
        "res",
        "--format-sort-force",
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
        log.warning("yt-dlp exited with code %s: %s", process.returncode,
                    download_diagnostic(detail))
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


def selected_video(metadata):
    """Require a concrete YouTube format and dimensions before downloading."""
    format_id = metadata.get("format_id", "")
    if not isinstance(format_id, str) or not re.fullmatch(r"[0-9]+(?:-[0-9]+)?(?:\+[0-9]+(?:-[0-9]+)?)*", format_id):
        raise DownloadFailure("YouTube returned an unsupported format selection")
    try:
        width, height = int(metadata.get("width") or 0), int(metadata.get("height") or 0)
    except (TypeError, ValueError, OverflowError) as error:
        raise DownloadFailure("YouTube returned invalid video dimensions") from error
    if width <= 0 or height <= 0:
        raise DownloadFailure("YouTube returned no video dimensions")
    log.info("YouTube selected format %s at %dx%d", format_id, width, height)
    return format_id, width, height


def verify_download(output, width, height, timeout):
    """Check actual media dimensions before accepting it as the source video."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(output)],
            capture_output=True, timeout=timeout,
        )
        if result.returncode:
            raise DownloadFailure("Unable to verify downloaded video resolution")
        stream = json.loads(result.stdout)["streams"][0]
        actual_width, actual_height = int(stream["width"]), int(stream["height"])
    except (subprocess.TimeoutExpired, ValueError, KeyError, IndexError, TypeError, OverflowError) as error:
        raise DownloadFailure("Unable to verify downloaded video resolution") from error
    log.info("YouTube downloaded %dx%d; requested %dx%d", actual_width, actual_height, width, height)
    if actual_width < width or actual_height < height:
        raise DownloadFailure("Downloaded video resolution was lower than requested")


def download_section(url, output, start_seconds, end_seconds, format_id, timeout=180, proxy="", progress=lambda: None):
    """Fetch the exact formats selected during metadata lookup, without fallback."""
    arguments = [
        "--download-sections",
        f"*{start_seconds:g}-{end_seconds:g}",
        "--format",
        format_id,
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
        raise DownloadFailure(
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

    retry_errors = (DownloadFailure,)
    if use_tor:
        from .tor import TorConnectionFailure, change_exit, tor_connection
        retry_errors += (TorConnectionFailure,)
    proxy = f"http://{os.getenv('VIDEO_TOR_HOST', '127.0.0.1')}:9080" if use_tor else ""
    attempts = 5 if use_tor else 1
    best_width = best_height = 0
    try:
        for attempt in range(attempts):
            progress()
            try:
                # Reconnect on every attempt so a dropped controller cannot poison retries.
                connection = tor_connection(progress) if use_tor else nullcontext(None)
                with connection as controller:
                    if attempt:
                        change_exit(controller, progress)
                    progress()
                    # Each attempt starts fresh; never reuse a partial file from another exit.
                    with tempfile.TemporaryDirectory(dir=path.parent) as directory:
                        output = Path(directory) / "clip.mp4"
                        try:
                            metadata = json.loads(downloader_command(
                                ["--dump-single-json", "--skip-download", "--format", "bv*+ba/b"], url,
                                min(60, deadline - time.monotonic()), proxy, progress,
                            ))
                        except json.JSONDecodeError as error:
                            raise DownloadFailure(
                                "YouTube returned invalid video metadata"
                            ) from error
                        end_seconds = clip_end(metadata, start_seconds)
                        format_id, width, height = selected_video(metadata)
                        if width < best_width or height < best_height:
                            raise DownloadFailure("YouTube temporarily offered a lower video resolution")
                        best_width, best_height = width, height
                        progress()
                        download_section(
                            url, output, start_seconds, end_seconds, format_id,
                            min(180, deadline - time.monotonic()), proxy, progress,
                        )
                        progress()
                        verify_download(output, width, height, min(30, deadline - time.monotonic()))
                        progress()
                        output.replace(path)
                        return
            except retry_errors as error:
                log.warning("YouTube import attempt %s/%s: %s", attempt + 1, attempts, error)
                progress()
                if (isinstance(error, DownloadFailure) and not error.retryable) or attempt == attempts - 1:
                    raise ValueError(
                        "YouTube could not provide this video. Please try another public link or upload the file."
                    ) from error
    except InterruptedError:
        raise
    except OSError as error:
        raise ValueError(
            "The YouTube connection is unavailable. Please try again or upload the file."
        ) from error

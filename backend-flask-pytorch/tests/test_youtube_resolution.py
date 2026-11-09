"""Exercise importer format policy with yt-dlp's real format selector."""

import tempfile
import json
from contextlib import nullcontext
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yt_dlp

from video.sources.youtube import download_section, download_youtube


class YouTubeResolutionTests(unittest.TestCase):
    def run_import(self, metadata, dimensions, url="https://youtu.be/abcdefghijk"):
        """Stub only network/media boundaries; run the real import retry loop."""
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "accepted.mp4"
            attempts = []

            def download(url, output, *args, **kwargs):
                attempts.append(output)
                output.write_bytes(b"downloaded video")

            with patch.dict("os.environ", {"VIDEO_YOUTUBE_TOR": "true"}), \
                 patch("video.sources.tor.tor_connection", side_effect=lambda _: nullcontext(object())), \
                 patch("video.sources.tor.change_exit") as rotate, \
                 patch("video.sources.youtube.downloader_command", side_effect=[json.dumps(m).encode() for m in metadata]), \
                 patch("video.sources.youtube.download_section", side_effect=download), \
                 patch("video.processing.media.probe", side_effect=[{"streams": [{"codec_type": "video", "width": w, "height": h}], "format": {"duration": "10"}} for w, h in dimensions]):
                error = None
                try:
                    download_youtube(url, destination)
                except ValueError as caught:
                    error = caught
                return destination.exists(), rotate.call_count, len(attempts), error

    def test_known_4k_video_retries_exit_that_only_advertises_360p(self):
        low = {"duration": 60000, "width": 640, "height": 360}
        high = {"duration": 60000, "width": 3840, "height": 2160}
        accepted, rotations, downloads, error = self.run_import(
            [low, high], [(3840, 2160)], "https://www.youtube.com/watch?v=_rpdUcbkG7A")
        self.assertIsNone(error)
        self.assertTrue(accepted)
        self.assertEqual((rotations, downloads), (1, 1))

    def test_download_downgrade_retries_and_remembers_highest_resolution(self):
        high = {"duration": 100, "width": 3840, "height": 2160}
        low = {"duration": 100, "width": 640, "height": 360}
        accepted, rotations, downloads, error = self.run_import(
            [high, low, high], [(640, 360), (3840, 2160)])
        self.assertIsNone(error)
        self.assertTrue(accepted)
        self.assertEqual((rotations, downloads), (2, 2))

    def test_exhausted_low_resolution_attempts_never_publish_source(self):
        low = {"duration": 60000, "width": 640, "height": 360}
        accepted, rotations, downloads, error = self.run_import(
            [low] * 5, [], "https://youtu.be/_rpdUcbkG7A?t=52610")
        self.assertFalse(accepted)
        self.assertIsInstance(error, ValueError)
        self.assertEqual((rotations, downloads), (4, 0))

    def test_genuinely_low_resolution_video_is_accepted(self):
        accepted, rotations, downloads, error = self.run_import(
            [{"duration": 100, "width": 640, "height": 360}], [(640, 360)])
        self.assertIsNone(error)
        self.assertTrue(accepted)
        self.assertEqual((rotations, downloads), (0, 1))

    def test_repeated_download_downgrades_never_publish_source(self):
        high = {"duration": 100, "width": 3840, "height": 2160}
        accepted, rotations, downloads, error = self.run_import(
            [high] * 5, [(640, 360)] * 5)
        self.assertFalse(accepted)
        self.assertIsInstance(error, ValueError)
        self.assertEqual((rotations, downloads), (4, 5))

    def test_highest_advertised_format_sets_minimum_even_if_selected_metadata_is_low(self):
        metadata = {"duration": 100, "width": 640, "height": 360,
                    "formats": [{"width": 3840, "height": 2160, "vcodec": "vp9"}]}
        accepted, rotations, downloads, error = self.run_import(
            [metadata] * 2, [(640, 360), (3840, 2160)])
        self.assertTrue(accepted)
        self.assertIsNone(error)
        self.assertEqual((rotations, downloads), (1, 2))

    def test_resolution_beats_extractor_preference(self):
        process = MagicMock()
        process.__enter__.return_value = process
        process.communicate.return_value = (b"", b"")
        process.returncode = 0
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "clip.mp4"
            output.touch()
            with patch("video.sources.youtube.subprocess.Popen", return_value=process) as launch:
                download_section("https://youtu.be/_rpdUcbkG7A", output, 52608, 52618)
            options = yt_dlp.parse_options(launch.call_args.args[0][3:]).ydl_opts
        options.update(quiet=True, simulate=True)
        with yt_dlp.YoutubeDL(options) as downloader:
            selected = downloader.process_ie_result({
                "id": "fixture", "title": "Resolution regression",
                "formats": [
                    {"format_id": "18", "url": "https://example.com/360.mp4",
                     "width": 640, "height": 360, "vcodec": "avc1", "acodec": "aac",
                     "ext": "mp4", "preference": 0},
                    {"format_id": "313", "url": "https://example.com/2160.webm",
                     "width": 3840, "height": 2160, "vcodec": "vp9", "acodec": "none",
                     "ext": "webm", "preference": -10},
                    {"format_id": "140", "url": "https://example.com/audio.m4a",
                     "vcodec": "none", "acodec": "aac", "ext": "m4a"},
                ],
            }, download=False)
        self.assertEqual((selected["width"], selected["height"]), (3840, 2160))


"""Public entry points and bundled media still work after moving backend modules."""

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from images.routes import blueprint
from video.sources.source import copy_example


class BackendLayoutTests(unittest.TestCase):
    def test_image_endpoints_keep_their_urls(self):
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(blueprint)
        client = app.test_client()
        for url in ('/api-pytorch/image-url-pytorch', '/api-pytorch/image-url-pytorch-mask'):
            with self.subTest(url=url):
                response = client.post(url)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json, {'error': 'No file part'})

    def test_legacy_example_falls_back_to_frontend_asset(self):
        store = Mock(bucket=None)
        source = Path(__file__).resolve().parents[2] / 'frontend/src/assets/ml_video.mp4'
        destination = Path('unused-test-destination.mp4')
        with patch.dict('os.environ', {'VIDEO_EXAMPLE_PATH': 'missing-test-example.mp4'}), \
             patch('video.sources.source.shutil.copyfile') as copy:
            copy_example(store, destination)
        copy.assert_called_once_with(source, destination)

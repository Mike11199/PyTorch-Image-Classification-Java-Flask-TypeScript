"""Exercise snapshot persistence, invalidation, and best-effort recovery."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langgraph_vision_assistant.model.prompt_cache import PromptCache
from langgraph_vision_assistant.model.settings import ModelSettings


class DiskSlot:
    def __init__(self, directory):
        self.directory = directory
        self.state = b'processed prefix'

    def slot(self, action, filename):
        path = self.directory / filename
        if action == 'save':
            path.write_bytes(self.state)
        else:
            self.state = path.read_bytes()
        return {}


class PromptCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.model, self.server = root / 'model.gguf', root / 'server'
        self.model.write_bytes(b'model')
        self.server.write_bytes(b'runtime')
        self.env = patch.dict('os.environ', {'LLM_PROMPT_CACHE_DIR': str(root / 'cache')})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.settings = ModelSettings(str(self.model), str(self.server), '2')

    def test_cache_survives_replacing_model_process(self):
        cache = PromptCache(self.settings)
        first = DiskSlot(cache.directory)
        cache.save(first)
        second = DiskSlot(cache.directory)
        second.state = b''
        PromptCache(self.settings).restore(second)
        self.assertEqual(second.state, b'processed prefix')

    def test_missing_cache_does_not_restore(self):
        cache = PromptCache(self.settings)
        class NoCalls:
            def slot(self, *args):
                raise AssertionError('No saved state to restore')
        cache.restore(NoCalls())

    def test_changed_model_or_runtime_cannot_reuse_snapshot(self):
        initial = PromptCache(self.settings).filename
        self.model.write_bytes(b'different model')
        changed_model = PromptCache(self.settings).filename
        self.assertNotEqual(initial, changed_model)
        self.server.write_bytes(b'different runtime')
        self.assertNotEqual(changed_model, PromptCache(self.settings).filename)

    def test_failed_save_preserves_last_good_snapshot(self):
        cache = PromptCache(self.settings)
        cache.save(DiskSlot(cache.directory))
        class BrokenSlot:
            def slot(self, action, filename):
                (cache.directory / filename).write_bytes(b'partial')
                raise OSError('disk write failed')
        cache.save(BrokenSlot())
        self.assertEqual((cache.directory / cache.filename).read_bytes(), b'processed prefix')

    def test_bad_restore_discards_snapshot_and_falls_back_to_cold(self):
        cache = PromptCache(self.settings)
        cache.save(DiskSlot(cache.directory))
        class BrokenSlot:
            def slot(self, *args):
                raise ValueError('incompatible state')
        cache.restore(BrokenSlot())
        self.assertFalse((cache.directory / cache.filename).exists())

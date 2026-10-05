"""The model owner must release resources on switching, startup failure, and timeout."""

import threading
import unittest
from unittest.mock import Mock, patch

import requests

import model_runtime
from langgraph_vision_assistant.model.runtime import LocalModel


class LocalRuntimeTests(unittest.TestCase):
    def test_dead_cached_process_is_replaced_before_next_inference(self):
        dead_model = Mock()
        dead_model.is_alive.return_value = False
        replacement = Mock()
        with patch.object(model_runtime, '_model', dead_model), \
             patch.object(model_runtime, '_kind', 'llm'), \
             patch.object(model_runtime, '_lock', threading.Lock()), \
             patch('langgraph_vision_assistant.model.runtime.LocalModel', return_value=replacement):
            with model_runtime.model_session('llm') as loaded:
                self.assertIs(loaded, replacement)
            dead_model.close.assert_called_once()

    def test_inference_timeout_uses_the_routes_retryable_error(self):
        model = LocalModel.__new__(LocalModel)
        model.url = 'http://127.0.0.1:12345'
        model.process = None
        model.log = Mock()
        model.client = Mock()
        model.client.post.side_effect = requests.ReadTimeout('inference took too long')
        with self.assertRaises(TimeoutError):
            model.create_chat_completion(messages=[])

    def test_switching_to_vision_closes_llm_before_loading_detection_model(self):
        events = []
        language_model = Mock()
        language_model.close.side_effect = lambda: events.append('closed')
        vision_model = Mock()
        vision_model.eval.return_value = vision_model

        def load_model(*_):
            self.assertEqual(events, ['closed'])
            return vision_model

        with patch.object(model_runtime, '_model', language_model), \
             patch.object(model_runtime, '_kind', 'llm'), \
             patch.object(model_runtime, '_lock', threading.Lock()), \
             patch('inference.model_fn', side_effect=load_model):
            with model_runtime.model_session('boxes') as model:
                self.assertIs(model, vision_model)

    def test_failed_model_startup_releases_shared_lock(self):
        lock = threading.Lock()
        with patch.object(model_runtime, '_model', None), \
             patch.object(model_runtime, '_kind', None), \
             patch.object(model_runtime, '_lock', lock), \
             patch('langgraph_vision_assistant.model.runtime.LocalModel', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                with model_runtime.model_session('llm'):
                    self.fail('Unavailable models cannot enter an inference session')
            self.assertFalse(lock.locked())

    def test_close_reaps_a_process_that_ignores_termination(self):
        import subprocess
        model = LocalModel.__new__(LocalModel)
        model.client = Mock()
        model.log = Mock()
        process = model.process = Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired('llama-server', 5), 0]
        model.close()
        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        self.assertEqual(process.wait.call_count, 2)
        model.client.close.assert_called_once()
        model.log.close.assert_called_once()

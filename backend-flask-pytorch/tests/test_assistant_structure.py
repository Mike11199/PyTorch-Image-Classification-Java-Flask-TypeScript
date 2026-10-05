"""Contracts preserved by the typed request and local-runtime boundaries."""

import unittest
from unittest.mock import patch

from langgraph_vision_assistant.api.schemas import AssistantRequest
from langgraph_vision_assistant.model.settings import ModelSettings


class StructureTests(unittest.TestCase):
    def test_request_normalizes_without_changing_browser_field_names(self):
        request = AssistantRequest.model_validate({
            'message': '  cats red  ', 'page': 'mask',
            'availableClasses': ['dog', 'cat', 'cat'],
        })
        self.assertEqual(request.to_context(), {
            'message': 'cats red', 'page': 'mask',
            'availableClasses': ['cat', 'dog'], 'view': {},
        })

    def test_request_rejects_nonfinite_view_values_and_coercion(self):
        valid = {'message': 'cats', 'page': 'mask', 'availableClasses': ['cat']}
        for changes in ({'view': {'x': float('nan')}}, {'message': 123},
                        {'availableClasses': ('cat',)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                AssistantRequest.model_validate({**valid, **changes})

    def test_runtime_settings_read_environment_once(self):
        with patch.dict('os.environ', {'LLM_MODEL_PATH': 'cats.gguf',
                                      'LLM_SERVER_PATH': 'llama-server', 'LLM_THREADS': '4'}):
            settings = ModelSettings.from_environment()
        self.assertEqual(settings.model_path, 'cats.gguf')
        self.assertEqual(settings.server_path, 'llama-server')
        self.assertEqual(settings.threads, '4')

import unittest

from langgraph_vision_assistant.api.request import validate_request


class RequestTests(unittest.TestCase):
    def test_trims_message_and_defaults_view(self):
        result = validate_request({'message': '  only cats  ', 'page': 'boxes', 'availableClasses': ['cat']})
        self.assertEqual(result['message'], 'only cats')
        self.assertEqual(result['view'], {})

    def test_rejects_bad_or_excessive_request_fields(self):
        valid = {'message': 'hello', 'page': 'boxes', 'availableClasses': ['cat'], 'view': {}}
        invalid = [[], {**valid, 'message': ''}, {**valid, 'message': 'x' * 1001},
                   {**valid, 'page': 'other'}, {**valid, 'availableClasses': ['cat'] * 81},
                   {**valid, 'availableClasses': ['<script>']}, {**valid, 'view': []},
                   {**valid, 'view': {'x': 'a' * 3001}}]
        for body in invalid:
            with self.subTest(body=str(body)[:100]), self.assertRaises(ValueError):
                validate_request(body)

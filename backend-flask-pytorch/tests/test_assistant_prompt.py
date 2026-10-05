import copy
import json
import unittest

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph_vision_assistant.agent.prompt import initial_messages


class PromptTests(unittest.TestCase):
    def test_request_and_viewer_snapshot_stay_separate_and_unchanged(self):
        context = {'message': 'Make cats red and dogs puple', 'page': 'mask',
                   'availableClasses': ['cat', 'dog'], 'view': {'selectedClasses': ['cat']}}
        original = copy.deepcopy(context)
        messages = initial_messages(context)
        self.assertIsInstance(messages[0], SystemMessage)
        self.assertIsInstance(messages[1], HumanMessage)
        self.assertEqual(messages[1].content, context['message'])
        snapshot = json.loads(messages[0].content.split('Viewer context: ', 1)[1])
        self.assertEqual(snapshot['view'], {'selectedClasses': ['cat']})
        self.assertNotIn('message', snapshot)
        self.assertEqual(context, original)

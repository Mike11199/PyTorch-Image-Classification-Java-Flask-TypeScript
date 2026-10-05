"""Check that only a complete, successful tool turn can change the browser."""

import unittest

from langchain_core.messages import AIMessage, ToolMessage

from langgraph_vision_assistant.tools.results import FailedToolBatch, browser_commands


class ToolResultTests(unittest.TestCase):
    def test_no_calls_do_not_collect_old_commands(self):
        old_result = ToolMessage(content='prepared', tool_call_id='old',
                                 artifact={'type': 'reset_view'})
        self.assertEqual(browser_commands([old_result], []), [])

    def test_missing_or_mismatched_results_are_rejected(self):
        for messages in ([], [AIMessage(content='hello')],
                         [ToolMessage(content='prepared', tool_call_id='wrong')]):
            with self.subTest(messages=messages), self.assertRaises(RuntimeError):
                browser_commands(messages, ['expected'])

    def test_duplicate_results_are_rejected(self):
        result = ToolMessage(content='prepared', tool_call_id='first')
        with self.assertRaises(RuntimeError):
            browser_commands([result, result], ['first', 'second'])

    def test_failure_rejects_successful_commands_in_same_turn(self):
        success = ToolMessage(content='prepared', tool_call_id='first',
                              artifact={'type': 'reset_view'})
        failure = ToolMessage(content='invalid class', tool_call_id='second', status='error')
        with self.assertRaises(FailedToolBatch):
            browser_commands([success, failure], ['first', 'second'])

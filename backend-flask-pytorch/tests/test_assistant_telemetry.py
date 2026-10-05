import re
import unittest
from unittest.mock import patch

from flask import Flask
from langchain_core.messages import AIMessage

from langgraph_vision_assistant import register_langgraph_vision_assistant
from langgraph_vision_assistant.agent.graph import build_workflow


CONTEXT = {
    'message': 'only cars', 'page': 'boxes',
    'availableClasses': ['car'], 'view': {},
}


class AssistantTelemetryTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        register_langgraph_vision_assistant(app)
        self.client = app.test_client()

    def test_route_logs_one_correlated_terminal_event(self):
        workflow = build_workflow(
            lambda *_: AIMessage(content='', tool_calls=[{'name': 'reset_view', 'args': {}, 'id': 'reset'}])
        )
        with self.assertLogs('langgraph_vision_assistant', level='INFO') as logs:
            with patch('langgraph_vision_assistant.service.workflow', workflow):
                response = self.client.post('/api-pytorch/vision-assistant', json=CONTEXT)

        self.assertEqual(response.status_code, 200)
        request_ids = re.findall(r'request=([0-9a-f]{8})', '\n'.join(logs.output))
        self.assertTrue(request_ids)
        self.assertEqual(set(request_ids), {request_ids[0]})
        terminal = [line for line in logs.output
                    if 'event=request_completed' in line or 'event=request_failed' in line]
        self.assertEqual(len(terminal), 1)
        self.assertIn('event=request_started', '\n'.join(logs.output))

    def test_workflow_logs_calls_and_failed_batches(self):
        generated = iter([
            AIMessage(content='', tool_calls=[{'name': 'unknown', 'args': {}, 'id': 'bad'}]),
            AIMessage(content='', tool_calls=[{'name': 'reset_view', 'args': {}, 'id': 'reset'}]),
        ])
        workflow = build_workflow(lambda *_: next(generated))
        with self.assertLogs('langgraph_vision_assistant', level='INFO') as logs:
            workflow.invoke({'context': CONTEXT, 'request_id': 'abc12345'})

        output = '\n'.join(logs.output)
        self.assertIn('event=tools_requested', output)
        self.assertIn('event=tool_batch_failed', output)
        self.assertIn('event=tool_batch_completed', output)
        self.assertIn('"name":"reset_view"', output)


if __name__ == '__main__':
    unittest.main()

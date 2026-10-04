import re
import unittest
from unittest.mock import patch

from flask import Flask

from langgraph_vision_assistant import register_langgraph_vision_assistant
from langgraph_vision_assistant.workflow import build_workflow


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
            lambda *_: {'actions': [{'type': 'reset_view'}]}
        )
        with self.assertLogs('langgraph_vision_assistant', level='INFO') as logs:
            with patch('langgraph_vision_assistant.routes.workflow', workflow):
                response = self.client.post('/api-pytorch/vision-assistant', json=CONTEXT)

        self.assertEqual(response.status_code, 200)
        request_ids = re.findall(r'request=([0-9a-f]{8})', '\n'.join(logs.output))
        self.assertTrue(request_ids)
        self.assertEqual(set(request_ids), {request_ids[0]})
        terminal = [line for line in logs.output
                    if 'event=request_completed' in line or 'event=request_failed' in line]
        self.assertEqual(len(terminal), 1)
        self.assertIn('event=request_started', '\n'.join(logs.output))

    def test_workflow_logs_plan_and_validation_attempts(self):
        generated = iter([
            {'actions': [{'type': 'unknown'}]},
            {'actions': [{'type': 'reset_view'}]},
        ])
        workflow = build_workflow(lambda *_: next(generated))
        with self.assertLogs('langgraph_vision_assistant', level='INFO') as logs:
            workflow.invoke({'context': CONTEXT, 'request_id': 'abc12345'})

        output = '\n'.join(logs.output)
        self.assertIn('event=plan_normalized', output)
        self.assertIn('event=validation_failed', output)
        self.assertIn('event=plan_validated', output)
        self.assertIn('"type":"reset_view"', output)


if __name__ == '__main__':
    unittest.main()

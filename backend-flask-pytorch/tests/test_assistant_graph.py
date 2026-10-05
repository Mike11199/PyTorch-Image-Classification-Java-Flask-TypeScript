import unittest
from unittest.mock import patch

from flask import Flask
from langchain_core.messages import AIMessage, ToolMessage

from langgraph_vision_assistant.agent.graph import PlanError, build_workflow
from langgraph_vision_assistant import register_langgraph_vision_assistant

CONTEXT = {'message': 'only cats', 'page': 'mask', 'availableClasses': ['cat', 'dog'], 'view': {}}


def calls(*actions, content=''):
    return AIMessage(content=content, tool_calls=[
        {'name': action['type'], 'args': {k: v for k, v in action.items() if k != 'type'},
         'id': f'call-{i}', 'type': 'tool_call'}
        for i, action in enumerate(actions)
    ])


class GraphTests(unittest.TestCase):
    def run_graph(self, model):
        return build_workflow(model).invoke({'context': CONTEXT, 'request_id': 'test'})

    def test_commands_keep_order_and_discard_generated_claims(self):
        actions = [
            {'type': 'set_class_color', 'className': 'cat', 'color': '#17a2b8', 'target': 'both'},
            {'type': 'set_class_color', 'className': 'cat', 'color': '#123456', 'target': 'boxes'},
        ]
        result = self.run_graph(lambda *_: calls(*actions, content='99 cats!'))
        self.assertEqual(result['result'], {'actions': actions, 'message': ''})
        self.assertEqual(result['attempt'], 1)

    def test_collector_restores_call_order_from_reversed_results(self):
        from langgraph_vision_assistant.agent.nodes import collect_results
        request = calls({'type': 'reset_view'}, {'type': 'set_confidence', 'value': 0.5})
        result = collect_results({'request_id': 'test', 'attempt': 1, 'messages': [
            request,
            ToolMessage(content='prepared', tool_call_id='call-1', artifact={'type': 'set_confidence', 'value': 0.5}),
            ToolMessage(content='prepared', tool_call_id='call-0', artifact={'type': 'reset_view'}),
        ]})
        self.assertEqual(result['result']['actions'], [
            {'type': 'reset_view'}, {'type': 'set_confidence', 'value': 0.5},
        ])

    def test_failed_batch_is_discarded_and_errors_reach_model(self):
        def model(messages, tools, context, request_id):
            self.assertEqual(request_id, 'test')
            results = [msg for msg in messages if isinstance(msg, ToolMessage)]
            if not results:
                return calls({'type': 'reset_view'}, {'type': 'set_visible_classes', 'classes': ['dragon']})
            self.assertEqual([result.status for result in results], ['success', 'error'])
            self.assertIn('dragon', results[-1].content)
            return calls({'type': 'set_visible_classes', 'classes': ['cat']})
        result = self.run_graph(model)
        self.assertEqual(result['result']['actions'], [{'type': 'set_visible_classes', 'classes': ['cat']}])
        self.assertEqual(result['attempt'], 2)

    def test_read_result_can_drive_the_next_tool_call(self):
        def model(messages, *_):
            results = [msg for msg in messages if isinstance(msg, ToolMessage)]
            if not results:
                return calls({'type': 'get_viewer_context'})
            self.assertIn('cat', results[-1].content)
            return calls({'type': 'reset_view'})
        result = self.run_graph(model)
        self.assertEqual(result['attempt'], 2)
        self.assertEqual(result['result']['actions'], [{'type': 'reset_view'}])

    def test_mixed_read_and_command_returns_only_command(self):
        result = self.run_graph(lambda *_: calls({'type': 'get_viewer_context'}, {'type': 'reset_view'}))
        self.assertEqual(result['result']['actions'], [{'type': 'reset_view'}])

    def test_read_loops_and_errors_stop_after_three_model_calls(self):
        for response in (calls({'type': 'get_viewer_context'}), calls({'type': 'unknown'})):
            seen = []
            def model(*args):
                seen.append(args)
                return response
            with self.subTest(response=response), self.assertRaises(PlanError):
                self.run_graph(model)
            self.assertEqual(len(seen), 3)

    def test_malformed_and_oversized_responses_never_run_tools(self):
        duplicate = AIMessage(content='', tool_calls=[
            {'name': 'reset_view', 'args': {}, 'id': 'same'},
            {'name': 'reset_view', 'args': {}, 'id': 'same'},
        ])
        invalid = AIMessage(content='', invalid_tool_calls=[{
            'name': 'reset_view', 'args': '{', 'id': 'bad', 'error': 'invalid json',
        }])
        for response in ({'actions': []}, calls(*[{'type': 'reset_view'}] * 7), duplicate,
                         invalid, AIMessage(content=''), AIMessage(content='x' * 241)):
            with self.subTest(response=response), self.assertRaises(PlanError):
                self.run_graph(lambda *_: response)

    def test_plain_clarification_has_no_actions(self):
        result = self.run_graph(lambda *_: AIMessage(content='Which class should I change?'))
        self.assertEqual(result['result'], {'actions': [], 'message': 'Which class should I change?'})


class RouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        register_langgraph_vision_assistant(app)
        self.client = app.test_client()

    def test_browser_response_shape_and_request_id(self):
        graph = build_workflow(lambda *_: calls({'type': 'reset_view'}, content='99 cats!'))
        with patch('langgraph_vision_assistant.service.workflow', graph):
            result = self.client.post('/api-pytorch/vision-assistant', json=CONTEXT)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json, {'actions': [{'type': 'reset_view'}], 'message': ''})
        self.assertTrue(result.headers['X-Request-ID'])

    def test_errors_release_request_slot(self):
        for error, status in [(TimeoutError(), 429), (FileNotFoundError(), 503),
                              (RuntimeError(), 502), (PlanError('invalid'), 422)]:
            def model(*_):
                raise error
            with patch('langgraph_vision_assistant.service.workflow', build_workflow(model)):
                for _ in range(2):
                    with self.subTest(error=error):
                        self.assertEqual(self.client.post('/api-pytorch/vision-assistant', json=CONTEXT).status_code, status)

    def test_occupied_request_slot_returns_busy_without_calling_model(self):
        from langgraph_vision_assistant.service import _request_slot
        _request_slot.acquire()
        try:
            result = self.client.post('/api-pytorch/vision-assistant', json=CONTEXT)
            self.assertEqual(result.status_code, 429)
        finally:
            _request_slot.release()

    def test_rejects_malformed_and_large_requests(self):
        self.assertEqual(self.client.post('/api-pytorch/vision-assistant', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api-pytorch/vision-assistant', data='x' * 16385).status_code, 413)

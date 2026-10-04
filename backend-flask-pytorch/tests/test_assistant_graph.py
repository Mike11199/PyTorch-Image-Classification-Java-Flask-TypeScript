import unittest
from unittest.mock import patch

from flask import Flask

from langgraph_vision_assistant.workflow import PlanError, build_workflow
from langgraph_vision_assistant.workflow_state import AssistantState
from langgraph_vision_assistant import register_langgraph_vision_assistant


CONTEXT = {'message': 'only cars', 'page': 'boxes', 'availableClasses': ['car'], 'view': {}}


class GraphTests(unittest.TestCase):
    def test_workflow_state_names_explain_the_request_lifecycle(self):
        self.assertEqual(set(AssistantState.__annotations__), {
            'context', 'request_id', 'plan', 'validation_error', 'attempt', 'result'
        })

    def test_repairs_invalid_plan_once(self):
        attempts = iter([{'actions': [{'type': 'oops'}]},
                         {'actions': [{'type': 'set_visible_classes', 'classes': ['car']}]}])
        result = build_workflow(lambda *_: next(attempts)).invoke({'context': CONTEXT, 'request_id': 'test'})
        self.assertEqual(result['attempt'], 2)
        self.assertEqual(result['result']['actions'][0]['classes'], ['car'])

    def test_allows_two_repairs_before_stopping(self):
        attempts = iter([
            {'actions': [{'type': 'oops'}]},
            {'actions': [{'type': 'still_wrong'}]},
            {'actions': [{'type': 'set_visible_classes', 'classes': ['car']}]},
        ])
        result = build_workflow(lambda *_: next(attempts)).invoke({'context': CONTEXT, 'request_id': 'test'})
        self.assertEqual(result['attempt'], 3)
        self.assertEqual(result['result']['actions'][0]['classes'], ['car'])

    def test_normalizes_explicit_class_color_and_layer_phrases(self):
        context = {
            'message': 'Make cat masks blue and make dog boxes and masks gray',
            'page': 'mask', 'availableClasses': ['cat', 'dog'], 'view': {},
        }
        wrong = {'actions': [
            {'type': 'set_class_color', 'className': 'cat', 'color': '#ff0000', 'target': 'masks'},
            {'type': 'set_class_color', 'className': 'dog', 'color': '#800080', 'target': 'boxes'},
        ]}
        actions = build_workflow(lambda *_: wrong).invoke({'context': context, 'request_id': 'test'})['result']['actions']
        self.assertEqual(actions, [
            {'type': 'set_class_color', 'className': 'cat', 'color': '#0000ff', 'target': 'masks'},
            {'type': 'set_class_color', 'className': 'dog', 'color': '#444444', 'target': 'both'},
        ])

    def test_invalid_plan_stops_without_partial_actions(self):
        with self.assertRaises(PlanError):
            build_workflow(lambda *_: {'actions': [{'type': 'oops'}]}).invoke({'context': CONTEXT, 'request_id': 'test'})


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        register_langgraph_vision_assistant(self.app)
        self.client = self.app.test_client()

    def test_returns_validated_actions_and_no_generated_count_claims(self):
        graph = build_workflow(lambda *_: {'actions': [{'type': 'reset_view'}], 'message': '99 cars!'})
        with patch('langgraph_vision_assistant.routes.workflow', graph):
            result = self.client.post('/api-pytorch/vision-assistant', json=CONTEXT)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json, {'actions': [{'type': 'reset_view'}], 'message': ''})

    def test_busy_model_returns_retryable_response_and_releases_slot(self):
        graph = build_workflow(lambda *_: (_ for _ in ()).throw(TimeoutError()))
        with patch('langgraph_vision_assistant.routes.workflow', graph):
            for _ in range(2):
                result = self.client.post('/api-pytorch/vision-assistant', json=CONTEXT)
                self.assertEqual(result.status_code, 429)

    def test_rejects_malformed_and_large_requests(self):
        self.assertEqual(self.client.post('/api-pytorch/vision-assistant', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api-pytorch/vision-assistant', data='x' * 16385).status_code, 413)


if __name__ == '__main__':
    unittest.main()

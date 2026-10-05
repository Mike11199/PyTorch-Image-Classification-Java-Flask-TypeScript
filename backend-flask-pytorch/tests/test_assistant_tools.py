import copy
import unittest

from langchain_core.messages import AIMessage
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from langgraph_vision_assistant import tools


CONTEXT = {'message': 'test', 'page': 'mask', 'availableClasses': ['cat', 'dog'], 'view': {'selectedClasses': ['cat']}}


class ViewerToolTests(unittest.TestCase):
    def invoke(self, name, args, page='mask'):
        self.assertTrue(hasattr(tools, 'VIEWER_TOOLS'), 'Viewer operations must be registered tools')
        graph = StateGraph(dict)
        graph.add_node('tools', ToolNode(tools.VIEWER_TOOLS, handle_tool_errors=True))
        graph.add_edge(START, 'tools')
        graph.add_edge('tools', END)
        call = {'name': name, 'args': args, 'id': 'call-1', 'type': 'tool_call'}
        state = {'messages': [AIMessage(content='', tool_calls=[call])],
                 'context': {**CONTEXT, 'page': page}}
        return graph.compile().invoke(state)['messages'][0]

    def test_every_command_preserves_its_browser_contract(self):
        cases = [
            ('set_visible_classes', {'classes': []}),
            ('set_class_color', {'className': 'cat', 'color': '#17A2b8', 'target': 'both'}),
            ('set_confidence', {'value': 0.5}),
            ('set_mask_opacity', {'value': 1}),
            ('set_layers', {'boxes': True, 'masks': False, 'labels': True}),
            ('count_detections', {'classes': ['dog'], 'region': 'left'}),
            ('select_detection', {'className': 'cat', 'mode': 'leftmost'}),
            ('seek_detection', {'className': 'dog', 'mode': 'next'}),
            ('reset_view', {}),
        ]
        for name, args in cases:
            with self.subTest(name=name):
                original = copy.deepcopy(args)
                result = self.invoke(name, args, page='video')
                self.assertEqual(result.status, 'success', result.content)
                self.assertEqual(result.tool_call_id, 'call-1')
                self.assertEqual(result.artifact, {'type': name, **args})
                self.assertEqual(args, original)
                self.assertIn('prepared', result.content.lower())

    def test_read_context_returns_actual_snapshot_without_command(self):
        result = self.invoke('get_viewer_context', {})
        self.assertIsNone(result.artifact)
        self.assertIn('selectedClasses', result.content)
        self.assertIn('cat', result.content)

    def test_color_defaults_to_the_pages_visible_layers(self):
        for page, target in [('boxes', 'boxes'), ('mask', 'both'), ('video', 'both')]:
            with self.subTest(page=page):
                result = self.invoke('set_class_color', {'className': 'cat', 'color': '#123456'}, page)
                self.assertEqual(result.status, 'success', result.content)
                self.assertEqual(result.artifact['target'], target)

    def test_bad_arguments_and_unsupported_operations_return_errors(self):
        cases = [
            ('set_confidence', {'value': value}, 'mask')
            for value in (True, '0.5', -1, 2, float('nan'), float('inf'))
        ] + [
            ('reset_view', {'extra': 1}, 'mask'),
            ('set_visible_classes', {'classes': ['dragon']}, 'mask'),
            ('set_visible_classes', {'classes': [1]}, 'mask'),
            ('set_visible_classes', {'classes': ['cat'] * 81}, 'mask'),
            ('set_class_color', {'className': 'cat', 'color': '#12345', 'target': 'both'}, 'mask'),
            ('set_class_color', {'className': 'cat', 'color': '#123456\n', 'target': 'both'}, 'mask'),
            ('set_class_color', {'className': 'cat', 'color': '#123456', 'target': 'masks'}, 'boxes'),
            ('set_mask_opacity', {'value': 0.5}, 'boxes'),
            ('set_layers', {'boxes': True, 'masks': True, 'labels': True}, 'boxes'),
            ('set_layers', {'boxes': 1, 'masks': False, 'labels': True}, 'mask'),
            ('seek_detection', {'className': 'cat', 'mode': 'first'}, 'mask'),
            ('eval', {'code': 'anything'}, 'mask'),
        ]
        for name, args, page in cases:
            with self.subTest(name=name, args=args, page=page):
                result = self.invoke(name, args, page)
                self.assertEqual(result.status, 'error', result)
                self.assertIsNone(result.artifact)

    def test_model_cannot_supply_context(self):
        self.assertTrue(hasattr(tools, 'VIEWER_TOOLS'))
        for registered in tools.VIEWER_TOOLS:
            schema = convert_to_openai_tool(registered)['function']['parameters']
            self.assertNotIn('context', schema.get('properties', {}))

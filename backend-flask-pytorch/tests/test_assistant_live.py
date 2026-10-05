"""Opt-in tests against the real local model, never a mocked completion."""

import os
import unittest
import json
from time import perf_counter
from typing import Annotated, Literal

from pydantic import Field

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode


@tool
def get_viewer_context() -> str:
    """Read the viewer's current selected class and color."""
    return '{"selectedClass": "dog", "color": "#17a2b8"}'


@tool
def set_class_color(className: Literal['cat', 'dog'],
                    color: Annotated[str, Field(pattern=r'^#[0-9a-fA-F]{6}$')],
                    target: Literal['boxes', 'masks', 'both']) -> str:
    """Prepare a class color using a six-digit hex color and boxes/masks/both target."""
    return 'Command prepared.'


@tool
def select_palette_color(color: str) -> str:
    """Select a hex color from the viewer's restricted palette."""
    if color != '#17a2b8':
        raise ValueError('That color is unavailable. Select #17a2b8 instead.')
    return 'Color selected.'


@unittest.skipUnless(os.getenv('RUN_LLM_SMOKE') == '1', 'Set RUN_LLM_SMOKE=1 for real Qwen inference.')
class LiveToolCallingTests(unittest.TestCase):
    def setUp(self):
        from langgraph_vision_assistant.model.client import call_model
        self.call_model = call_model
        self.context = {'page': 'mask', 'availableClasses': ['cat', 'dog'], 'view': {}}
        self.tools = [get_viewer_context, set_class_color]

    def test_compound_color_calls(self):
        from langgraph_vision_assistant.agent.prompt import initial_messages
        response = self.call_model([
            *initial_messages({**self.context, 'message': 'Make cats red and dogs teal.'}),
        ], self.tools, self.context, 'live-colors')
        self.assertEqual(len(response.tool_calls), 2, response)
        self.assertEqual(
            {(call['args']['className'], call['args']['color'].lower()) for call in response.tool_calls},
            {('cat', '#ff0000'), ('dog', '#008080')},
        )
        self.assertTrue(all(call['name'] == 'set_class_color' for call in response.tool_calls))

    def test_model_uses_read_tool_result(self):
        messages = [
            SystemMessage('Use tools. First read viewer context, then set the selected class to its returned color. Target both.'),
            HumanMessage('Apply the selected color to the selected class.'),
        ]
        response = self.call_model(messages, [get_viewer_context], self.context, 'live-read')
        self.assertEqual([call['name'] for call in response.tool_calls], ['get_viewer_context'])
        call = response.tool_calls[0]
        result = get_viewer_context.invoke(call)
        self.assertIsInstance(result, ToolMessage)
        response = self.call_model(messages + [response, result], self.tools, self.context, 'live-read')
        self.assertEqual(len(response.tool_calls), 1, response)
        self.assertEqual(response.tool_calls[0]['name'], 'set_class_color')
        self.assertEqual(response.tool_calls[0]['args']['className'], 'dog')
        self.assertEqual(response.tool_calls[0]['args']['color'], '#17a2b8')

    def test_model_repairs_a_real_tool_error(self):
        messages = [SystemMessage('Use the tool. If the color is unavailable, use the alternative in its error.'),
                    HumanMessage('Select red (#ff0000).')]
        response = self.call_model(messages, [select_palette_color], self.context, 'live-error')
        graph = StateGraph(dict)
        graph.add_node('tools', ToolNode([select_palette_color], handle_tool_errors=True))
        graph.add_edge(START, 'tools')
        graph.add_edge('tools', END)
        result = graph.compile().invoke({'messages': [response]})['messages'][0]
        self.assertEqual(result.status, 'error', result)
        repaired = self.call_model(messages + [response, result], [select_palette_color], self.context, 'live-error')
        self.assertEqual(len(repaired.tool_calls), 1, repaired)
        result = graph.compile().invoke({'messages': [repaired]})['messages'][0]
        self.assertEqual(result.status, 'success', result)
        self.assertEqual(repaired.tool_calls[0]['args']['color'], '#17a2b8')


@unittest.skipUnless(os.getenv('RUN_LLM_SMOKE') == '1', 'Set RUN_LLM_SMOKE=1 for real Qwen inference.')
class LiveViewerTests(unittest.TestCase):
    def run_request(self, message, page='mask', view=None):
        from langgraph_vision_assistant.agent.graph import build_workflow
        started = perf_counter()
        result = build_workflow().invoke({'context': {
            'message': message, 'page': page, 'availableClasses': ['cat', 'dog'], 'view': view or {},
        }, 'request_id': 'live-viewer'})['result']
        print(json.dumps({'page': page, 'prompt': message, 'result': result,
                          'seconds': round(perf_counter() - started, 2)}), flush=True)
        return result['actions']

    def test_colors_across_all_viewers(self):
        cases = [
            ('Make cats red and dogs puple', {'cat': '#ff0000', 'dog': '#800080'}),
            ('Make cats red and dogs teal', {'cat': '#ff0000', 'dog': '#008080'}),
            ('Make dogs dark blue', {'dog': '#00008b'}),
            ('Make cats #123456 and dogs #abcdef', {'cat': '#123456', 'dog': '#abcdef'}),
        ]
        for page in ('boxes', 'mask', 'video'):
            for prompt, colors in cases:
                with self.subTest(page=page, prompt=prompt):
                    actions = self.run_request(prompt, page)
                    self.assertEqual(len(actions), len(colors))
                    self.assertTrue(all(action['type'] == 'set_class_color' for action in actions))
                    self.assertEqual({action['className']: action['color'].lower() for action in actions}, colors)
                    self.assertTrue(all(action['target'] == ('boxes' if page == 'boxes' else 'both') for action in actions))

    def test_filter_does_not_change_other_settings(self):
        for page in ('boxes', 'mask', 'video'):
            with self.subTest(page=page):
                self.assertEqual(self.run_request('Only show cats', page), [
                    {'type': 'set_visible_classes', 'classes': ['cat']},
                ])

    def test_explicit_layers_opacity_and_selected_class(self):
        for page in ('mask', 'video'):
            with self.subTest(page=page, operation='layers'):
                self.assertEqual(self.run_request('Make cat masks #123456 and dog boxes #abcdef', page), [
                    {'type': 'set_class_color', 'className': 'cat', 'color': '#123456', 'target': 'masks'},
                    {'type': 'set_class_color', 'className': 'dog', 'color': '#abcdef', 'target': 'boxes'},
                ])
            with self.subTest(page=page, operation='opacity'):
                self.assertEqual(self.run_request('Make masks fully opaque', page), [{'type': 'set_mask_opacity', 'value': 1}])
        self.assertEqual(self.run_request('Make those teal', view={'selectedClasses': ['cat']}), [
            {'type': 'set_class_color', 'className': 'cat', 'color': '#008080', 'target': 'both'},
        ])

    def test_unavailable_classes_and_masks_cannot_produce_commands(self):
        from langgraph_vision_assistant.agent.state import PlanError
        for prompt in ('Make dragons red', 'Show masks only'):
            with self.subTest(prompt=prompt):
                try:
                    actions = self.run_request(prompt, 'boxes')
                except PlanError:
                    continue
                self.assertEqual(actions, [])

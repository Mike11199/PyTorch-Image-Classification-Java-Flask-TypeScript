"""Check viewer rules directly, without starting Qwen or LangGraph."""

import unittest

from pydantic import ValidationError

from langgraph_vision_assistant.viewer.state import ViewerContext
from langgraph_vision_assistant.viewer.visibility import build_hide_commands
from langgraph_vision_assistant.viewer.appearance import ClassColor, class_color_command


def context(view):
    """Build the same typed context used by an assistant request."""
    return ViewerContext.from_request({
        'message': 'hide cars', 'page': 'video',
        'availableClasses': ['car', 'person'], 'view': view,
    })


class ViewerRulesTest(unittest.TestCase):
    def test_hide_cars_preserves_people(self):
        viewer = context({'filters': {'visibleClasses': []}})
        self.assertEqual(build_hide_commands(['cars'], viewer), [
            {'type': 'set_visible_classes', 'classes': ['person']},
        ])

    def test_hiding_last_class_does_not_show_everything(self):
        viewer = context({'filters': {'visibleClasses': ['car']}})
        self.assertEqual(build_hide_commands(['car'], viewer), [
            {'type': 'set_visible_classes', 'classes': None},
        ])

    def test_already_hidden_classes_stay_hidden(self):
        viewer = context({'filters': {'visibleClasses': None}})
        self.assertEqual(build_hide_commands(['cars'], viewer), [
            {'type': 'set_visible_classes', 'classes': None},
        ])

    def test_missing_layers_are_not_invented(self):
        with self.assertRaisesRegex(ValueError, 'layer settings'):
            build_hide_commands(['masks'], context({}))

    def test_malformed_layers_fail_before_a_tool_runs(self):
        with self.assertRaises(ValidationError):
            context({'layers': {'boxes': {'enabled': 'yes'}}})

    def test_prompt_snapshot_preserves_unknown_settings_and_order(self):
        view = {'highlight': None, 'filters': {'visibleClasses': []}, 'futureSetting': 42}
        viewer = context(view)
        snapshot = viewer.prompt_snapshot()
        self.assertEqual(snapshot['view'], view)
        self.assertEqual(list(snapshot['view']), list(view))
        self.assertEqual(viewer.view.filters.visible_classes, [])

    def test_color_defaults_to_boxes_labels_and_masks(self):
        command = class_color_command(ClassColor(className='car', color='purple'), context({}))
        self.assertEqual(command, {
            'type': 'set_class_color', 'className': 'car', 'color': '#800080', 'target': 'both',
        })

    def test_layer_and_class_hide_can_be_combined(self):
        viewer = context({'filters': {'visibleClasses': []},
                          'layers': {'boxes': {'enabled': True}, 'masks': {'enabled': True},
                                     'labels': {'enabled': False}}})
        self.assertEqual(build_hide_commands(['masks', 'cars'], viewer), [
            {'type': 'set_layers', 'boxes': True, 'masks': False, 'labels': False},
            {'type': 'set_visible_classes', 'classes': ['person']},
        ])

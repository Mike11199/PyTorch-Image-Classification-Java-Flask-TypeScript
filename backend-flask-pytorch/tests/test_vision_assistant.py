"""Run the real local Qwen model through the assistant. No mocks or skips.

From the repository root:
docker compose exec -T flask python -m unittest discover -s tests -p test_vision_assistant.py
"""

import unittest

from langgraph_vision_assistant.service import run_assistant


def separate_color_layers(actions):
    """A single 'both' color edit has the same effect as one edit per layer."""
    expanded = []
    for action in actions:
        if action['type'] == 'set_class_color' and action['target'] == 'both':
            expanded.extend([{**action, 'target': 'boxes'}, {**action, 'target': 'masks'}])
        else:
            expanded.append(action)
    return expanded


class VisionAssistantTest(unittest.TestCase):
    def assert_actions(self, message, expected, page='video'):
        """Send a real request and compare its browser commands, ignoring order."""
        reply = run_assistant({
            'message': message,
            'page': page,
            'availableClasses': [
                'backpack', 'bicycle', 'car', 'handbag',
                'motorcycle', 'person', 'traffic light', 'truck',
            ],
            'view': {},
        }, request_id=self._testMethodName)
        self.assertCountEqual(separate_color_layers(reply['actions']), separate_color_layers(expected))
        self.assertEqual(reply['message'], '')
        self.assertGreater(reply['timing']['inference_ms'], 0)
        self.assertGreaterEqual(reply['timing']['total_ms'], reply['timing']['inference_ms'])

    def test_show_masks_only_at_full_opacity(self):
        self.assert_actions('Show masks only at full opacity', [
            {'type': 'set_layers', 'boxes': False, 'masks': True, 'labels': False},
            {'type': 'set_mask_opacity', 'value': 1},
        ])

    def test_make_car_purple_and_person_red(self):
        # "both" changes boxes, labels, and masks on the video page.
        self.assert_actions('Make car purple and person red', [
            {'type': 'set_class_color', 'className': 'car',
             'color': '#800080', 'target': 'both'},
            {'type': 'set_class_color', 'className': 'person',
             'color': '#ff0000', 'target': 'both'},
        ])

    def test_make_car_purple(self):
        self.assert_actions('Make car purple', [
            {'type': 'set_class_color', 'className': 'car',
             'color': '#800080', 'target': 'both'},
        ])

    def test_make_car_masks_blue(self):
        self.assert_actions('Make car masks blue', [
            {'type': 'set_class_color', 'className': 'car',
             'color': '#0000ff', 'target': 'masks'},
        ])

    def test_colors_on_mask_image_page(self):
        self.assert_actions('Make car purple and person red', [
            {'type': 'set_class_color', 'className': 'car', 'color': '#800080', 'target': 'both'},
            {'type': 'set_class_color', 'className': 'person', 'color': '#ff0000', 'target': 'both'},
        ], page='mask')

    def test_colors_on_boxes_image_page(self):
        self.assert_actions('Make car purple and person red', [
            {'type': 'set_class_color', 'className': 'car', 'color': '#800080', 'target': 'boxes'},
            {'type': 'set_class_color', 'className': 'person', 'color': '#ff0000', 'target': 'boxes'},
        ], page='boxes')

    def test_color_typo(self):
        self.assert_actions('Make car puple and person red', [
            {'type': 'set_class_color', 'className': 'car', 'color': '#800080', 'target': 'both'},
            {'type': 'set_class_color', 'className': 'person', 'color': '#ff0000', 'target': 'both'},
        ])

    def test_other_color_names(self):
        self.assert_actions('Make car teal and person coral', [
            {'type': 'set_class_color', 'className': 'car', 'color': '#008080', 'target': 'both'},
            {'type': 'set_class_color', 'className': 'person', 'color': '#ff7f50', 'target': 'both'},
        ])

    def test_make_car_boxes_and_masks_purple(self):
        self.assert_actions('Make car boxes and masks purple', [
            {'type': 'set_class_color', 'className': 'car',
             'color': '#800080', 'target': 'both'},
        ])

    def test_make_car_masks_only_purple(self):
        self.assert_actions('Make car masks only purple', [
            {'type': 'set_class_color', 'className': 'car',
             'color': '#800080', 'target': 'masks'},
        ])

    def test_make_car_boxes_only_purple(self):
        self.assert_actions('Make car boxes only purple', [
            {'type': 'set_class_color', 'className': 'car',
             'color': '#800080', 'target': 'boxes'},
        ])

    def test_color_two_classes_with_different_layers(self):
        self.assert_actions('Make car masks blue and person boxes red', [
            {'type': 'set_class_color', 'className': 'car',
             'color': '#0000ff', 'target': 'masks'},
            {'type': 'set_class_color', 'className': 'person',
             'color': '#ff0000', 'target': 'boxes'},
        ])

    def test_show_boxes_only(self):
        self.assert_actions('Show boxes only', [
            {'type': 'set_layers', 'boxes': True, 'masks': False, 'labels': False},
        ])

    def test_show_boxes_and_masks_only(self):
        self.assert_actions('Show boxes and masks only', [
            {'type': 'set_layers', 'boxes': True, 'masks': True, 'labels': False},
        ])

    def test_count_visible_car_detections(self):
        # The browser counts detector results in the current frame, not Qwen.
        self.assert_actions('How many car detections are visible?', [
            {'type': 'count_detections', 'classes': ['car'], 'region': 'all'},
        ])

    def test_jump_to_frame_with_most_cars(self):
        self.assert_actions('Jump to the frame with the most car detections', [
            {'type': 'seek_detection', 'className': 'car', 'mode': 'peak'},
        ])

    def test_hide_detections_below_80_percent(self):
        self.assert_actions('Hide detections below 80% confidence', [
            {'type': 'set_confidence', 'value': 0.8},
        ])

    def test_only_show_car(self):
        self.assert_actions('Only show car', [
            {'type': 'set_visible_classes', 'classes': ['car']},
        ])

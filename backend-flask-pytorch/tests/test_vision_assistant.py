import unittest

from vision_assistant.schemas import validate_request, validate_plan


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.context = validate_request({
            'message': 'Only cars, orange', 'page': 'boxes',
            'availableClasses': ['car', 'person'], 'view': {},
        })

    def test_compound_actions_preserve_order(self):
        actions = [{'type': 'set_visible_classes', 'classes': ['car']},
                   {'type': 'set_class_color', 'className': 'car', 'color': '#ff8800', 'target': 'boxes'}]
        self.assertEqual(validate_plan({'actions': actions}, self.context)['actions'], actions)

    def test_color_target_selects_boxes_masks_or_both(self):
        context = {**self.context, 'page': 'mask', 'message': 'Make car red'}
        for target in ('boxes', 'masks', 'both'):
            action = {'type': 'set_class_color', 'className': 'car',
                      'color': '#ff0000', 'target': target}
            with self.subTest(target=target):
                self.assertEqual(validate_plan({'actions': [action]}, context)['actions'], [action])

    def test_rejects_colors_not_named_in_request(self):
        context = validate_request({
            'message': 'Make cat masks blue and dog boxes and masks gray',
            'page': 'mask', 'availableClasses': ['cat', 'dog'], 'view': {},
        })
        wrong = [
            {'type': 'set_class_color', 'className': 'cat', 'color': '#ff0000', 'target': 'masks'},
            {'type': 'set_class_color', 'className': 'dog', 'color': '#800080', 'target': 'both'},
        ]
        with self.assertRaisesRegex(ValueError, 'requested colors'):
            validate_plan({'actions': wrong}, context)

        correct = [
            {'type': 'set_class_color', 'className': 'cat', 'color': '#0000ff', 'target': 'masks'},
            {'type': 'set_class_color', 'className': 'dog', 'color': '#444444', 'target': 'both'},
        ]
        self.assertEqual(validate_plan({'actions': correct}, context)['actions'], correct)

        incomplete = [
            {'type': 'set_class_color', 'className': 'cat', 'color': '#0000ff', 'target': 'masks'},
            {'type': 'set_class_color', 'className': 'dog', 'color': '#444444', 'target': 'boxes'},
        ]
        with self.assertRaisesRegex(ValueError, 'requested layers'):
            validate_plan({'actions': incomplete}, context)

    def test_unknown_class_rejects_entire_plan(self):
        with self.assertRaises(ValueError):
            validate_plan({'actions': [
                {'type': 'set_confidence', 'value': 0.8},
                {'type': 'set_visible_classes', 'classes': ['dragon']},
            ]}, self.context)

    def test_cannot_seek_or_enable_masks_on_boxes_page(self):
        for action in [{'type': 'seek_detection', 'className': 'car', 'mode': 'peak'},
                       {'type': 'set_layers', 'boxes': False, 'masks': True}]:
            with self.subTest(action=action), self.assertRaises(ValueError):
                validate_plan({'actions': [action]}, self.context)

    def test_rejects_unsafe_or_malformed_actions(self):
        for action in [{'type': 'eval', 'code': 'alert(1)'},
                       {'type': 'set_confidence', 'value': float('nan')},
                       {'type': 'set_confidence', 'value': 80},
                       {'type': 'set_confidence', 'value': True},
                       {'type': 'set_class_color', 'className': 'car', 'color': 'url(x)', 'target': 'boxes'},
                       {'type': 'set_class_color', 'className': 'car', 'color': '#ff0000', 'target': 'glow'},
                       {'type': 'reset_view', 'extra': 'ignored?'}]:
            with self.subTest(action=action), self.assertRaises(ValueError):
                validate_plan({'actions': [action]}, self.context)

    def test_limits_request_and_plan(self):
        for body in [[], {'message': 'x' * 1001, 'page': 'boxes', 'availableClasses': []},
                     {'message': 'hi', 'page': 'other', 'availableClasses': []}]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                validate_request(body)
        with self.assertRaises(ValueError):
            validate_plan({'actions': [{'type': 'reset_view'}] * 7}, self.context)


if __name__ == '__main__':
    unittest.main()

"""Define viewer tools and reject plans that cannot be executed safely."""

import math
import re

from .styles import validate_requested_colors, validate_requested_layers

MAX_ACTIONS = 6


def _object_schema(properties):
    return {
        'type': 'object', 'properties': properties,
        'required': list(properties), 'additionalProperties': False,
    }


def _enum(*values):
    return {'type': 'string', 'enum': list(values)}


CLASS_LIST = {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 80}
TOOLS = {
    'set_visible_classes': {'classes': CLASS_LIST},
    'set_class_color': {
        'className': {'type': 'string'},
        'color': {'type': 'string', 'pattern': '^#[0-9a-fA-F]{6}$'},
        'target': _enum('boxes', 'masks', 'both'),
    },
    'set_confidence': {'value': {'type': 'number', 'minimum': 0, 'maximum': 1}},
    'set_mask_opacity': {'value': {'type': 'number', 'minimum': 0, 'maximum': 1}},
    'set_layers': {'boxes': {'type': 'boolean'}, 'masks': {'type': 'boolean'}},
    'count_detections': {'classes': CLASS_LIST, 'region': _enum('all', 'left', 'right')},
    'select_detection': {
        'className': {'type': 'string'},
        'mode': _enum('leftmost', 'rightmost', 'largest', 'least_confident'),
    },
    'seek_detection': {'className': {'type': 'string'}, 'mode': _enum('first', 'next', 'peak')},
    'reset_view': {},
}


def plan_schema():
    """Return the JSON grammar used to constrain Qwen's response."""
    variants = [_object_schema({'type': _enum(name), **fields})
                for name, fields in TOOLS.items()]
    return _object_schema({
        'actions': {'type': 'array', 'maxItems': MAX_ACTIONS, 'items': {'oneOf': variants}},
        'message': {'type': 'string', 'maxLength': 240},
    })


def _valid_type(value, kind):
    checks = {
        'string': lambda: isinstance(value, str),
        'boolean': lambda: isinstance(value, bool),
        'number': lambda: type(value) in (int, float) and math.isfinite(value),
        'array': lambda: isinstance(value, list),
    }
    return checks[kind]()


def _validate_value(value, schema):
    kind = schema['type']
    if not _valid_type(value, kind):
        raise ValueError('Invalid tool argument type.')
    if value not in schema.get('enum', [value]):
        raise ValueError('Unsupported tool argument.')
    if kind == 'number' and not schema['minimum'] <= value <= schema['maximum']:
        raise ValueError('Confidence must be between 0 and 1.')
    if kind == 'string' and 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
        raise ValueError('Colors must be six-digit hex values.')
    if kind == 'array':
        if len(value) > schema['maxItems'] or any(not isinstance(item, str) for item in value):
            raise ValueError('Invalid category list.')


def _validate_action(action, context):
    if not isinstance(action, dict) or not isinstance(action.get('type'), str):
        raise ValueError('Invalid action.')
    name = action['type']
    fields = TOOLS.get(name)
    if fields is None or set(action) != {'type', *fields}:
        raise ValueError('Unknown tool or unexpected arguments.')
    for field, schema in fields.items():
        _validate_value(action[field], schema)
    available = set(context['availableClasses'])
    requested = action.get('classes', [action.get('className')])
    if any(category not in available for category in requested if category is not None):
        raise ValueError('Use only categories detected in this scene.')
    if name == 'seek_detection' and context['page'] != 'video':
        raise ValueError('Seeking is only available for video.')
    if name == 'set_layers' and action['masks'] and context['page'] == 'boxes':
        raise ValueError('This viewer has no masks.')
    if name == 'set_mask_opacity' and context['page'] == 'boxes':
        raise ValueError('This viewer has no masks.')
    if name == 'set_class_color' and action['target'] != 'boxes' and context['page'] == 'boxes':
        raise ValueError('This viewer has no masks.')


def validate_plan(plan, context):
    if not isinstance(plan, dict) or set(plan) - {'actions', 'message'}:
        raise ValueError('Expected an action plan.')
    actions = plan.get('actions')
    message = plan.get('message', '')
    if not isinstance(actions, list) or len(actions) > MAX_ACTIONS:
        raise ValueError('Use at most six actions.')
    if not isinstance(message, str) or len(message) > 240:
        raise ValueError('Invalid explanation.')
    for action in actions:
        _validate_action(action, context)
    validate_requested_colors(actions, context['message'])
    validate_requested_layers(actions, context)
    return {'actions': actions, 'message': message if not actions else ''}

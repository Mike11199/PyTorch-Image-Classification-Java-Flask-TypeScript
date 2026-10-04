"""JSON grammar and argument rules for the viewer tools."""

MAX_ACTIONS = 6


def object_schema(properties):
    return {'type': 'object', 'properties': properties,
            'required': list(properties), 'additionalProperties': False}


def enum(*values):
    return {'type': 'string', 'enum': list(values)}


CLASS_LIST = {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 80}
TOOLS = {
    'set_visible_classes': {'classes': CLASS_LIST},
    'set_class_color': {
        'className': {'type': 'string'},
        'color': {'type': 'string', 'pattern': '^#[0-9a-fA-F]{6}$'},
        'target': enum('boxes', 'masks', 'both'),
    },
    'set_confidence': {'value': {'type': 'number', 'minimum': 0, 'maximum': 1}},
    'set_layers': {'boxes': {'type': 'boolean'}, 'masks': {'type': 'boolean'}},
    'count_detections': {'classes': CLASS_LIST, 'region': enum('all', 'left', 'right')},
    'select_detection': {
        'className': {'type': 'string'},
        'mode': enum('leftmost', 'rightmost', 'largest', 'least_confident'),
    },
    'seek_detection': {'className': {'type': 'string'}, 'mode': enum('first', 'next', 'peak')},
    'reset_view': {},
}


def plan_schema():
    variants = [object_schema({'type': enum(name), **fields}) for name, fields in TOOLS.items()]
    return object_schema({
        'actions': {'type': 'array', 'maxItems': MAX_ACTIONS, 'items': {'oneOf': variants}},
        'message': {'type': 'string', 'maxLength': 240},
    })

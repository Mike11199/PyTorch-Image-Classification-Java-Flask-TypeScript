"""Validate layer words that are explicit in color-change requests."""

import re


def _requested_layers(message, classes):
    mentions = []
    for category in classes:
        pattern = rf'\b{re.escape(category.lower())}(?:s)?\b'
        mentions.extend((match.start(), match.end(), category)
                        for match in re.finditer(pattern, message.lower()))
    mentions.sort()
    requested = {}
    for index, (_, end, category) in enumerate(mentions):
        next_start = mentions[index + 1][0] if index + 1 < len(mentions) else len(message)
        clause = message[end:next_start].lower()
        layers = set()
        if re.search(r'\bbox(?:es)?\b', clause):
            layers.add('boxes')
        if re.search(r'\bmasks?\b', clause):
            layers.add('masks')
        if layers:
            requested.setdefault(category, set()).update(layers)
    return requested


def validate_requested_layers(actions, context):
    expected = _requested_layers(context['message'], context['availableClasses'])
    if not expected:
        return
    actual = {}
    for action in actions:
        if action['type'] != 'set_class_color':
            continue
        layers = {'boxes', 'masks'} if action['target'] == 'both' else {action['target']}
        actual.setdefault(action['className'], set()).update(layers)
    if any(actual.get(category, set()) != layers for category, layers in expected.items()):
        detail = '; '.join(f'{category}: {" and ".join(sorted(layers))}'
                           for category, layers in expected.items())
        raise ValueError(f'Use exactly the requested layers for each category: {detail}.')

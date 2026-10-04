"""Normalize and validate explicit color and layer instructions."""

import re

NAMED_COLORS = {
    'red': '#ff0000', 'orange': '#ff8800', 'yellow': '#ffff00',
    'green': '#00ff00', 'blue': '#0000ff', 'purple': '#5b146e',
    'gray': '#444444', 'grey': '#444444', 'white': '#ffffff',
    'black': '#000000',
}


def _class_clauses(message, classes):
    mentions = []
    for category in classes:
        pattern = rf'\b{re.escape(category.lower())}(?:s)?\b'
        mentions.extend((match.start(), match.end(), category)
                        for match in re.finditer(pattern, message.lower()))
    mentions.sort()
    for index, (_, end, category) in enumerate(mentions):
        next_start = mentions[index + 1][0] if index + 1 < len(mentions) else len(message)
        yield category, message[end:next_start].lower()


def requested_colors(message):
    message = message.lower()
    colors = set(re.findall(r'#[0-9a-f]{6}\b', message))
    colors.update(value for name, value in NAMED_COLORS.items()
                  if re.search(rf'\b{name}\b', message))
    return colors


def validate_requested_colors(actions, message):
    expected = requested_colors(message)
    if not expected:
        return
    actual = {action['color'].lower() for action in actions
              if action['type'] == 'set_class_color'}
    if actual != expected:
        raise ValueError('Use exactly the requested colors: '
                         + ', '.join(sorted(expected)) + '.')


def validate_requested_layers(actions, context):
    expected = {}
    for category, clause in _class_clauses(
            context['message'], context['availableClasses']):
        layers = set()
        if re.search(r'\bbox(?:es)?\b', clause):
            layers.add('boxes')
        if re.search(r'\bmasks?\b', clause):
            layers.add('masks')
        if layers:
            expected.setdefault(category, set()).update(layers)
    if not expected:
        return
    actual = {}
    for action in actions:
        if action['type'] == 'set_class_color':
            layers = {'boxes', 'masks'} if action['target'] == 'both' else {action['target']}
            actual.setdefault(action['className'], set()).update(layers)
    if any(actual.get(category, set()) != layers for category, layers in expected.items()):
        detail = '; '.join(f'{category}: {" and ".join(sorted(layers))}'
                           for category, layers in expected.items())
        raise ValueError(f'Use exactly the requested layers for each category: {detail}.')


def _clause_color(clause):
    names = '|'.join(map(re.escape, NAMED_COLORS))
    match = re.search(rf'#[0-9a-f]{{6}}\b|\b(?:{names})\b', clause)
    if not match:
        return None
    value = match.group()
    return value if value.startswith('#') else NAMED_COLORS[value]


def _clause_target(clause, page):
    boxes = bool(re.search(r'\bbox(?:es)?\b', clause))
    masks = bool(re.search(r'\bmasks?\b', clause))
    if boxes and masks:
        return 'both'
    if masks:
        return 'masks'
    if boxes or page == 'boxes':
        return 'boxes'
    return 'both'


def _requests_layer_visibility(message):
    layer = r'(?:box(?:es)?|masks?)'
    command = r'(?:show|hide|keep|enable|disable)'
    state = r'(?:on|off|only|visible|hidden)'
    message = message.lower()
    return bool(
        re.search(rf'\b{command}\b[^.]*\b{layer}\b', message)
        or re.search(rf'\b{layer}\b[^.]*\b{state}\b', message)
    )


def normalize_explicit_styles(plan, context):
    if not isinstance(plan, dict) or not isinstance(plan.get('actions'), list):
        return plan
    styles = []
    for category, clause in _class_clauses(context['message'], context['availableClasses']):
        color = _clause_color(clause)
        if color:
            styles.append({'type': 'set_class_color', 'className': category,
                           'color': color, 'target': _clause_target(clause, context['page'])})
    if not styles:
        return plan
    styled_classes = {action['className'] for action in styles}
    actions = [action for action in plan['actions']
               if not (isinstance(action, dict) and action.get('type') == 'set_class_color'
                       and action.get('className') in styled_classes)]
    if not _requests_layer_visibility(context['message']):
        actions = [action for action in actions
                   if not (isinstance(action, dict) and action.get('type') == 'set_layers')]
    return {**plan, 'actions': [*actions, *styles]}

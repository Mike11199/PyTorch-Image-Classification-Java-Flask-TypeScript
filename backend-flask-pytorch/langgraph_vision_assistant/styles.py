"""Enforce color and box/mask wording that the user stated explicitly.

Qwen proposes actions, but a small model can change a requested color or confuse
"mask color" with "show masks only." This module parses those unambiguous phrases
directly so the final plan preserves them exactly.
"""

import re

NAMED_COLORS = {
    'red': '#ff0000', 'orange': '#ff8800', 'yellow': '#ffff00',
    'green': '#00ff00', 'blue': '#0000ff', 'purple': '#5b146e',
    'gray': '#444444', 'grey': '#444444', 'white': '#ffffff',
    'black': '#000000',
}

CLASS_ALIASES = {
    'bike': 'bicycle',
    'bikes': 'bicycle',
    'people': 'person',
}


def _class_clauses(message, classes):
    """Yield each detected class and the words following its mention."""
    message_lower = message.lower()
    mentions = []
    for category in classes:
        pattern = rf'\b{re.escape(category.lower())}(?:s)?\b'
        mentions.extend((match.start(), match.end(), category)
                        for match in re.finditer(pattern, message_lower))
    available = set(classes)
    for alias, category in CLASS_ALIASES.items():
        if category in available:
            mentions.extend((match.start(), match.end(), category)
                            for match in re.finditer(rf'\b{alias}\b', message_lower))
    mentions.sort()
    for index, (_, end, category) in enumerate(mentions):
        next_start = mentions[index + 1][0] if index + 1 < len(mentions) else len(message)
        yield category, message[end:next_start].lower()


def _named_color(token):
    """Resolve an exact color or one with a single accidentally repeated letter."""
    if token in NAMED_COLORS:
        return NAMED_COLORS[token]
    for index in range(1, len(token)):
        if token[index] == token[index - 1]:
            repaired = token[:index] + token[index + 1:]
            if repaired in NAMED_COLORS:
                return NAMED_COLORS[repaired]
    return None


def _color_mentions(message):
    """Yield color values in their textual order."""
    for match in re.finditer(r'#[0-9a-f]{6}\b|\b[a-z]+\b', message.lower()):
        token = match.group()
        color = token if token.startswith('#') else _named_color(token)
        if color:
            yield color


def requested_colors(message):
    """Return every named or hexadecimal color explicitly present in the request."""
    return set(_color_mentions(message))


def validate_requested_colors(actions, message):
    """Reject a plan that loses or invents a color when colors were explicit."""
    expected = requested_colors(message)
    if not expected:
        return
    actual = {action['color'].lower() for action in actions
              if action['type'] == 'set_class_color'}
    if actual != expected:
        raise ValueError('Use exactly the requested colors: '
                         + ', '.join(sorted(expected)) + '.')


def validate_requested_layers(actions, context):
    """Ensure explicit box/mask color targets stay attached to the right class."""
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
    return next(_color_mentions(clause), None)


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


def _requests_full_mask_opacity(message):
    """Return whether the request explicitly asks for fully opaque masks."""
    message = message.lower()
    return bool(
        re.search(r'\bmasks?\b[^.]*\b(?:full|100\s*%)\b[^.]*\bopacity\b', message)
        or re.search(r'\b(?:full|100\s*%)\b[^.]*\b(?:mask\s+)?opacity\b', message)
    )


def apply_explicit_style_requests(plan, context):
    """Correct Qwen's plan using explicit class, color, and box/mask wording.

    Generated color actions for mentioned classes are replaced with actions parsed
    directly from the request. A color-only request also drops an accidental
    ``set_layers`` action, which would otherwise hide every box or mask globally.
    Ambiguous requests and unrelated actions are left unchanged.
    """
    if not isinstance(plan, dict) or not isinstance(plan.get('actions'), list):
        return plan
    styles = []
    for category, clause in _class_clauses(context['message'], context['availableClasses']):
        color = _clause_color(clause)
        if color:
            styles.append({'type': 'set_class_color', 'className': category,
                           'color': color, 'target': _clause_target(clause, context['page'])})
    full_mask_opacity = _requests_full_mask_opacity(context['message'])
    if not styles and not full_mask_opacity:
        return plan
    styled_classes = {action['className'] for action in styles}
    actions = [action for action in plan['actions']
               if not (isinstance(action, dict) and action.get('type') == 'set_class_color'
                       and action.get('className') in styled_classes)]
    if not _requests_layer_visibility(context['message']):
        actions = [action for action in actions
                   if not (isinstance(action, dict) and action.get('type') == 'set_layers')]
    if full_mask_opacity:
        actions = [action for action in actions
                   if not (isinstance(action, dict)
                           and action.get('type') == 'set_mask_opacity')]
        actions.append({'type': 'set_mask_opacity', 'value': 1})
    return {**plan, 'actions': [*actions, *styles]}

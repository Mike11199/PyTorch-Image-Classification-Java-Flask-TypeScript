"""Make explicit class, color, and layer phrases deterministic."""

import re

from .color_validation import NAMED_COLORS


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
    return {**plan, 'actions': [*actions, *styles]}

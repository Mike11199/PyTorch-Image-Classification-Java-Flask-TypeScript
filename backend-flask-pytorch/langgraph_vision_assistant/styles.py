"""Correct and validate Qwen plans against explicit wording in the request."""

import re

from .language import (
    class_clauses,
    clause_target,
    color_mentions,
    requested_colors,
    requests_full_mask_opacity,
    requests_layer_visibility,
)


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
    for category, clause in class_clauses(
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


def _explicit_color_actions(context):
    actions = []
    for category, clause in class_clauses(
            context['message'], context['availableClasses']):
        color = next(color_mentions(clause), None)
        if color:
            actions.append({
                'type': 'set_class_color',
                'className': category,
                'color': color,
                'target': clause_target(clause, context['page']),
            })
    return actions


def _replace_color_actions(actions, styles):
    styled_classes = {action['className'] for action in styles}
    return [action for action in actions
            if not (isinstance(action, dict)
                    and action.get('type') == 'set_class_color'
                    and action.get('className') in styled_classes)]


def apply_explicit_style_requests(plan, context):
    """Preserve explicit colors, targets, visibility, and full mask opacity."""
    if not isinstance(plan, dict) or not isinstance(plan.get('actions'), list):
        return plan

    styles = _explicit_color_actions(context)
    full_mask_opacity = requests_full_mask_opacity(context['message'])
    if not styles and not full_mask_opacity:
        return plan

    actions = _replace_color_actions(plan['actions'], styles)
    if not requests_layer_visibility(context['message']):
        actions = [action for action in actions
                   if not (isinstance(action, dict)
                           and action.get('type') == 'set_layers')]
    if full_mask_opacity:
        actions = [action for action in actions
                   if not (isinstance(action, dict)
                           and action.get('type') == 'set_mask_opacity')]
        actions.append({'type': 'set_mask_opacity', 'value': 1})
    return {**plan, 'actions': [*actions, *styles]}

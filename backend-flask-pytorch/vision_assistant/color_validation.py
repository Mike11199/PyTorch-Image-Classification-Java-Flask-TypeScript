"""Keep explicit user colors intact when the small model forms a tool plan."""

import re


NAMED_COLORS = {
    'red': '#ff0000', 'orange': '#ff8800', 'yellow': '#ffff00',
    'green': '#00ff00', 'blue': '#0000ff', 'purple': '#800080',
    'gray': '#444444', 'grey': '#444444', 'white': '#ffffff',
    'black': '#000000',
}


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
        values = ', '.join(sorted(expected))
        raise ValueError(f'Use exactly the requested colors: {values}.')

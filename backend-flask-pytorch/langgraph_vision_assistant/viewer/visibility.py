"""Build class and layer visibility commands from the current viewer state.

These functions return ordinary dictionaries. They do not run tools, mutate
the browser, or interpret sentences. Missing state is an error when an edit
needs to preserve an existing selection.
"""

from collections.abc import Sequence

from .checks import require_classes, require_masks
from .commands import LayersCommand, ViewerCommand, VisibleClassesCommand
from .state import ViewerContext

LAYER_NAMES = ('boxes', 'masks', 'labels')


def visible_classes(classes: list[str], context: ViewerContext) -> VisibleClassesCommand:
    """Replace the class selection after checking the detected class names."""
    require_classes(classes, context)
    return {'type': 'set_visible_classes', 'classes': classes}


def hide_classes(classes: list[str], context: ViewerContext) -> VisibleClassesCommand:
    """Remove selected classes, preserving both partial and empty selections."""
    plurals = {name + 's': name for name in context.available_classes}
    if 'person' in context.available_classes:
        plurals['people'] = 'person'
    classes = [plurals.get(name, name) for name in classes]
    require_classes(classes, context)
    current = context.view.require_filters().visible_classes
    if current is None:
        return {'type': 'set_visible_classes', 'classes': None}
    visible = current or context.available_classes
    remaining = [name for name in visible if name not in classes]
    return {'type': 'set_visible_classes', 'classes': remaining or None}


def hide_layers(layers: list[str], context: ViewerContext) -> LayersCommand:
    """Disable named layers while preserving every other visibility flag."""
    current = context.view.require_layers()
    return {'type': 'set_layers',
            'boxes': current.boxes.enabled and 'boxes' not in layers,
            'masks': current.masks.enabled and 'masks' not in layers,
            'labels': current.labels.enabled and 'labels' not in layers}


def build_hide_commands(targets: list[str], context: ViewerContext) -> list[ViewerCommand]:
    """Split explicit targets into layers and classes, then prepare their edits."""
    layers = [name for name in targets if name in LAYER_NAMES]
    classes = [name for name in targets if name not in LAYER_NAMES]
    commands: list[ViewerCommand] = []
    if layers:
        commands.append(hide_layers(layers, context))
    if classes:
        commands.append(hide_classes(classes, context))
    return commands


def restore_visibility(context: ViewerContext) -> list[ViewerCommand]:
    """Show all classes and supported layers without changing their appearance."""
    return [{'type': 'set_visible_classes', 'classes': []},
            {'type': 'set_layers', 'boxes': True, 'masks': context.page != 'boxes', 'labels': True}]


def set_layers(layers: Sequence[str] | None, opacity: float | None,
               context: ViewerContext) -> list[ViewerCommand]:
    """Replace visible layers and/or mask opacity, leaving omitted settings alone."""
    if (layers and 'masks' in layers) or opacity is not None:
        require_masks(context)
    if layers is None and opacity is None:
        raise ValueError('Provide layers or opacity to change.')
    commands: list[ViewerCommand] = []
    if layers is not None:
        commands.append({'type': 'set_layers', 'boxes': 'boxes' in layers,
                         'masks': 'masks' in layers, 'labels': 'labels' in layers})
    if opacity is not None:
        commands.append({'type': 'set_mask_opacity', 'value': opacity})
    return commands

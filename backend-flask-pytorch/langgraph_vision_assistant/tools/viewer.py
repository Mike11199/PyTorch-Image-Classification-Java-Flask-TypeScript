"""Define the actions Qwen can request for the current viewer.

The @tool decorator exposes each function's name, description, and arguments
to the model. Qwen selects a function and supplies arguments; LangGraph's
ToolNode executes it. tools/registry.py lists the functions available to both.

Each function validates its arguments and prepares browser edits. A single
set_layers call can produce visibility and opacity edits together. Edits reach
the browser only after results.py checks that the entire attempt succeeded.
"""

from langchain_core.tools import tool
from pydantic import StrictStr


from ..types import PreparedCommand, ViewerContext
from ..commands import ClassColorCommand, LayersCommand
from .checks import require_classes, require_masks
from .commands import prepared
from .colors import color_hex
from .inputs import Classes, ClassColor, ClassColors, Context, Fraction, Layers, Region, Seek, Selection, Target
from .inputs import ViewerLayers


@tool(response_format='content_and_artifact')
def set_visible_classes(classes: Classes, context: Context) -> PreparedCommand:
    """Filter object classes such as car or person. Never use for boxes, masks, or labels. Empty list shows all classes."""
    require_classes(classes, context)
    return prepared({'type': 'set_visible_classes', 'classes': classes})


@tool(response_format='content_and_artifact')
def set_class_colors(colors: ClassColors, context: Context) -> PreparedCommand:
    """Recolor one or more object classes together. Include every requested object. Omitted layers means all layers."""
    return prepared(*(class_color_command(change, context) for change in colors))


def class_color_command(change: ClassColor, context: ViewerContext) -> ClassColorCommand:
    """Validate one color change and translate its layers to the browser target."""
    require_classes([change.className], context)
    target: Target = 'both'
    if change.layers == ['boxes']:
        target = 'boxes'
    elif change.layers == ['masks']:
        require_masks(context)
        target = 'masks'
    if context['page'] == 'boxes':
        target = 'boxes'
    return {'type': 'set_class_color', 'className': change.className,
            'color': color_hex(change.color), 'target': target}


@tool(response_format='content_and_artifact')
def set_confidence(value: Fraction) -> PreparedCommand:
    """Set the minimum detection confidence from 0 to 1."""
    return prepared({'type': 'set_confidence', 'value': value})


@tool(response_format='content_and_artifact')
def set_layers(context: Context, layers: Layers | None = None,
               opacity: Fraction | None = None) -> PreparedCommand:
    """Change visible layers and/or mask opacity. Omit settings the user did not request. Full opacity is 1."""
    if (layers and 'masks' in layers) or opacity is not None:
        require_masks(context)
    if layers is None:
        if opacity is None:
            raise ValueError('Provide layers or opacity to change.')
        return prepared({'type': 'set_mask_opacity', 'value': opacity})
    visibility: LayersCommand = {'type': 'set_layers', 'boxes': 'boxes' in layers,
                  'masks': 'masks' in layers, 'labels': 'labels' in layers}
    if opacity is None:
        return prepared(visibility)
    return prepared(visibility, {'type': 'set_mask_opacity', 'value': opacity})


@tool(response_format='content_and_artifact')
def hide_layers(layers: Layers, context: Context) -> PreparedCommand:
    """Hide the named layers. Preserve the current visibility of every other layer."""
    current = ViewerLayers.model_validate(context['view'].get('layers'))
    return prepared({
        'type': 'set_layers',
        'boxes': current.boxes.enabled and 'boxes' not in layers,
        'masks': current.masks.enabled and 'masks' not in layers,
        'labels': current.labels.enabled and 'labels' not in layers,
    })


@tool(response_format='content_and_artifact')
def count_detections(classes: Classes, context: Context, region: Region = 'all') -> PreparedCommand:
    """Count visible detections of these classes. Default: the whole frame. Empty classes means all classes."""
    require_classes(classes, context)
    return prepared({'type': 'count_detections', 'classes': classes, 'region': region})


@tool(response_format='content_and_artifact')
def select_detection(className: StrictStr, mode: Selection, context: Context) -> PreparedCommand:
    """Ask the browser to highlight one detection of this class by position, size, or confidence."""
    require_classes([className], context)
    return prepared({'type': 'select_detection', 'className': className, 'mode': mode})


@tool(response_format='content_and_artifact')
def seek_detection(className: StrictStr, mode: Seek, context: Context) -> PreparedCommand:
    """Seek video playback: first occurrence, next occurrence, or peak (frame with the most detections)."""
    require_classes([className], context)
    if context['page'] != 'video':
        raise ValueError('Seeking is only available on the video page.')
    return prepared({'type': 'seek_detection', 'className': className, 'mode': mode})


@tool(response_format='content_and_artifact')
def reset_view(context: Context) -> PreparedCommand:
    """Reset viewer settings to their defaults."""
    return prepared({'type': 'reset_view'})

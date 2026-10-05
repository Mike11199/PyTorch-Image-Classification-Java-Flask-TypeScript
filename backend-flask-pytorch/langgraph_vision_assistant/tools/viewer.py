"""The functions Qwen can call, registered in tools/registry.py.

Each tool checks its arguments and returns a prepared browser command. It does
not edit viewer state or run arbitrary code. LangGraph executes these functions;
the browser applies their commands only after the whole batch succeeds.
"""

from langchain_core.tools import tool
from pydantic import StrictBool, StrictStr


from ..types import PreparedCommand, ViewerSnapshot
from .checks import require_classes, require_masks
from .commands import prepared
from .inputs import Classes, Color, Context, Fraction, Region, Seek, Selection, Target


@tool
def get_viewer_context(context: Context) -> ViewerSnapshot:
    """Read detected class names and current viewer settings. Does not inspect pixels or count objects."""
    return {'page': context['page'], 'availableClasses': context['availableClasses'], 'view': context['view']}


@tool(response_format='content_and_artifact')
def set_visible_classes(classes: Classes, context: Context) -> PreparedCommand:
    """Show only these detected classes. An empty list shows all classes."""
    require_classes(classes, context)
    return prepared({'type': 'set_visible_classes', 'classes': classes})


@tool(response_format='content_and_artifact')
def set_class_color(className: StrictStr, color: Color, context: Context,
                    target: Target | None = None) -> PreparedCommand:
    """Recolor a detected class. Omit target unless the user specifies boxes or masks."""
    require_classes([className], context)
    if target is None:
        target = 'boxes' if context['page'] == 'boxes' else 'both'
    if target != 'boxes':
        require_masks(context)
    return prepared({'type': 'set_class_color', 'className': className, 'color': color, 'target': target})


@tool(response_format='content_and_artifact')
def set_confidence(value: Fraction) -> PreparedCommand:
    """Set the minimum detection confidence from 0 to 1."""
    return prepared({'type': 'set_confidence', 'value': value})


@tool(response_format='content_and_artifact')
def set_mask_opacity(value: Fraction, context: Context) -> PreparedCommand:
    """Set mask opacity from 0 (transparent) to 1 (opaque). Requires masks."""
    require_masks(context)
    return prepared({'type': 'set_mask_opacity', 'value': value})


@tool(response_format='content_and_artifact')
def set_layers(boxes: StrictBool, masks: StrictBool, labels: StrictBool, context: Context) -> PreparedCommand:
    """Show or hide each layer. Preserve current settings for layers the user did not mention."""
    if masks:
        require_masks(context)
    return prepared({'type': 'set_layers', 'boxes': boxes, 'masks': masks, 'labels': labels})


@tool(response_format='content_and_artifact')
def count_detections(classes: Classes, region: Region, context: Context) -> PreparedCommand:
    """Ask the browser to count detections in a region. Empty classes means all. This tool does not return a count."""
    require_classes(classes, context)
    return prepared({'type': 'count_detections', 'classes': classes, 'region': region})


@tool(response_format='content_and_artifact')
def select_detection(className: StrictStr, mode: Selection, context: Context) -> PreparedCommand:
    """Ask the browser to highlight one detection of this class by position, size, or confidence."""
    require_classes([className], context)
    return prepared({'type': 'select_detection', 'className': className, 'mode': mode})


@tool(response_format='content_and_artifact')
def seek_detection(className: StrictStr, mode: Seek, context: Context) -> PreparedCommand:
    """Ask the video viewer to seek to the first, next, or peak occurrence of a detected class."""
    require_classes([className], context)
    if context['page'] != 'video':
        raise ValueError('Seeking is only available on the video page.')
    return prepared({'type': 'seek_detection', 'className': className, 'mode': mode})


@tool(response_format='content_and_artifact')
def reset_view(context: Context) -> PreparedCommand:
    """Reset viewer settings to their defaults."""
    return prepared({'type': 'reset_view'})

"""Expose viewer operations as tools Qwen can call.

Tool names, docstrings, and argument types form the model-facing interface.
Each wrapper delegates to plain rules in viewer/ and packages their commands
for LangGraph. registry.py supplies these tools to the model and ToolNode.
"""

from langchain_core.tools import tool
from pydantic import StrictStr

from ..agent.tool_results import PreparedCommand, prepared
from ..viewer import appearance, detections, visibility
from .inputs import Classes, ClassColors, Context, Fraction, Layers, Region, Seek, Selection


@tool(response_format='content_and_artifact')
def set_visible_classes(classes: Classes, context: Context) -> PreparedCommand:
    """Filter object classes such as car or person. Never use for boxes, masks, or labels. Empty list shows all classes."""
    return prepared(visibility.visible_classes(classes, context))


@tool(response_format='content_and_artifact')
def hide(targets: Classes, context: Context) -> PreparedCommand:
    """Hide named objects or layers. Targets are detected class names, boxes, masks, or labels."""
    return prepared(*visibility.build_hide_commands(targets, context))


@tool(response_format='content_and_artifact')
def restore_all_visibility(context: Context) -> PreparedCommand:
    """Restore both layers and classes for 'show all'. For categories only, use set_visible_classes instead."""
    return prepared(*visibility.restore_visibility(context))


@tool(response_format='content_and_artifact')
def set_class_colors(colors: ClassColors, context: Context) -> PreparedCommand:
    """Recolor one or more object classes together. Include every requested object. Omitted layers means all layers."""
    return prepared(*(appearance.class_color_command(change, context) for change in colors))


@tool(response_format='content_and_artifact')
def set_confidence(value: Fraction) -> PreparedCommand:
    """Set the minimum detection confidence from 0 to 1."""
    return prepared({'type': 'set_confidence', 'value': value})


@tool(response_format='content_and_artifact')
def set_layers(context: Context, layers: Layers | None = None,
               opacity: Fraction | None = None) -> PreparedCommand:
    """Change visible layers and/or mask opacity. Omit settings the user did not request. Full opacity is 1."""
    return prepared(*visibility.set_layers(layers, opacity, context))


@tool(response_format='content_and_artifact')
def count_detections(classes: Classes, context: Context, region: Region = 'all') -> PreparedCommand:
    """Count visible detections of these classes. Default: the whole frame. Empty classes means all classes."""
    return prepared(detections.count_detections(classes, region, context))


@tool(response_format='content_and_artifact')
def select_detection(className: StrictStr, mode: Selection, context: Context) -> PreparedCommand:
    """Ask the browser to highlight one detection of this class by position, size, or confidence."""
    return prepared(detections.select_detection(className, mode, context))


@tool(response_format='content_and_artifact')
def seek_detection(className: StrictStr, mode: Seek, context: Context) -> PreparedCommand:
    """Seek video playback: first occurrence, next occurrence, or peak (frame with the most detections)."""
    return prepared(detections.seek_detection(className, mode, context))


@tool(response_format='content_and_artifact')
def reset_view(context: Context) -> PreparedCommand:
    """Reset viewer settings to their defaults."""
    return prepared({'type': 'reset_view'})

"""List the tools exposed to Qwen and reject unexpected arguments.

This is the single place to register a new tool. viewer.py contains the actual
functions; graph.py gives this list to LangGraph's ToolNode.
"""

from pydantic import BaseModel
from .viewer import (
    get_viewer_context, set_visible_classes, set_class_color, set_confidence,
    set_mask_opacity, set_layers, count_detections, select_detection,
    seek_detection, reset_view,
)

VIEWER_TOOLS = [
    get_viewer_context, set_visible_classes, set_class_color, set_confidence,
    set_mask_opacity, set_layers, count_detections, select_detection, seek_detection, reset_view,
]

# LangChain's inferred models otherwise ignore misspelled/extra arguments.
for viewer_tool in VIEWER_TOOLS:
    schema = viewer_tool.get_input_schema()
    assert issubclass(schema, BaseModel)
    schema.model_config['extra'] = 'forbid'
    schema.model_rebuild(force=True)

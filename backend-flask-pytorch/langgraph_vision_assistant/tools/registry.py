"""Choose which tools Qwen may request and LangGraph may execute.

VIEWER_TOOLS contains the functions defined in viewer.py. model/client.py sends
their names, descriptions, and argument schemas to Qwen; agent/graph.py gives
the same list to ToolNode so it can execute the chosen calls.

The schema configuration below rejects unexpected arguments rather than silently
ignoring them. Add a new tool here after defining its function in viewer.py.
"""

from pydantic import BaseModel
from .viewer import (
    set_visible_classes, set_class_colors, set_confidence,
    set_layers, hide_layers, count_detections, select_detection,
    seek_detection, reset_view,
)

VIEWER_TOOLS = [
    set_visible_classes, set_class_colors, set_confidence,
    set_layers, hide_layers, count_detections, select_detection, seek_detection, reset_view,
]

# LangChain's inferred models otherwise ignore misspelled/extra arguments.
for viewer_tool in VIEWER_TOOLS:
    schema = viewer_tool.get_input_schema()
    assert issubclass(schema, BaseModel)
    schema.model_config['extra'] = 'forbid'
    schema.model_rebuild(force=True)

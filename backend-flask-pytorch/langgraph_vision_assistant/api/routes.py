"""HTTP entry point for the viewer assistant.

This file only connects HTTP input to the assistant service and formats success.
Read service.py next for request coordination, then agent/graph.py for LangGraph.
"""

import uuid

from flask import Blueprint, Response, g

from ..service import run_assistant
from .errors import register_error_handlers
from .request import read_request_context
from .responses import success

blueprint = Blueprint('langgraph_vision_assistant', __name__)
register_error_handlers(blueprint)


@blueprint.post('/api-pytorch/vision-assistant')
def ask_assistant() -> Response:
    """Read one request, call the service, and return commands for the browser."""
    request_id = g.assistant_request_id = uuid.uuid4().hex[:8]
    context = read_request_context()
    result = run_assistant(context, request_id)
    return success(result)

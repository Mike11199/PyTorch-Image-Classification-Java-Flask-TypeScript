"""Receive POST /api-pytorch/vision-assistant from the browser.

ask_assistant assigns a request ID, reads validated input through request.py,
and passes it to service.run_assistant. The returned edits or clarification
are formatted as JSON by responses.py.

Flask dispatches failures to the handlers in errors.py. Follow service.py next
to see how the request starts the LangGraph workflow.
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

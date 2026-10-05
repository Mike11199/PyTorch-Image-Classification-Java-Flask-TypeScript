"""Receive POST /api-pytorch/vision-assistant from the browser.

ask_assistant assigns a request ID, reads bounded JSON, validates its schema,
and passes it to service.run_assistant. errors.py formats responses and maps
exceptions to HTTP status codes.

Flask dispatches failures to the handlers in errors.py. Follow service.py next
to see how the request starts the LangGraph workflow.
"""

import json
import uuid

from flask import Blueprint, Response, g, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from ..service import run_assistant
from ..viewer.state import ViewerRequest
from .errors import json_response, register_error_handlers
from .schemas import AssistantRequest

MAX_REQUEST_BYTES = 16384

blueprint = Blueprint('langgraph_vision_assistant', __name__)
register_error_handlers(blueprint)


@blueprint.post('/api-pytorch/vision-assistant')
def ask_assistant() -> Response:
    """Read one request, call the service, and return commands for the browser."""
    request_id = g.assistant_request_id = uuid.uuid4().hex[:8]
    payload = read_request()
    result = run_assistant(payload, request_id)
    return json_response(result, 200)


def read_request() -> ViewerRequest:
    """Read bounded JSON and validate request fields before starting inference."""
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        raise RequestEntityTooLarge()
    raw = request.stream.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        raise RequestEntityTooLarge()
    try:
        return AssistantRequest.model_validate(json.loads(raw)).to_request()
    except (ValueError, TypeError, UnicodeError) as error:
        raise BadRequest() from error

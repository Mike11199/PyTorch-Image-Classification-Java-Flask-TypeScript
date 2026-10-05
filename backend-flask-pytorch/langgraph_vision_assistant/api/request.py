"""Read the browser's request body before starting the assistant.

routes.py calls read_request_context. We enforce the byte limit before parsing
JSON, then use AssistantRequest in schemas.py to validate and normalize its
fields. The result is a ViewerContext dictionary for service.py.

Oversized bodies become HTTP 413 errors; malformed JSON or invalid fields become
HTTP 400 errors. Keeping these checks here prevents invalid input reaching Qwen.
"""

import json

from flask import request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from ..types import ViewerContext
from .schemas import AssistantRequest

MAX_REQUEST_BYTES = 16384


def read_request_context() -> ViewerContext:
    """Read a bounded JSON body and translate validation failures into HTTP errors."""
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        raise RequestEntityTooLarge()
    raw = request.stream.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        raise RequestEntityTooLarge()
    try:
        return validate_request(json.loads(raw))
    except (ValueError, TypeError, UnicodeError) as error:
        raise BadRequest() from error



def validate_request(body: object) -> ViewerContext:
    """Validate JSON with the request schema and return graph input."""
    return AssistantRequest.model_validate(body).to_context()

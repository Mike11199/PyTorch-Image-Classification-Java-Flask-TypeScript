"""Turn successful results and failures into the frontend's JSON format.

Both paths attach the request ID and emit one terminal log event. This module
contains no workflow or error-classification logic; see errors.py for HTTP codes.
"""

from flask import Response, g, jsonify, make_response

from ..telemetry import log_event
from ..types import AssistantResult, ErrorResponse


def success(result: AssistantResult) -> Response:
    """Return a successful browser command batch or clarification."""
    return json_response(result, 200)


def failure(message: str, status: int) -> Response:
    """Return a user-facing error without exposing exception details."""
    return json_response({'error': message}, status)


def json_response(payload: AssistantResult | ErrorResponse, status: int) -> Response:
    """Log completion and attach the same correlation ID to the response."""
    request_id = g.assistant_request_id
    if status < 400:
        log_event('request_completed', request_id, status=status)
    else:
        log_event('request_failed', request_id, status=status, error=payload.get('error'))
    response = make_response(jsonify(payload), status)
    response.headers['X-Request-ID'] = request_id
    return response

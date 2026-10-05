"""Map failures during an assistant request to HTTP error responses.

routes.py registers these handlers on the assistant blueprint. Flask calls the
matching handler when request validation, the service, or inference raises an
exception. Each handler chooses a status and message; json_response adds the
same request ID and completion logging to successful and failed responses.

Expected failures tell the user whether to correct input or retry. Unexpected
failures are logged with details while the browser receives a generic message.
"""

from flask import Blueprint, Response, current_app, g, jsonify, make_response
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from ..agent.state import PlanError
from ..service import AssistantBusyError
from ..telemetry import log_event
from ..types import AssistantResult, ErrorResponse


def json_response(payload: AssistantResult | ErrorResponse, status: int) -> Response:
    """Log completion and attach the request ID to the JSON response."""
    request_id = g.assistant_request_id
    if status < 400:
        log_event('request_completed', request_id, status=status, timing=payload.get('timing'))
    else:
        log_event('request_failed', request_id, status=status, error=payload.get('error'))
    response = make_response(jsonify(payload), status)
    response.headers['X-Request-ID'] = request_id
    return response


def failure(message: str, status: int) -> Response:
    """Return a user-facing error without exposing exception details."""
    return json_response({'error': message}, status)


def invalid_request(error: BadRequest | ValidationError) -> Response:
    """Report malformed JSON or unsupported request fields."""
    return failure('Invalid request. Use a supported viewer and a message of 1–1,000 characters.', 400)


def request_too_large(error: RequestEntityTooLarge) -> Response:
    """Reject an oversized body before it reaches the model."""
    return failure('The assistant request is too large.', 413)


def assistant_busy(error: TimeoutError) -> Response:
    """Tell the caller to retry when a request slot or inference call times out."""
    if isinstance(error, AssistantBusyError):
        return failure(str(error), 429)
    return failure('A vision model is still running. Please try again when it finishes.', 429)


def model_unavailable(error: FileNotFoundError | ImportError) -> Response:
    """Explain that the local model or runtime is missing."""
    current_app.logger.exception('Vision assistant model unavailable')
    return failure('The assistant model is not installed. Rebuild the Flask container.', 503)


def invalid_tool_batch(error: PlanError) -> Response:
    """Report that the bounded repair loop could not produce valid commands."""
    return failure(str(error), 422)


def unexpected_failure(error: Exception) -> Response:
    """Log unexpected details locally while returning a generic failure."""
    current_app.logger.exception('Vision assistant failed')
    return failure('The assistant could not complete this request. Please try again.', 502)


def register_error_handlers(blueprint: Blueprint) -> None:
    """Attach this endpoint's exception mapping to its Flask blueprint."""
    blueprint.register_error_handler(BadRequest, invalid_request)
    blueprint.register_error_handler(ValidationError, invalid_request)
    blueprint.register_error_handler(RequestEntityTooLarge, request_too_large)
    blueprint.register_error_handler(TimeoutError, assistant_busy)
    blueprint.register_error_handler(FileNotFoundError, model_unavailable)
    blueprint.register_error_handler(ImportError, model_unavailable)
    blueprint.register_error_handler(PlanError, invalid_tool_batch)
    blueprint.register_error_handler(Exception, unexpected_failure)

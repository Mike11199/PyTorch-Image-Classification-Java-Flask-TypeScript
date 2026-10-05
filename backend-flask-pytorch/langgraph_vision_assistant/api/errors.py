"""Translate backend exceptions into stable, user-facing HTTP errors.

Flask calls these handlers when routes.py or service.py raises. Keeping this
mapping here lets the route show only the successful request path.
"""

from flask import Blueprint, Response, current_app
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from ..agent.state import PlanError
from ..service import AssistantBusyError
from .responses import failure


def invalid_request(error: BadRequest) -> Response:
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
    blueprint.register_error_handler(RequestEntityTooLarge, request_too_large)
    blueprint.register_error_handler(TimeoutError, assistant_busy)
    blueprint.register_error_handler(FileNotFoundError, model_unavailable)
    blueprint.register_error_handler(ImportError, model_unavailable)
    blueprint.register_error_handler(PlanError, invalid_tool_batch)
    blueprint.register_error_handler(Exception, unexpected_failure)

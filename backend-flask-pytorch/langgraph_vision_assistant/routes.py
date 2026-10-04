"""HTTP boundary for the local LangGraph vision assistant."""

import json
import threading
import uuid

from flask import Blueprint, current_app, jsonify, make_response, request

from .request import validate_request
from .telemetry import log_event
from .workflow import PlanError, WORKFLOW_RECURSION_LIMIT, build_workflow

MAX_REQUEST_BYTES = 16384

blueprint = Blueprint('langgraph_vision_assistant', __name__)
workflow = build_workflow()
# Bound pending LLM work as well as model memory. Other Gunicorn threads can serve status.
_request_slot = threading.BoundedSemaphore(1)


def _read_request_context():
    raw = request.stream.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        raise OverflowError
    return validate_request(json.loads(raw))


def _response(payload, status, request_id):
    event = 'request_completed' if status < 400 else 'request_failed'
    fields = {'status': status}
    if status >= 400:
        fields['error'] = payload['error']
    log_event(event, request_id, **fields)
    response = make_response(jsonify(payload), status)
    response.headers['X-Request-ID'] = request_id
    return response


def _failure(message, status, request_id):
    return _response({'error': message}, status, request_id)


def _invoke_workflow(context, request_id):
    state = {'context': context, 'request_id': request_id}
    return workflow.invoke(state, {'recursion_limit': WORKFLOW_RECURSION_LIMIT})['result']


def _run_workflow(context, request_id):
    try:
        return _response(_invoke_workflow(context, request_id), 200, request_id)
    except TimeoutError:
        return _failure(
            'A vision model is still running. Please try again when it finishes.',
            429, request_id,
        )
    except (FileNotFoundError, ImportError):
        current_app.logger.exception('Vision assistant model unavailable')
        return _failure(
            'The assistant model is not installed. Rebuild the Flask container.',
            503, request_id,
        )
    except PlanError as error:
        return _failure(str(error), 422, request_id)
    except Exception:
        current_app.logger.exception('Vision assistant failed')
        return _failure(
            'The assistant could not complete this request. Please try again.',
            502, request_id,
        )


@blueprint.post('/api-pytorch/vision-assistant')
def plan_actions():
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        return jsonify(error='The assistant request is too large.'), 413

    request_id = uuid.uuid4().hex[:8]
    try:
        context = _read_request_context()
    except OverflowError:
        return _failure('The assistant request is too large.', 413, request_id)
    except (ValueError, TypeError, UnicodeError):
        return _failure(
            'Invalid request. Use a supported viewer and a message of 1–1,000 characters.',
            400, request_id,
        )

    log_event(
        'request_started', request_id, page=context['page'],
        message=context['message'][:200],
        available_class_count=len(context['availableClasses']),
    )
    if not _request_slot.acquire(blocking=False):
        return _failure('The assistant is busy. Please try again shortly.', 429, request_id)

    try:
        return _run_workflow(context, request_id)
    finally:
        _request_slot.release()

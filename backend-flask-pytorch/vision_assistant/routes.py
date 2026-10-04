"""HTTP boundary; independent of the image and video route modules."""

import threading

from flask import Blueprint, current_app, jsonify, request

from .graph import PlanError, build_graph
from .model import generate_plan
from .schemas import validate_request

blueprint = Blueprint('vision_assistant', __name__)
graph = build_graph(generate_plan)
# Bound pending LLM work as well as model memory. Other Gunicorn threads can serve status.
_request_slot = threading.BoundedSemaphore(1)


@blueprint.post('/api-pytorch/vision-assistant')
def plan_actions():
    if request.content_length is not None and request.content_length > 16384:
        return jsonify(error='The assistant request is too large.'), 413
    raw = request.stream.read(16385)
    if len(raw) > 16384:
        return jsonify(error='The assistant request is too large.'), 413
    try:
        import json

        context = validate_request(json.loads(raw))
    except (ValueError, TypeError, UnicodeError):
        return jsonify(error='Invalid request. Use a supported viewer and a message of 1–1,000 characters.'), 400
    if not _request_slot.acquire(blocking=False):
        return jsonify(error='The assistant is busy. Please try again shortly.'), 429
    try:
        result = graph.invoke({'context': context}, {'recursion_limit': 8})['result']
        return jsonify(result)
    except TimeoutError:
        return jsonify(error='A vision model is still running. Please try again when it finishes.'), 429
    except (FileNotFoundError, ImportError):
        current_app.logger.exception('Vision assistant model unavailable')
        return jsonify(error='The assistant model is not installed. Rebuild the Flask container.'), 503
    except PlanError as error:
        return jsonify(error=str(error)), 422
    except Exception:
        current_app.logger.exception('Vision assistant failed')
        return jsonify(error='The assistant could not complete this request. Please try again.'), 502
    finally:
        _request_slot.release()

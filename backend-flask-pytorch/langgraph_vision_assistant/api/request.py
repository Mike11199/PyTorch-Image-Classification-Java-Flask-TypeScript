"""Read and validate HTTP input before the assistant service sees it.

read_request_context handles Flask/body limits. validate_request is a pure
validator that returns typed context or raises ValueError for invalid fields.
"""

import json
import re
from typing import cast, TypeGuard

from flask import request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from ..types import Page, ViewerContext

PAGES = {'boxes', 'mask', 'video'}
CATEGORY = re.compile(r'[a-z][a-z -]{0,39}')
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


def _valid_categories(categories: object) -> TypeGuard[list[str]]:
    """Accept only a bounded list of ordinary COCO-style class names."""
    if not isinstance(categories, list) or len(categories) > 80:
        return False
    for name in categories:
        if not isinstance(name, str) or not CATEGORY.fullmatch(name):
            return False
    return True


def validate_request(body: object) -> ViewerContext:
    """Validate untrusted JSON and return the normalized graph input.

    Raises ValueError for unsupported pages, oversized input, or malformed fields.
    """
    if not isinstance(body, dict):
        raise ValueError('A JSON object is required.')

    message = body.get('message')
    page = body.get('page')
    categories = body.get('availableClasses')
    view = body.get('view', {})

    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 1000:
        raise ValueError('Enter a request of 1 to 1,000 characters.')
    if not isinstance(page, str) or page not in PAGES:
        raise ValueError('Unknown viewer.')
    if not _valid_categories(categories):
        raise ValueError('Invalid detected categories.')
    if not isinstance(view, dict) or len(json.dumps(view, allow_nan=False)) > 3000:
        raise ValueError('Invalid viewer state.')
    return {
        'message': message.strip(),
        'page': cast(Page, page),
        'availableClasses': sorted(set(categories)),
        'view': view,
    }

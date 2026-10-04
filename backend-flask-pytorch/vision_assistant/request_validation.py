"""Validate the small amount of viewer context sent to the model."""

import json
import re

PAGES = {'boxes', 'mask', 'video'}
CATEGORY = re.compile(r'[a-z][a-z -]{0,39}')


def _valid_categories(categories):
    return (isinstance(categories, list) and len(categories) <= 80 and
            all(isinstance(name, str) and CATEGORY.fullmatch(name) for name in categories))


def validate_request(body):
    if not isinstance(body, dict):
        raise ValueError('A JSON object is required.')
    message = body.get('message')
    page = body.get('page')
    categories = body.get('availableClasses')
    view = body.get('view', {})
    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 1000:
        raise ValueError('Enter a request of 1 to 1,000 characters.')
    if page not in PAGES:
        raise ValueError('Unknown viewer.')
    if not _valid_categories(categories):
        raise ValueError('Invalid detected categories.')
    if not isinstance(view, dict) or len(json.dumps(view, allow_nan=False)) > 3000:
        raise ValueError('Invalid viewer state.')
    return {'message': message.strip(), 'page': page,
            'availableClasses': sorted(set(categories)), 'view': view}

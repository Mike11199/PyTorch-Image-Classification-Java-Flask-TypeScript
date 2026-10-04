"""Small, searchable log events for tracing one assistant request."""

import json
import logging

LOGGER = logging.getLogger('langgraph_vision_assistant')
LOGGER.setLevel(logging.INFO)


def log_event(event, request_id, **fields):
    details = ' '.join(
        f'{name}={json.dumps(value, separators=(",", ":"), sort_keys=True)}'
        for name, value in fields.items()
    )
    suffix = f' {details}' if details else ''
    LOGGER.info('request=%s event=%s%s', request_id, event, suffix)

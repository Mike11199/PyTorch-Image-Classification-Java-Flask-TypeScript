"""Small, searchable log events for tracing one assistant request."""

import json
import logging

LOGGER = logging.getLogger('langgraph_vision_assistant')
LOGGER.setLevel(logging.INFO)


def log_event(event: str, request_id: str, **fields: object) -> None:
    """Write compact fields with a request ID so model and HTTP events correlate."""
    parts = []
    for name, value in fields.items():
        encoded_value = json.dumps(value, separators=(',', ':'), sort_keys=True)
        parts.append(f'{name}={encoded_value}')
    details = ' '.join(parts)
    suffix = f' {details}' if details else ''
    LOGGER.info('request=%s event=%s%s', request_id, event, suffix)

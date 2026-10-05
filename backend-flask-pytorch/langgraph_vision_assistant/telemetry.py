"""Write consistent log events for an assistant request.

The route creates a request ID that the service, graph steps, and model client
pass to log_event. Events include that ID, a name, and JSON-encoded details such
as attempt counts, durations, or errors.

Searching logs for the request ID shows what happened across those modules.
The HTTP response exposes the same ID in its X-Request-ID header.
"""

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

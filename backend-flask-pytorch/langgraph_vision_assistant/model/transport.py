"""Authenticated HTTP communication with the private llama.cpp server.

This class owns the HTTP session only. runtime.py decides when a failed request
requires stopping the process. client.py converts chat messages for this API.
"""

from typing import Any
import requests


class ModelTransport:
    """Health and chat requests to one local server, without proxy inheritance."""

    def __init__(self, port: int, key: str) -> None:
        """Create a session authenticated with this process's temporary key."""
        self.url = f'http://127.0.0.1:{port}'
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers['Authorization'] = f'Bearer {key}'

    def is_ready(self) -> bool:
        """Return false while the server is loading or not yet listening."""
        try:
            return self.session.get(self.url + '/health', timeout=1).ok
        except (requests.ConnectionError, requests.Timeout):
            return False

    def complete(self, payload: dict[str, object]) -> dict[str, Any]:
        """Send one chat request and reject unsuccessful HTTP responses."""
        response = self.session.post(self.url + '/v1/chat/completions', json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Release HTTP connections; safe to call repeatedly."""
        self.session.close()

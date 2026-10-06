"""Communicate with the local model server over authenticated HTTP.

runtime.py creates one ModelTransport for its server's port and temporary API
key. The transport owns a requests session, checks server health, and sends chat
payloads built by client.py to the completion endpoint.

It returns the server's JSON or raises an HTTP/connection error. runtime.py
handles cleanup when inference stalls or disconnects; client.py converts a
successful JSON response into the message used by the graph.
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
        # CPU cold prompts can exceed two minutes on the production t3.medium.
        # Stay below Java's 300-second request deadline.
        response = self.session.post(self.url + '/v1/chat/completions', json=payload, timeout=(5, 240))
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Release HTTP connections; safe to call repeatedly."""
        self.session.close()

    def slot(self, action: str, filename: str) -> dict[str, Any]:
        """Save/restore private slot zero using the same loopback authentication."""
        response = self.session.post(
            self.url + '/slots/0', params={'action': action},
            json={'filename': filename}, timeout=(5, 15),
        )
        response.raise_for_status()
        return response.json()

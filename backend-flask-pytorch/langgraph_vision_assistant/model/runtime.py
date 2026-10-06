"""Keep the local model process and its HTTP connection alive together.

The shared model owner in the backend's runtime/model_runtime.py creates LocalModel
when a request needs Qwen. LocalModel reads settings, starts ModelServer, and
waits for readiness through ModelTransport before accepting chat requests.

Switching to a vision model closes both resources. Startup failures and stalled
or disconnected inference also trigger cleanup. server.py handles process
mechanics; transport.py handles HTTP; this file coordinates their lifetime.
"""

import atexit
from pathlib import Path
from typing import Any
import uuid
import requests
import logging

from .server import ModelServer, unused_loopback_port
from .settings import ModelSettings
from .transport import ModelTransport
from .prompt_cache import PromptCache


class LocalModel:
    """A ready-to-use local model whose resources are released together."""

    def __init__(self) -> None:
        """Load settings, start the private server, and wait for readiness."""
        settings = ModelSettings.from_environment()
        self.name = Path(settings.model_path).stem
        if not Path(settings.model_path).is_file():
            raise FileNotFoundError(settings.model_path)
        port, key = unused_loopback_port(), uuid.uuid4().hex
        self.transport = ModelTransport(port, key)
        self.server: ModelServer | None = None
        self.cache = None
        try:
            self.cache = PromptCache(settings)
        except OSError as error:
            logging.getLogger(__name__).warning('Prompt cache disabled: %s', error)
        try:
            self.server = ModelServer(settings, port, key, self.cache.directory if self.cache else None)
            self.server.wait_until_ready(self.transport.is_ready)
            if self.cache:
                self.cache.restore(self.transport)
        except Exception:
            self.close()
            raise
        atexit.register(self.close)

    def create_chat_completion(self, **payload: object) -> dict[str, Any]:
        """Run inference; discard a stalled or disconnected server before retry."""
        try:
            response = self.transport.complete({**payload, 'cache_prompt': True, 'id_slot': 0})
            if self.cache:
                self.cache.save(self.transport)
            return response
        except requests.Timeout as error:
            self.close()
            raise TimeoutError('Local inference timed out. Please try again.') from error
        except requests.ConnectionError:
            self.close()
            raise

    def is_alive(self) -> bool:
        """Let the shared owner replace a process that exited between requests."""
        return self.server is not None and self.server.is_alive()

    def close(self) -> None:
        """Release the process and HTTP session, including after failed startup."""
        atexit.unregister(self.close)
        try:
            if self.server is not None:
                self.server.close()
        finally:
            self.transport.close()

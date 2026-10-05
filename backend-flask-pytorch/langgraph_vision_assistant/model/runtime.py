"""Start and stop a private llama.cpp process under the shared model owner.

This owns process lifecycle only. Chat message conversion lives in client.py.
"""

import atexit
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from typing import Any
import uuid

import requests


def unused_loopback_port() -> int:
    """Let the OS choose a local port for this model instance."""
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


class LocalModel:
    """A lazy, CPU-only model process with an authenticated loopback chat API."""

    def __init__(self) -> None:
        """Start the configured GGUF and clean up if startup fails."""
        model_path = os.getenv('LLM_MODEL_PATH', '/opt/models/Qwen_Qwen3-0.6B-Q4_K_M.gguf')
        if not Path(model_path).is_file():
            raise FileNotFoundError(model_path)
        port = unused_loopback_port()
        self.url = f'http://127.0.0.1:{port}'
        self.client = requests.Session()
        self.client.trust_env = False
        key = uuid.uuid4().hex
        self.client.headers['Authorization'] = f'Bearer {key}'
        self.log = tempfile.TemporaryFile(mode='w+b')
        self.process: subprocess.Popen[bytes] | None = None
        try:
            self.process = self._launch(model_path, port, key)
            self._wait_until_ready()
        except Exception:
            self.close()
            raise
        atexit.register(self.close)

    def _launch(self, model_path: str, port: int, key: str) -> subprocess.Popen[bytes]:
        """Launch the pinned runtime with no public listener or model-side tools."""
        command = [
            os.getenv('LLM_SERVER_PATH', '/opt/llama/llama-server'),
            '--model', model_path, '--host', '127.0.0.1', '--port', str(port),
            '--api-key', key, '--jinja', '--parallel', '1',
            '--ctx-size', '8192', '--n-gpu-layers', '0',
            '--threads', os.getenv('LLM_THREADS', '1'),
            '--threads-batch', os.getenv('LLM_THREADS', '1'),
            '--reasoning-budget', '0', '--no-webui',
        ]
        return subprocess.Popen(
            command, stdout=self.log, stderr=self.log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )

    def _wait_until_ready(self) -> None:
        """Wait up to two minutes, reporting startup failures with runtime logs."""
        assert self.process is not None
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.log.seek(0)
                detail = self.log.read().decode('utf-8', errors='replace')[-2000:]
                raise RuntimeError(f'Local model failed to start: {detail}')
            try:
                if self.client.get(self.url + '/health', timeout=1).ok:
                    return
            except requests.ConnectionError:
                pass
            time.sleep(0.1)
        raise TimeoutError('Local model startup timed out.')

    def create_chat_completion(self, **payload: object) -> dict[str, Any]:
        """Call the local chat API; LangChain validates its message shape in client.py."""
        try:
            response = self.client.post(self.url + '/v1/chat/completions', json=payload, timeout=120)
        except requests.Timeout as error:
            self.close()
            raise TimeoutError('Local inference timed out. Please try again.') from error
        except requests.ConnectionError:
            self.close()
            raise
        response.raise_for_status()
        return response.json()

    def is_alive(self) -> bool:
        """Let the model owner replace a child that exited between requests."""
        return self.process is not None and self.process.poll() is None

    def close(self) -> None:
        """Release model memory and reap the process; safe to call more than once."""
        atexit.unregister(self.close)
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.client.close()
        self.log.close()

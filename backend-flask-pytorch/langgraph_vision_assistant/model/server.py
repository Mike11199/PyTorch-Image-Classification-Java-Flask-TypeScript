"""Start, monitor, and stop the llama.cpp process that runs Qwen.

runtime.py creates ModelServer with model settings, a local port, and a temporary
API key. This class launches the process, captures its logs, and waits for the
readiness check supplied by the HTTP transport.

If startup fails, the logs explain why. On shutdown, the process is terminated
and reaped, using a forced stop if needed. Chat requests and response conversion
belong to transport.py and client.py.
"""

from collections.abc import Callable
import os
import socket
import subprocess
import tempfile
import time

from .settings import ModelSettings


def unused_loopback_port() -> int:
    """Ask the operating system for an available local port."""
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


class ModelServer:
    """One private CPU inference process and its captured diagnostic log."""

    def __init__(self, settings: ModelSettings, port: int, key: str) -> None:
        """Launch the process, releasing the log if launching fails."""
        self.log = tempfile.TemporaryFile(mode='w+b')
        self.process: subprocess.Popen[bytes] | None = None
        try:
            self.process = self._launch(settings, port, key)
        except Exception:
            self.log.close()
            raise

    def _launch(self, settings: ModelSettings, port: int, key: str) -> subprocess.Popen[bytes]:
        """Launch the pinned runtime with no public listener or model-side tools."""
        command = [
            settings.server_path,
            '--model', settings.model_path, '--host', '127.0.0.1', '--port', str(port),
            '--api-key', key, '--jinja', '--parallel', '1',
            '--ctx-size', '8192', '--n-gpu-layers', '0',
            '--threads', settings.threads,
            '--threads-batch', settings.threads,
            '--reasoning-budget', '0', '--no-webui',
        ]
        return subprocess.Popen(
            command, stdout=self.log, stderr=self.log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )

    def wait_until_ready(self, is_ready: Callable[[], bool]) -> None:
        """Wait up to two minutes, reporting startup failures with runtime logs."""
        assert self.process is not None
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.log.seek(0)
                detail = self.log.read().decode('utf-8', errors='replace')[-2000:]
                raise RuntimeError(f'Local model failed to start: {detail}')
            if is_ready():
                return
            time.sleep(0.1)
        raise TimeoutError('Local model startup timed out.')

    def is_alive(self) -> bool:
        """Let the model owner replace a child that exited between requests."""
        return self.process is not None and self.process.poll() is None

    def close(self) -> None:
        """Release model memory and reap the process; safe to call more than once."""
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.log.close()

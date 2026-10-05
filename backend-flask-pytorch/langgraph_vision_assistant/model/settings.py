"""Read the configuration needed to start a local Qwen process.

runtime.py calls ModelSettings.from_environment before creating the server.
The resulting dataclass holds the model path, server executable, and CPU thread
count, using container defaults when environment overrides are absent.

server.py consumes these values when building the launch command. Keeping them
together makes configuration visible without searching through process code.
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ModelSettings:
    """Paths and CPU thread count used by one local model process."""

    model_path: str
    server_path: str
    threads: str

    @classmethod
    def from_environment(cls) -> 'ModelSettings':
        """Use container defaults unless the deployment supplies overrides."""
        return cls(
            model_path=os.getenv('LLM_MODEL_PATH', '/opt/models/Qwen_Qwen3-0.6B-Q4_K_M.gguf'),
            server_path=os.getenv('LLM_SERVER_PATH', '/opt/llama/llama-server'),
            threads=os.getenv('LLM_THREADS', '1'),
        )

"""Read local model configuration once, before starting llama.cpp."""

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

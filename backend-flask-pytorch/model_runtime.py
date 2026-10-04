"""One model owner shared by image, video, and viewer-assistant requests."""

import gc
import os
import threading
from contextlib import contextmanager

import torch

_lock = threading.Lock()
_model = None
_kind = None
torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))


@contextmanager
def model_session(kind, timeout=120):
    """Hold exclusive inference access, loading a model only when its kind changes."""
    global _model, _kind
    if kind not in {'boxes', 'mask', 'llm'}:
        raise ValueError('Unsupported model kind: ' + kind)
    if not _lock.acquire(timeout=timeout):
        raise TimeoutError("The model is busy. Please try again shortly.")
    try:
        if _kind != kind:
            if _kind == 'llm' and _model is not None:
                _model.close()
            _model = None
            _kind = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            if kind == "mask":
                from inference_mask import model_fn

                _model = model_fn().eval()
            elif kind == 'boxes':
                from inference import model_fn

                _model = model_fn(False).eval()
            else:
                from llama_cpp import Llama

                model_path = os.getenv('LLM_MODEL_PATH', '/opt/models/Qwen_Qwen3-0.6B-Q4_K_M.gguf')
                if not os.path.isfile(model_path):
                    raise FileNotFoundError(model_path)
                _model = Llama(
                    model_path=model_path, chat_format='chatml',
                    n_ctx=4096, n_threads=int(os.getenv('LLM_THREADS', '1')),
                    n_threads_batch=int(os.getenv('LLM_THREADS', '1')),
                    n_gpu_layers=0, verbose=False,
                )
            _kind = kind
        with torch.inference_mode():
            yield _model
    finally:
        _lock.release()

"""One model owner shared by image, video, and viewer-assistant requests."""

import gc
import os
import threading
from contextlib import contextmanager
from time import perf_counter

import torch

from langgraph_vision_assistant.telemetry import log_event

_lock = threading.Lock()
_model = None
_kind = None
torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))


@contextmanager
def model_session(kind, timeout=120, request_id=None):
    """Hold exclusive inference access, loading a model only when its kind changes."""
    global _model, _kind
    if kind not in {'boxes', 'mask', 'llm'}:
        raise ValueError('Unsupported model kind: ' + kind)
    trace_id = request_id or 'vision-inference'
    waiting_at = perf_counter()
    log_event('model_slot_waiting', trace_id, kind=kind)
    if not _lock.acquire(timeout=timeout):
        log_event('model_slot_timeout', trace_id, kind=kind, timeout_seconds=timeout)
        raise TimeoutError("The model is busy. Please try again shortly.")
    acquired_at = perf_counter()
    log_event(
        'model_slot_acquired', trace_id, kind=kind,
        wait_ms=round((acquired_at - waiting_at) * 1000),
    )
    try:
        if _kind != kind:
            previous_kind = _kind
            if _kind == 'llm' and _model is not None:
                _model.close()
            _model = None
            _kind = None
            if previous_kind is not None:
                log_event('model_unloaded', trace_id, kind=previous_kind)
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
            log_event('model_loaded', trace_id, kind=kind)
        with torch.inference_mode():
            yield _model
    finally:
        _lock.release()
        log_event(
            'model_slot_released', trace_id, kind=kind,
            held_ms=round((perf_counter() - acquired_at) * 1000),
        )

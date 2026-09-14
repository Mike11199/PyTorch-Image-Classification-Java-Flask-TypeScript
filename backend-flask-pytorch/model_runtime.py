"""One model owner shared by image requests and the video worker."""

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
def model_session(kind, timeout=5):
    """Hold exclusive inference access, loading a model only when its kind changes."""
    global _model, _kind
    if not _lock.acquire(timeout=timeout):
        raise TimeoutError("The model is busy. Please try again shortly.")
    try:
        if _kind != kind:
            _model = None
            _kind = None
            gc.collect()
            if kind == "mask":
                from inference_mask import model_fn

                _model = model_fn().eval()
            else:
                from inference import model_fn

                _model = model_fn(False).eval()
            _kind = kind
        with torch.inference_mode():
            yield _model
    finally:
        _lock.release()

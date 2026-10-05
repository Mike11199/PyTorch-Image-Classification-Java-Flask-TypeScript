"""One model process with threads for responsive status requests."""
workers = 1
worker_class = "gthread"
threads = 4
bind = "0.0.0.0:5000"
timeout = 180
graceful_timeout = 30


def post_worker_init(worker):
    """Report inference device availability before the first model is loaded."""
    import torch

    if torch.cuda.is_available():
        worker.log.info(
            "PyTorch inference device: CUDA (%s); torch=%s; CUDA build=%s. "
            "Models load on the first inference request.",
            torch.cuda.get_device_name(0), torch.__version__, torch.version.cuda,
        )
    else:
        worker.log.warning(
            "PyTorch inference device: CPU (CUDA unavailable); torch=%s; "
            "CUDA build=%s. Models load on the first inference request.",
            torch.__version__, torch.version.cuda or "none",
        )

"""Register the video API and its single background worker with Flask."""

import threading

from .api.routes import create_blueprint
from .storage.jobs import JobStore


def register_video_api(app, store=None):
    """Attach routes and start one worker for the configured store."""
    store = store if store is not None else JobStore()
    app.register_blueprint(create_blueprint(store))
    if store.worker_enabled:
        from .worker import run_worker

        threading.Thread(
            target=run_worker, args=(store,), daemon=True, name="video-worker"
        ).start()

"""Public entry point: register the assistant's HTTP endpoint with Flask.

Follow api/routes.py -> service.py -> agent/graph.py -> tools/viewer.py.
"""

from flask import Flask


def register_langgraph_vision_assistant(app: Flask) -> None:
    """Attach POST /api-pytorch/vision-assistant without loading the model."""
    from .api.routes import blueprint

    app.register_blueprint(blueprint)

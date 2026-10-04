"""Natural-language controls for the existing vision viewers."""


def register_vision_assistant(app):
    from .routes import blueprint

    app.register_blueprint(blueprint)

"""Create Flask and register the image, video, and assistant APIs.

Gunicorn loads app:app; python app.py starts local development. Endpoint code
lives in images/routes.py, video/api/, and langgraph_vision_assistant/api/.
"""

from flask import Flask
from flask_cors import CORS

from images.routes import blueprint as image_api
from video import register_video_api
from langgraph_vision_assistant import register_langgraph_vision_assistant

app = Flask(__name__)
CORS(app)
app.register_blueprint(image_api)
register_video_api(app)
register_langgraph_vision_assistant(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

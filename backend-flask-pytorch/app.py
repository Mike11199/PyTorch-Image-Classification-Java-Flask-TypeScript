from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from inference import model_fn, input_fn, predict_fn, output_fn
import json
import os
from io import BytesIO
import base64


app = Flask(__name__)
CORS(app)

# Allowed extensions (if you want to restrict the file types)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'model_dir'))
print(model_dir)
model = model_fn(model_dir)

@app.route('/api-pytorch/image-url-pytorch', methods=['POST'])
def predict():
    try:
        print('API Request received.')

        if 'image' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            image_data = file.read()
            input_tensor = input_fn(image_data)
            prediction = predict_fn(input_tensor, model)
            response = output_fn(prediction, 'application/json')
            print(jsonify(json.loads(response)))
            return jsonify(json.loads(response)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


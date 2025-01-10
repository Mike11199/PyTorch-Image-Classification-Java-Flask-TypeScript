from flask import Flask, request, jsonify
from flask_cors import CORS

import inference as inf
import inference_mask as inf_mask
import json

app = Flask(__name__)
CORS(app)

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            fast_rcnn_model = inf.model_fn(load_weights_from_checkpoint=False)
            input_tensor = inf.input_fn(image_data)
            prediction = inf.predict_fn(input_tensor, fast_rcnn_model)
            response = inf.output_fn(prediction)
            print(jsonify(json.loads(response)))
            return jsonify(json.loads(response)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api-pytorch/image-url-pytorch-mask', methods=['POST'])
def predict_mask():
    try:
        print('API Request received.')

        if 'image' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            image_data = file.read()
            mask_rcnn_model = inf_mask.model_fn()
            input_tensor = inf_mask.input_fn(image_data)
            prediction = inf_mask.predict_fn(input_tensor, mask_rcnn_model)
            response = inf_mask.output_fn(prediction, 'application/json')
            return jsonify(json.loads(response)), 200
    except Exception as e:
        print("error: " + str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


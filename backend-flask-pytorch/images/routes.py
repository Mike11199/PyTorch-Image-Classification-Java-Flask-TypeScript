"""Receive image uploads and return Faster R-CNN or Mask R-CNN predictions.

app.py registers this blueprint. Each route decodes the upload, reserves the
shared model session, and formats predictions with boxes.py or masks.py.
The endpoint URLs are unchanged by grouping these routes into the images package.
"""

import json
from flask import Blueprint, request, jsonify
from . import boxes as inf, masks as inf_mask
from runtime.model_runtime import model_session

blueprint = Blueprint('images', __name__)

# Allowed extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


# Helper function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@blueprint.route("/api-pytorch/image-url-pytorch", methods=["POST"])
def predict():
    try:
        print("API Request received.")

        if "image" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            image_data = file.read()
            input_tensor = inf.input_fn(image_data)
            with model_session("boxes") as fast_rcnn_model:
                prediction = inf.predict_fn(input_tensor, fast_rcnn_model)
                response = inf.output_fn(prediction)
            print(jsonify(json.loads(response)))
            return jsonify(json.loads(response)), 200
        return jsonify({"error": "Please upload a PNG or JPEG image."}), 400
    except TimeoutError as e:
        return jsonify({"error": str(e)}), 429
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route("/api-pytorch/image-url-pytorch-mask", methods=["POST"])
def predict_mask():
    try:
        print("API Request received.")

        if "image" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            image_data = file.read()
            input_tensor = inf_mask.input_fn(image_data)
            with model_session("mask") as mask_rcnn_model:
                prediction = inf_mask.predict_fn(input_tensor, mask_rcnn_model)
                response = inf_mask.output_fn(prediction)
            return jsonify(json.loads(response)), 200
        return jsonify({"error": "Please upload a PNG or JPEG image."}), 400
    except TimeoutError as e:
        return jsonify({"error": str(e)}), 429
    except Exception as e:
        print("error: " + str(e))
        return jsonify({"error": str(e)}), 500


from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import inference as inf
import inference_mask as inf_mask
import json
import os
from io import BytesIO
import base64
import requests


if __name__ == "__main__":
    import sys

    # download image
    image_url = "https://i.redd.it/v8z0crk5gho71.png"
    image_url_2 = "https://img.pikbest.com/wp/202345/dog-sitting-three-dogs-and-cats-in-front-of-a-dark-background_9581207.jpg!w700wp"
    response = requests.get(image_url)
    response.raise_for_status()
    image_bytes = response.content
    print(f"Downloaded {len(image_bytes)} bytes.")

    # Save it locally
    save_path = "downloaded_image.png"
    with open(save_path, "wb") as f:
        f.write(image_bytes)
    print(f"Image saved as: {save_path}")

    # load the model
    model = inf_mask.model_fn(".")

    # convert to input format
    data_for_inference = inf_mask.input_fn(image_bytes)

    # run prediction
    prediction_output = inf_mask.predict_fn(data_for_inference, model)

    # get final output
    final_response_json = inf_mask.output_fn(prediction_output, "application/json")

    print("JSON Response:")
    print(final_response_json)

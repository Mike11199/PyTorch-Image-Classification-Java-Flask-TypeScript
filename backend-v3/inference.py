import os
import torch
import io
import logging
import numpy as np
import cv2
import base64
from io import BytesIO
import json
from PIL import Image
from torchvision import transforms
from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2
import matplotlib.pyplot as plt


DEFAULT_MODEL_FILENAME = "fasterrcnn_resnet50_fpn.pth"

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

coco_names = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table',
    'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
    'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]


class ModelLoadError(Exception):
    pass

def model_fn(model_dir):
    """
    Loads a regular PyTorch model checkpoint for Faster R-CNN.
    Args:
        model_dir: a directory where the model is saved.
    Returns:
        A PyTorch model.
    """
    model_path = os.path.join(model_dir, "fasterrcnn_resnet50_fpn.pth")

    # Check if the model file exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    try:
        model = fasterrcnn_resnet50_fpn_v2(pretrained=True)
        state_dict = torch.load(model_path, map_location=torch.device("cpu"))
        model.load_state_dict(state_dict, strict=False)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)

        print("Michael - Model loaded successfully!")
        return model
    except RuntimeError as e:
        raise ModelLoadError(f"Failed to load model from {model_path}. Error: {e}")

def input_fn(input_data):
    """
    Args:
        input_data: the request payload serialized (binary image data)
    """
    logger.info("input_fn_start")
    image_array = np.frombuffer(input_data, np.uint8)

    # Decode the image using OpenCV
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # Convert the OpenCV image (BGR) to a PIL image (RGB)
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    # Normalize the image using transforms (convert to tensor)
    preprocess = transforms.Compose([transforms.ToTensor()])
    normalized = preprocess(image_pil)
    normalized_np = normalized.numpy()
    print("Normalized shape:", normalized_np.shape)

    logger.info("input_fn_end")
    return normalized_np

def predict_fn(data, model):
    """A default predict_fn for PyTorch. Calls a model on data deserialized in input_fn.
    Runs prediction on GPU if cuda is available.
    Args:
        data: input data (torch.Tensor) for prediction deserialized by input_fn
        model: PyTorch model loaded in memory by model_fn
    Returns: a prediction
    """
    logger.info("predict_fn_start")
    with torch.no_grad():
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = model.eval().to(device)
            targets = None
            data = torch.as_tensor(data, device=device)
            output = model([data], targets)

    logger.info("predict_fn_end")
    return output


def output_fn(prediction, accept):
    """A default output_fn for PyTorch. Serializes predictions from predict_fn to JSON, CSV or NPY format.
    Args:
        prediction: a prediction result from predict_fn
        accept: type which the output data needs to be serialized
    Returns: output data serialized
    """
    logger.info("output_fn_start")

    output_data =prediction[0]

    boxes = output_data.get("boxes", [])
    pred_scores = np.array(output_data.get("scores", []))
    pred_bboxes = np.array(output_data.get("boxes", []))

    print(pred_scores)

    detection_threshold = 0.9
    boxes = pred_bboxes[pred_scores >= detection_threshold].astype(np.int32)
    labels = np.array(output_data.get("labels", [])[:len(boxes)])
    pred_classes = [coco_names[i] for i in labels]

    logger.info(pred_scores)
    logger.info(boxes)
    logger.info(labels)
    logger.info(pred_classes)

    logger.info("Constructing JSON")

    response_data = {
        "scores": pred_scores.tolist(),
        "boxes": boxes.tolist(),
        "labels": labels.tolist(),
        "classes": pred_classes
    }

    logger.info(response_data)

    response_json = json.dumps(response_data)
    logger.info("output_fn_end")

    return response_json





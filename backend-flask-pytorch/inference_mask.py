import os
import torch
import logging
import numpy as np
import cv2
import json
from PIL import Image
from torchvision import transforms
from torchvision.models.detection import maskrcnn_resnet50_fpn_v2
import matplotlib.pyplot as plt
import base64
from io import BytesIO

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

def overlay_mask_manual(
    image_bgr: np.ndarray,
    mask_binary: np.ndarray,  # 0 or 1
    color_bgr: tuple,         # (B, G, R)
    alpha: float = 0.5
):
    """
    Manually alpha-blend `color_bgr` into `image_bgr` where `mask_binary == 1`.
    A fallback if OpenCV's addWeighted(...) doesn't allow `mask=` in your environment.
    """
    # Convert 0 or 1 mask to 0 or 255 (uint8)
    mask_255 = (mask_binary * 255).astype(np.uint8)
    # Coordinates of the pixels where mask=255
    coords = np.where(mask_255 == 255)

    # Original pixel values at those coords
    orig_vals = image_bgr[coords].astype(np.float32)

    # Overlay color repeated for each pixel
    overlay_vals = np.array(color_bgr, dtype=np.float32)
    overlay_vals = np.tile(overlay_vals, (orig_vals.shape[0], 1))

    # Blend
    blended = cv2.addWeighted(orig_vals, 1 - alpha, overlay_vals, alpha, 0)
    blended = blended.astype(np.uint8)

    # Put blended pixels back into original
    image_bgr[coords] = blended
    return image_bgr


def model_fn(model_dir):
    """
    Loads a Mask R-CNN model with pretrained COCO weights (ignoring any local .pth).
    """
    try:
        model = maskrcnn_resnet50_fpn_v2(pretrained=True)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        logger.info("Loaded Mask R-CNN model with default pretrained (COCO) weights.")
        return model
    except RuntimeError as e:
        raise ModelLoadError(f"Failed to load the pretrained Mask R-CNN model. Error: {e}")


def input_fn(input_data):
    """
    Returns a dict with:
      - 'tensor': the image as a NumPy array for inference
      - 'original_image': the original OpenCV BGR image for annotation
    """
    logger.info("input_fn_start")
    image_array = np.frombuffer(input_data, np.uint8)

    # Decode the image using OpenCV (BGR)
    image_cv2 = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image_cv2 is None:
        raise ValueError("Failed to decode image from input bytes.")

    # Convert the image to PIL (RGB) for torchvision transforms
    image_pil = Image.fromarray(cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB))

    # Normalize the image using transforms
    preprocess = transforms.Compose([transforms.ToTensor()])
    tensor = preprocess(image_pil)
    logger.info(f"Input image tensor shape: {tensor.shape}")
    logger.info("input_fn_end")

    return {
        "tensor": tensor.numpy(),      # for inference
        "original_image": image_cv2    # keep BGR image for drawing
    }


def predict_fn(data, model):
    logger.info("predict_fn_start")
    with torch.no_grad():
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.eval().to(device)

        input_tensor = torch.as_tensor(data["tensor"], device=device)
        output = model([input_tensor])  # run inference

    logger.info("predict_fn_end")

    # Return both the output and the original_image so we can draw in output_fn
    return {
        "predictions": output,
        "original_image": data["original_image"]
    }


def output_fn(prediction_dict, accept):
    logger.info("output_fn_start")

    predictions = prediction_dict["predictions"][0]   # single image
    original_image = prediction_dict["original_image"] # BGR

    boxes = predictions.get("boxes", [])
    scores = predictions.get("scores", [])
    labels = predictions.get("labels", [])
    masks = predictions.get("masks", [])  # shape: [N, 1, H, W]

    # Convert to CPU numpy
    if torch.is_tensor(boxes):
        boxes = boxes.detach().cpu().numpy()
    if torch.is_tensor(scores):
        scores = scores.detach().cpu().numpy()
    if torch.is_tensor(labels):
        labels = labels.detach().cpu().numpy()
    if torch.is_tensor(masks):
        masks = masks.detach().cpu().numpy()

    detection_threshold = 0.9
    idxs = np.where(scores >= detection_threshold)[0]

    boxes = boxes[idxs].astype(int)
    scores = scores[idxs]
    labels = labels[idxs]
    masks = masks[idxs]

    # Draw bounding boxes + label text on the original image
    for i, box in enumerate(boxes):
        cls_id = labels[i]
        class_name = coco_names[cls_id] if cls_id < len(coco_names) else f"ID_{cls_id}"
        score_val = scores[i]

        cv2.rectangle(
            original_image,
            (box[0], box[1]),
            (box[2], box[3]),
            color=(0, 255, 0),  # green
            thickness=2
        )
        cv2.putText(
            original_image,
            f"{class_name}: {score_val:.2f}",
            (box[0], box[1] - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            thickness=1
        )

    # Initialize list to hold all masks as arrays
    masks_array = []

    # Process each mask
    for i in range(len(boxes)):
        mask = masks[i, 0]  # shape: [H, W]
        mask_binary = (mask > 0.5).astype(int)  # 0 or 1

        # Optionally, resize mask to match image size if needed
        # mask_binary = cv2.resize(mask_binary, (original_image.shape[1], original_image.shape[0]), interpolation=cv2.INTER_NEAREST)

        # Convert mask to list for JSON serialization
        mask_list = mask_binary.tolist()
        masks_array.append(mask_list)

    # Save the final annotated image locally - debugging only
    # debug_save_path = "annotated_image_debug.jpg"
    # cv2.imwrite(debug_save_path, original_image)
    # logger.info(f"Annotated image saved to {debug_save_path}")

    # Convert the annotated image to Base64
    _, buffer = cv2.imencode(".jpg", original_image)
    image_bytes = buffer.tobytes()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    pred_classes = [coco_names[l] if l < len(coco_names) else f"ID_{l}" for l in labels]

    response_data = {
        "scores": scores.tolist(),
        "boxes": boxes.tolist(),
        "labels": labels.tolist(),
        "classes": pred_classes,
        "masks_array": masks_array  # Array of mask arrays
    }

    response_json = json.dumps(response_data)
    logger.info("output_fn_end")
    return response_json
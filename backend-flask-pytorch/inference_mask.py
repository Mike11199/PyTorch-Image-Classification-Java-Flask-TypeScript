import os
import uuid
from datetime import datetime
import torch
import logging
import numpy as np
import cv2
import json
from PIL import Image
from torchvision import transforms
from typing import Optional, Any, Dict, Tuple, List
from torchvision.models.detection import (
    maskrcnn_resnet50_fpn_v2,
    MaskRCNN_ResNet50_FPN_V2_Weights
)
from torchvision.models.detection.mask_rcnn import MaskRCNN

from coco_labels import coco_names


# set up logger as global variable
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ModelLoadError(Exception):
    pass


def model_fn() -> MaskRCNN:
    """
    Loads a Mask R-CNN model with pretrained COCO weights (ignoring any local .pth model).
    """
    try:
        weights = MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT
        model = maskrcnn_resnet50_fpn_v2(weights=weights)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        logger.info("Loaded Mask R-CNN model with default pretrained (COCO) weights.")
        return model
    except RuntimeError as e:
        raise ModelLoadError(f"Failed to load the pretrained Mask R-CNN model. Error: {e}")


def input_fn(input_data: bytes) -> Dict[str, np.ndarray]:
    """
    Decode and preprocess binary image data for inference and annotation.

    This function takes raw binary image data, decodes it into an OpenCV-compatible
    (BGR) image, converts it to a PIL image (RGB), then transforms it into a torch tensor
    for inference. It also provides the original BGR image for annotation or further
    processing.

    Note - might be possible to skip cv2 and convert directly to PIL but left this in.

    Returns a dict with:
      - 'tensor': the image as a NumPy array for inference
      - 'original_image': the original OpenCV BGR image for annotation
    """
    logger.info("input_fn_start")

    # Convert raw image bytes from uploaded image into a 1d numpy array of type uint8
    image_1d_np_array: np.ndarray  = np.frombuffer(buffer=input_data, dtype=np.uint8)

    # Decode the image using OpenCV (BGR) into a 3d numpy array
    image_cv2_3d_np_array: np.ndarray = decode_array_to_cv2_image(image_1d_np_array=image_1d_np_array)

    # Convert the image to a PIL (Python Imaging Library) Image (RGB) for torchvision transforms
    image_pil = Image.fromarray(cv2.cvtColor(src=image_cv2_3d_np_array, code=cv2.COLOR_BGR2RGB))

    # Converts PIL image to a normalized pytorch tensor using transforms for the model
    normalized_image_tensor: torch.Tensor = get_pytorch_tensor_from_pil_image(image_pil=image_pil)

    logger.info("input_fn_end")

    return {
        "tensor": normalized_image_tensor.numpy(),
        "original_image": image_cv2_3d_np_array
    }


def get_pytorch_tensor_from_pil_image(image_pil: Image) -> torch.Tensor:
    """
    Convert a PIL image into a PyTorch tensor using torchvision transforms.

    This function applies a simple transformation pipeline consisting of
    `transforms.ToTensor()`, which:
      - Converts a PIL image (or NumPy array) in the format (H, W, C)
        to a PyTorch tensor in the format (C, H, W).
      - Scales pixel values (0-255 for uin8) to the range [0, 1] to normalize them.

    Args:
        image_pil (PIL.Image.Image): The source image in PIL (RGB) format.

    Returns:
        torch.Tensor: A PyTorch tensor representation of the image,
            with shape (C, H, W) and dtype float32.

            e.g -
            [
                [   # Channel 0 (Blue)
                    [B1, B2, B3],
                    [B4, B5, B6]
                ],
                [   # Channel 1 (Green)
                    [G1, G2, G3],
                    [G4, G5, G6]
                ],
                [   # Channel 2 (Red)
                    [R1, R2, R3],
                    [R4, R5, R6]
                ]
            ]
    """
    preprocess = transforms.Compose(transforms=[transforms.ToTensor()])
    tensor = preprocess(image_pil)
    logger.info(f"Input image tensor shape: {tensor.shape}")
    return tensor


def decode_array_to_cv2_image(image_1d_np_array: np.ndarray) -> np.ndarray:
    """
    Decodes a 1D NumPy array of raw (compressed) image bytes into a 3D BGR (Blue, Green, Red)
    NumPy array.

    Uses OpenCV's `cv2.imdecode` to interpret the input as an image. If the
    decode operation fails (e.g., the bytes do not represent a valid image), a ValueError
    is raised.

    Args:
        image_1d_array (np.ndarray): A 1D NumPy array (dtype=np.uint8) containing
            raw, compressed image data (e.g., JPEG/PNG).

    Returns:
        np.ndarray: A 3D NumPy array (H, W, 3) in BGR color space on success.

        e.g- [
                [ [B1, G1, R1], [B2, G2, R2], [B3, G3, R3] ],
                [ [B4, G4, R4], [B5, G5, R5], [B6, G6, R6] ] ]
    """
    image_cv2: Optional[np.ndarray] = cv2.imdecode(buf=image_1d_np_array, flags=cv2.IMREAD_COLOR)
    if image_cv2 is None:
        raise ValueError("Failed to decode image from input bytes.")

    return image_cv2


def predict_fn(data: Dict[str, np.ndarray], model: MaskRCNN) -> Dict[str, Any]:
    """
    Run a forward pass of the PyTorch model on the input tensor and return predictions.

    This function takes a dictionary containing a preprocessed input tensor and the
    original image (BGR). It places the model in evaluation mode, transfers both the
    model and the tensor to the appropriate device (CUDA if available, otherwise CPU),
    then performs inference. The resulting predictions are returned along with the
    original image.

    Args:
        data (dict): A dictionary that must include:
            - "tensor": The input image as a NumPy array or PyTorch tensor suitable
              for inference (after any necessary preprocessing).
            - "original_image": The original OpenCV BGR image for later use
              (e.g., for annotation).
        model (torch.nn.Module): A PyTorch model ready for inference.

    Returns:
        dict[str, Any]: A dictionary containing:
            - "predictions": The model's output after running inference on the input tensor.
            - "original_image": The original BGR image from `data`.

    """
    logger.info("predict_fn_start")
    with torch.no_grad():
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.eval().to(device)

        input_tensor = torch.as_tensor(data=data["tensor"], device=device)

        # run inference on tensor with the pytorch model
        output = model([input_tensor])

    logger.info("predict_fn_end")

    # Return both the output and the original_image
    return {
        "predictions": output,
        "original_image": data["original_image"]
    }


def output_fn(prediction_dict: Dict[str, Any]) -> str:
    """
    Takes predictions from the model and returns a JSON object of scores, boxes, labels, classes, and masks.

    Predictions are filtered for only those above a certain accuracy.
    """
    logger.info("output_fn_start")
    original_image, boxes, scores, labels, masks = process_predictions(prediction_dict=prediction_dict)

    # array of a mask per object, each mask a binary array
    normalized_masks_array = create_normalized_mask_arrays(boxes, masks)

    # get each class name from label integers, e.g 18, from coco_names array or generic id_# if missing
    pred_classes_names = [coco_names[l] if l < len(coco_names) else f"ID_{l}" for l in labels]

    logger.info("scores: " + str(scores))
    logger.info("boxes: " + str(boxes))
    logger.info("labels: " + str(labels))
    logger.info("classes: " + str(pred_classes_names))

    # save image locally - uncomment to debug
    # save_original_image_locally_with_mask(original_image, boxes, scores, labels, masks)

    response_data = {
        "scores": scores.tolist(),             # [0.9984003]
        "boxes": boxes.tolist(),               # [[ 229   23 1192  791]]
        "labels": labels.tolist(),             # [18]
        "classes": pred_classes_names,         # ['dog']
        "masks_array": normalized_masks_array  # Array of 2D binary mask arrays for each detection
    }

    response_json = json.dumps(response_data)
    logger.info("output_fn_end")
    return response_json


def create_normalized_mask_arrays(boxes: np.ndarray, masks: np.ndarray) -> List[List[List[int]]]:
    """
    Converts mask predictions to binary arrays.

    Each mask prediction is an array containing confidence values between 0 and 1 (e.g., 0.53, 0.93)
    that indicate the likelihood of each pixel belonging to an object. This function converts those values
    to a binary array, where 1 indicates that the pixel is part of the object and 0 indicates that it is not.
    """
    masks_array = []

    # Process each mask
    for i in range(len(boxes)):
        mask = masks[i, 0]  # shape: [H, W]
        mask_binary = (mask > 0.5).astype(int)  # 0 or 1

        # Convert mask to list for JSON serialization
        mask_list = mask_binary.tolist()
        masks_array.append(mask_list)
    return masks_array


def process_predictions(prediction_dict: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Takes prediction results for a single image and converts them to CPU NumPy arrays if needed.

    This is because if the model was ran on a GPU, the predictions will be GPU tensors, which
    NumPy can't load.  If ran on a CPU, conversion is skipped.

    Args:
        prediction_dict (dict): A dictionary that should contain at least:
            - "predictions": a list where each element is a dictionary with keys:
            - "boxes": bounding boxes as a tensor or list.
            - "scores": confidence scores as a tensor or list.
            - "labels": detected class labels as a tensor or list.
            - "original_image": the original image (can be a NumPy array or any format).
            - "masks": segmentation masks as a tensor or list.  shape: [N, 1, H, W]
                e.g-
                [
                    [ for object 0
                        [[0.02, 0.9,  0.95, 0.1,  0.0],
                        [0.01, 0.0,  0.9,  0.88, 0.02],]
                    ],
                    [ for object 1
                        [ [0.0,  0.0,  0.01, 0.02, 0.8 ],
                        [0.2,  0.25, 0.3,  0.35, 0.9 ],
                        [0.01, 0.02, 0.0,  0.4,  0.6 ],]
                    ]
                ]

    Returns:
        tuple: (original_image, boxes, scores, labels, masks) where boxes, scores, labels,
               and masks are converted to NumPy arrays (if they were tensors).
    """

    # Get first prediction since the model processes one image only
    predictions = prediction_dict["predictions"][0]
    original_image = prediction_dict["original_image"]

    # Extract data from predictions (could be gpu tensor or lists)
    boxes = predictions.get("boxes", [])
    scores = predictions.get("scores", [])
    labels = predictions.get("labels", [])
    masks = predictions.get("masks", [])

    # Convert any GPU tensors to CPU NumPy arrays
    if torch.is_tensor(boxes):
        boxes = boxes.detach().cpu().numpy()
    if torch.is_tensor(scores):
        scores = scores.detach().cpu().numpy()
    if torch.is_tensor(labels):
        labels = labels.detach().cpu().numpy()
    if torch.is_tensor(masks):
        masks = masks.detach().cpu().numpy()

    filtered_boxes, filtered_scores, filtered_labels, filtered_masks = filter_detections(
        boxes=boxes, scores=scores, labels=labels, masks=masks, detection_threshold=0.9
    )

    return original_image, filtered_boxes, filtered_scores, filtered_labels, filtered_masks


def filter_detections( boxes: np.ndarray, scores: np.ndarray, labels: np.ndarray, masks: np.ndarray, detection_threshold: float = 0.9
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Filters detections based on a score threshold.  For example, only return bounding boxes, and masks
    if the model is 90% confident in that detection belongs to a specific type of object.
    """
    # Find indices where scores meet or exceed the threshold
    idxs = np.where(scores >= detection_threshold)[0]

    # Filter each array using the indices.  idxs is a list so this is slicing each array
    filtered_boxes = boxes[idxs].astype(int)
    filtered_scores = scores[idxs]
    filtered_labels = labels[idxs]
    filtered_masks = masks[idxs]

    return filtered_boxes, filtered_scores, filtered_labels, filtered_masks


def save_original_image_locally_with_mask(original_image: np.ndarray, boxes: np.ndarray, scores: np.ndarray, labels: np.ndarray, masks: np.ndarray) -> None:
    """
    Saves the image with masks and bounding boxes locally to the same directory where
    this file exists. To test a model locally or for debugging.
    """

    # iterate through each detection and draw labels/masks
    for i, (box, mask) in enumerate(zip(boxes, masks)):
        cls_id = labels[i]
        class_name = coco_names[cls_id] if cls_id < len(coco_names) else f"ID_{cls_id}"
        score_val = scores[i]

        np.random.seed(cls_id)
        color = tuple(np.random.randint(0, 256) for _ in range(3))  # Random RGB color

        # Draw bounding box and class label with accuracy score
        cv2.rectangle(original_image, (box[0], box[1]), (box[2], box[3]), color=color, thickness=2)
        cv2.putText(original_image, f"{class_name}: {score_val:.4f}", (box[0] + 5, box[1] + 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1)

        original_image = overlay_mask_manual(image_bgr=original_image, mask_binary=mask, color_bgr=color, alpha=0.5)

    # save image locally
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_str = f"{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:6]}"
    filename = f"annotated_image_{date_str}.jpg"
    debug_save_path = os.path.join(script_dir, filename)
    cv2.imwrite(debug_save_path, original_image)
    logger.info(f"Annotated image saved to {debug_save_path}")


def overlay_mask_manual(image_bgr: np.ndarray, mask_binary: np.ndarray, color_bgr: Tuple[int, int, int], alpha: float = 0.5) -> np.ndarray:
    """Takes an image and mask as numpy arrays and overlays the mask on to the image.  Returns combined numpy array"""
    mask = np.squeeze(mask_binary)
    mask_3ch = mask[..., None].astype('float32')
    overlay = np.full(image_bgr.shape, color_bgr, dtype='float32')
    img_float = image_bgr.astype('float32')
    blended = (1 - mask_3ch * alpha) * img_float + (mask_3ch * alpha) * overlay
    blended = np.clip(blended, 0, 255).astype(image_bgr.dtype)
    return blended
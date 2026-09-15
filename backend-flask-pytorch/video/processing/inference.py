"""Run Mask R-CNN and label each visible mask pixel with its detection ID."""

from contextlib import contextmanager

import cv2
import numpy as np
import torch

from coco_labels import coco_names
import model_runtime


@contextmanager
def model_frame_size(model, tensor):
    """Prevent internal upscaling while the caller holds the shared model lock."""
    transform = model.transform
    previous = transform.min_size, transform.max_size
    height, width = tensor.shape[-2:]
    transform.min_size = (min(height, width),)
    transform.max_size = max(height, width)
    try:
        yield
    finally:
        transform.min_size, transform.max_size = previous


def frame_tensor(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return torch.from_numpy(rgb.copy()).permute(2, 0, 1).float().div_(255)


def predict_frame(frame):
    """Keep at most twenty confident detections and release the shared model."""
    tensor = frame_tensor(frame)
    with model_runtime.model_session("mask", timeout=120) as model:
        with model_frame_size(model, tensor):
            prediction = model([tensor.to(next(model.parameters()).device)])[0]
        scores = prediction["scores"].cpu().numpy()
        keep = np.flatnonzero(scores >= 0.9)[:20]
        boxes = prediction["boxes"][keep].cpu().numpy()
        labels = prediction["labels"][keep].cpu().numpy()
        masks = prediction["masks"][keep, 0].cpu().numpy() >= 0.5
    return boxes, labels, scores[keep], masks


def index_masks(shape, prediction):
    """ID zero is transparent; ID n selects detections[n - 1]. Later masks win."""
    height, width = shape[:2]
    mask_ids = np.zeros((height, width), dtype=np.uint8)
    detections = []
    for detection_index, (box, label, score, mask) in enumerate(zip(*prediction), 1):
        color = [int(60 + (int(label) * factor) % 196) for factor in (67, 113, 157)]
        mask_ids[mask] = detection_index
        detections.append(
            {
                "box": box.tolist(),
                "label": coco_names[int(label)],
                "score": float(score),
                "color": color,
            }
        )
    return mask_ids, detections


def analyze_frame(frame):
    return index_masks(frame.shape, predict_frame(frame))

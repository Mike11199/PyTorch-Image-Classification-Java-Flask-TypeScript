"""Mask resolution choices; playback always keeps its original resolution."""

MASK_QUALITIES = {"fast": 320, "detailed": 640}
DEFAULT_MASK_QUALITY = "detailed"


def validate_mask_quality(value):
    if not isinstance(value, str) or value not in MASK_QUALITIES:
        raise ValueError("Choose Fast or Detailed mask quality.")
    return value


def job_mask_quality(job):
    """Keep older jobs at their original 640-pixel mask resolution."""
    return validate_mask_quality(job.get("maskQuality", "detailed"))


def model_frame_edge(job):
    return MASK_QUALITIES[job_mask_quality(job)]

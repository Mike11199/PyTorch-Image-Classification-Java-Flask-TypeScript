"""Download Torchvision model weights while building the container image."""

from torchvision.models.detection import (
    FasterRCNN_ResNet50_FPN_V2_Weights,
    MaskRCNN_ResNet50_FPN_V2_Weights,
)


def main() -> None:
    weights_to_cache = (
        FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT,
        MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT,
    )
    for weights in weights_to_cache:
        weights.get_state_dict(progress=True, check_hash=True)


if __name__ == "__main__":
    main()

"""ComfyUI node definitions."""

from __future__ import annotations

import importlib

import numpy as np
from PIL import Image

from .kcentroid import k_centroid_downscale


def _frame_to_pil(frame) -> Image.Image:
    array = frame.detach().cpu().numpy()
    if array.ndim != 3 or array.shape[-1] not in (1, 3, 4):
        raise ValueError(
            "IMAGE must have shape [batch, height, width, channels] with "
            "1, 3, or 4 channels"
        )

    array = np.clip(array * 255.0, 0, 255).astype(np.uint8)
    if array.shape[-1] == 1:
        array = array[..., 0]

    return Image.fromarray(array)


class KCentroidDownscale:
    """Downscale a ComfyUI IMAGE batch with the K-Centroid algorithm."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "width": (
                    "INT",
                    {"default": 128, "min": 1, "max": 16384, "step": 1},
                ),
                "height": (
                    "INT",
                    {"default": 128, "min": 1, "max": 16384, "step": 1},
                ),
                "centroids": (
                    "INT",
                    {"default": 2, "min": 1, "max": 256, "step": 1},
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "downscale"
    CATEGORY = "image/transform"
    DESCRIPTION = (
        "Downscales each image by clustering the colors in every source tile "
        "and choosing its dominant clustered color."
    )

    def downscale(self, image, width: int, height: int, centroids: int):
        if image.ndim != 4:
            raise ValueError(
                "IMAGE must have shape [batch, height, width, channels]"
            )
        if image.shape[0] < 1:
            raise ValueError("IMAGE batch must not be empty")

        frames = [
            np.asarray(
                k_centroid_downscale(
                    _frame_to_pil(frame),
                    width=width,
                    height=height,
                    centroids=centroids,
                ),
                dtype=np.uint8,
            )
            for frame in image
        ]

        torch = importlib.import_module("torch")
        output = torch.from_numpy(np.stack(frames)).to(dtype=torch.float32)
        return (output.div_(255.0),)

"""ComfyUI node definitions."""

from __future__ import annotations

import importlib

import numpy as np
from PIL import Image

from .kcentroid import (
    k_centroid_downscale,
    k_centroid_downscale_channel,
)


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
            },
            "optional": {
                "mask": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "downscale"
    CATEGORY = "image/transform"
    DESCRIPTION = (
        "Downscales each image by clustering the colors in every source tile "
        "and choosing its dominant clustered color. Embedded RGBA alpha or "
        "an optional ComfyUI MASK is downscaled with the same method."
    )

    def downscale(
        self,
        image,
        width: int,
        height: int,
        centroids: int,
        mask=None,
    ):
        if image.ndim != 4:
            raise ValueError(
                "IMAGE must have shape [batch, height, width, channels]"
            )
        if image.shape[0] < 1:
            raise ValueError("IMAGE batch must not be empty")

        downscaled_images = [
            k_centroid_downscale(
                _frame_to_pil(frame),
                width=width,
                height=height,
                centroids=centroids,
            )
            for frame in image
        ]
        frames = [
            np.asarray(frame, dtype=np.uint8)
            for frame in downscaled_images
        ]

        if mask is not None:
            mask_frames = self._downscale_mask(
                mask=mask,
                image_batch=int(image.shape[0]),
                source_width=int(image.shape[2]),
                source_height=int(image.shape[1]),
                width=width,
                height=height,
                centroids=centroids,
            )
        else:
            mask_frames = []
            for frame in downscaled_images:
                if "A" in frame.getbands():
                    alpha = np.asarray(
                        frame.getchannel("A"),
                        dtype=np.float32,
                    )
                    mask_frames.append(1.0 - (alpha / 255.0))
                else:
                    mask_frames.append(
                        np.zeros((height, width), dtype=np.float32)
                    )

        torch = importlib.import_module("torch")
        output = torch.from_numpy(np.stack(frames)).to(dtype=torch.float32)
        output_mask = torch.from_numpy(np.stack(mask_frames)).to(
            dtype=torch.float32
        )
        return (output.div_(255.0), output_mask)

    @staticmethod
    def _downscale_mask(
        mask,
        image_batch: int,
        source_width: int,
        source_height: int,
        width: int,
        height: int,
        centroids: int,
    ):
        array = mask.detach().cpu().numpy()
        if array.ndim == 2:
            array = array[None, ...]
        if array.ndim != 3:
            raise ValueError("MASK must have shape [batch, height, width]")
        if array.shape[1:] != (source_height, source_width):
            raise ValueError(
                "MASK dimensions must match IMAGE dimensions: expected "
                f"{source_width}x{source_height}, got "
                f"{array.shape[2]}x{array.shape[1]}"
            )
        if array.shape[0] == 1 and image_batch > 1:
            array = np.repeat(array, image_batch, axis=0)
        elif array.shape[0] != image_batch:
            raise ValueError(
                "MASK batch size must be 1 or match the IMAGE batch size"
            )

        downscaled_masks = []
        for frame in array:
            transparency = np.clip(frame, 0.0, 1.0)
            alpha = Image.fromarray(
                ((1.0 - transparency) * 255.0).astype(np.uint8)
            )
            downscaled_alpha = k_centroid_downscale_channel(
                alpha,
                width=width,
                height=height,
                centroids=centroids,
            )
            downscaled_masks.append(
                1.0
                - (
                    np.asarray(downscaled_alpha, dtype=np.float32)
                    / 255.0
                )
            )

        return downscaled_masks

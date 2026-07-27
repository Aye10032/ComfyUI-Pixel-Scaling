"""K-Centroid image downscaling.

The algorithm is adapted from Astropulse/pixeldetector's k-centroid-only
branch, which is distributed under the MIT License.
"""

from __future__ import annotations

from itertools import product

import numpy as np
from PIL import Image


def _validate_parameters(
    image: Image.Image,
    width: int,
    height: int,
    centroids: int,
) -> None:
    if width < 1 or height < 1:
        raise ValueError("width and height must both be at least 1")
    if centroids < 1 or centroids > 256:
        raise ValueError("centroids must be between 1 and 256")
    if width > image.width or height > image.height:
        raise ValueError(
            "K-Centroid is a downscaling algorithm: the requested size "
            f"{width}x{height} exceeds the input size "
            f"{image.width}x{image.height}"
        )


def k_centroid_downscale(
    image: Image.Image,
    width: int,
    height: int,
    centroids: int = 2,
) -> Image.Image:
    """Downscale ``image`` by selecting a clustered dominant color per tile.

    Each output pixel represents one rectangular tile in the input. Pillow
    quantizes that tile into ``centroids`` color clusters using the same
    settings as the upstream implementation; the most frequent clustered
    color becomes the output pixel.
    """

    _validate_parameters(image, width, height, centroids)
    image = image.convert("RGB")

    downscaled = np.empty((height, width, 3), dtype=np.uint8)
    width_factor = image.width / width
    height_factor = image.height / height

    for x, y in product(range(width), range(height)):
        tile = image.crop(
            (
                x * width_factor,
                y * height_factor,
                (x * width_factor) + width_factor,
                (y * height_factor) + height_factor,
            )
        )
        quantized = tile.quantize(
            colors=centroids,
            method=1,
            kmeans=centroids,
        ).convert("RGB")
        color_counts = quantized.getcolors()
        if not color_counts:
            raise RuntimeError("K-Centroid could not determine a tile color")

        downscaled[y, x] = max(color_counts, key=lambda item: item[0])[1]

    return Image.fromarray(downscaled)

from itertools import product

import numpy as np
import pytest
from PIL import Image

from kcentroid import k_centroid_downscale


def _upstream_reference(image, width, height, centroids):
    image = image.convert("RGB")
    downscaled = np.zeros((height, width, 3), dtype=np.uint8)
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
        tile = tile.quantize(
            colors=centroids,
            method=1,
            kmeans=centroids,
        ).convert("RGB")
        color_counts = tile.getcolors()
        downscaled[y, x] = max(color_counts, key=lambda item: item[0])[1]

    return downscaled


def test_downscales_solid_tiles_to_their_colors():
    pixels = np.zeros((4, 4, 3), dtype=np.uint8)
    pixels[:2, :2] = (255, 0, 0)
    pixels[:2, 2:] = (0, 255, 0)
    pixels[2:, :2] = (0, 0, 255)
    pixels[2:, 2:] = (255, 255, 0)

    output = k_centroid_downscale(
        Image.fromarray(pixels),
        width=2,
        height=2,
        centroids=2,
    )

    np.testing.assert_array_equal(
        np.asarray(output),
        np.array(
            [
                [[255, 0, 0], [0, 255, 0]],
                [[0, 0, 255], [255, 255, 0]],
            ],
            dtype=np.uint8,
        ),
    )


def test_converts_input_to_rgb():
    image = Image.new("L", (4, 4), color=127)

    output = k_centroid_downscale(image, width=2, height=2)

    assert output.mode == "RGB"
    assert output.size == (2, 2)


def test_matches_upstream_algorithm_for_non_uniform_tiles():
    random = np.random.default_rng(42)
    pixels = random.integers(0, 256, (23, 31, 3), dtype=np.uint8)
    image = Image.fromarray(pixels)

    output = k_centroid_downscale(
        image,
        width=9,
        height=7,
        centroids=3,
    )

    np.testing.assert_array_equal(
        np.asarray(output),
        _upstream_reference(image, width=9, height=7, centroids=3),
    )


@pytest.mark.parametrize(
    ("width", "height", "centroids"),
    [
        (0, 1, 2),
        (1, 0, 2),
        (1, 1, 0),
        (1, 1, 257),
    ],
)
def test_rejects_invalid_parameters(width, height, centroids):
    with pytest.raises(ValueError):
        k_centroid_downscale(
            Image.new("RGB", (4, 4)),
            width=width,
            height=height,
            centroids=centroids,
        )


def test_rejects_upscaling():
    with pytest.raises(ValueError, match="downscaling algorithm"):
        k_centroid_downscale(
            Image.new("RGB", (4, 4)),
            width=5,
            height=4,
        )

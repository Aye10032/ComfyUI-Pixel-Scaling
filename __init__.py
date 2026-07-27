from .nodes import KCentroidDownscale

NODE_CLASS_MAPPINGS = {
    "KCentroidDownscale": KCentroidDownscale,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KCentroidDownscale": "K-Centroid Downscale",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

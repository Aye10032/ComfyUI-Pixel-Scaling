import importlib.util
import sys
from pathlib import Path


def test_comfyui_node_registration():
    root = Path(__file__).resolve().parents[1]
    package_name = "comfyui_pixel_scaling_test"
    spec = importlib.util.spec_from_file_location(
        package_name,
        root / "__init__.py",
        submodule_search_locations=[str(root)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module

    try:
        spec.loader.exec_module(module)
        node = module.NODE_CLASS_MAPPINGS["KCentroidDownscale"]

        assert (
            module.NODE_DISPLAY_NAME_MAPPINGS["KCentroidDownscale"]
            == "K-Centroid Downscale"
        )
        assert node.RETURN_TYPES == ("IMAGE",)
        assert node.FUNCTION == "downscale"
    finally:
        for name in tuple(sys.modules):
            if name == package_name or name.startswith(f"{package_name}."):
                del sys.modules[name]

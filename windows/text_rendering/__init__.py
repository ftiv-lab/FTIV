"""Text rendering submodules for phase-wise structural decomposition."""

from .adapter import RendererInputAdapter, adapt_renderer_input
from .layout import calculate_shadow_padding, get_blur_radius_px

__all__ = [
    "RendererInputAdapter",
    "adapt_renderer_input",
    "calculate_shadow_padding",
    "get_blur_radius_px",
]

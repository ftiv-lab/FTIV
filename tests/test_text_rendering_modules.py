from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from windows.text_rendering.adapter import RendererInputAdapter, adapt_renderer_input
from windows.text_rendering.layout import calculate_shadow_padding, get_blur_radius_px


@dataclass
class _DummyPoint:
    x: int = 0
    y: int = 0


class _ValidRendererSource:
    def __init__(self) -> None:
        self.is_vertical = False
        self.font_family = "Arial"
        self.font_size = 24
        self.text = "hello"
        self.geometry: Any = None
        self.extra = "value"

    def pos(self) -> _DummyPoint:
        return _DummyPoint(1, 2)

    def setGeometry(self, rect: Any) -> None:
        self.geometry = rect


def test_renderer_input_adapter_proxies_getattr_and_setattr() -> None:
    src = _ValidRendererSource()
    adapter = RendererInputAdapter(src)

    assert adapter.extra == "value"
    adapter.extra = "updated"
    assert src.extra == "updated"


def test_renderer_input_adapter_proxies_pos_and_set_geometry() -> None:
    src = _ValidRendererSource()
    adapter = RendererInputAdapter(src)

    point = adapter.pos()
    assert (point.x, point.y) == (1, 2)

    adapter.setGeometry((0, 0, 100, 50))
    assert src.geometry == (0, 0, 100, 50)


def test_renderer_input_adapter_rejects_missing_core_attrs() -> None:
    class _MissingText(_ValidRendererSource):
        def __init__(self) -> None:
            super().__init__()
            del self.text

    with pytest.raises(AttributeError):
        RendererInputAdapter(_MissingText())


def test_renderer_input_adapter_rejects_non_callable_pos() -> None:
    class _BadPos(_ValidRendererSource):
        pos = "not-callable"

    with pytest.raises(TypeError):
        RendererInputAdapter(_BadPos())


def test_renderer_input_adapter_rejects_non_callable_set_geometry() -> None:
    class _BadSetGeometry(_ValidRendererSource):
        setGeometry = "not-callable"

    with pytest.raises(TypeError):
        RendererInputAdapter(_BadSetGeometry())


def test_adapt_renderer_input_returns_existing_adapter() -> None:
    src = _ValidRendererSource()
    adapter = RendererInputAdapter(src)
    assert adapt_renderer_input(adapter) is adapter


def test_get_blur_radius_px_uses_shadow_enabled_flag() -> None:
    assert get_blur_radius_px(shadow_enabled=False, shadow_blur=99) == 0.0
    assert get_blur_radius_px(shadow_enabled=True, shadow_blur=50) == 10.0


def test_calculate_shadow_padding_disabled_returns_zero_padding() -> None:
    assert calculate_shadow_padding(
        font_size=40,
        shadow_enabled=False,
        shadow_offset_x=0.5,
        shadow_offset_y=-0.5,
        shadow_blur=30,
    ) == (0, 0, 0, 0)


def test_calculate_shadow_padding_positive_offsets() -> None:
    # font_size=10, offset=(0.5, 0.2), blur=10 -> blur_px=2
    # sx=5, sy=2 => left/top=0, right=7, bottom=4
    assert calculate_shadow_padding(
        font_size=10,
        shadow_enabled=True,
        shadow_offset_x=0.5,
        shadow_offset_y=0.2,
        shadow_blur=10,
    ) == (0, 0, 7, 4)


def test_calculate_shadow_padding_negative_offsets() -> None:
    # font_size=10, offset=(-0.5, -0.2), blur=10 -> blur_px=2
    # sx=-5, sy=-2 => left=7, top=4, right=0, bottom=0
    assert calculate_shadow_padding(
        font_size=10,
        shadow_enabled=True,
        shadow_offset_x=-0.5,
        shadow_offset_y=-0.2,
        shadow_blur=10,
    ) == (7, 4, 0, 0)

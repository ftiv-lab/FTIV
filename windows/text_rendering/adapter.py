from typing import Any

from models.protocols import RendererInput


class RendererInputAdapter:
    """RendererInput を満たす入力を正規化する互換アダプタ。"""

    _CORE_ATTRS: tuple[str, ...] = ("is_vertical", "font_family", "font_size", "text")

    def __init__(self, source: RendererInput) -> None:
        object.__setattr__(self, "_source", source)
        self._validate_source()

    def _validate_source(self) -> None:
        source: RendererInput = object.__getattribute__(self, "_source")
        missing: list[str] = [name for name in self._CORE_ATTRS if not hasattr(source, name)]
        if missing:
            raise AttributeError(f"RendererInput missing required attrs: {', '.join(missing)}")
        if not callable(getattr(source, "pos", None)):
            raise TypeError("RendererInput requires callable pos()")
        if not callable(getattr(source, "setGeometry", None)):
            raise TypeError("RendererInput requires callable setGeometry(...)")

    def pos(self) -> Any:
        source: RendererInput = object.__getattribute__(self, "_source")
        return source.pos()

    def setGeometry(self, rect: Any) -> None:
        source: RendererInput = object.__getattribute__(self, "_source")
        source.setGeometry(rect)

    def __getattr__(self, name: str) -> Any:
        source: RendererInput = object.__getattribute__(self, "_source")
        return getattr(source, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_source":
            object.__setattr__(self, name, value)
            return
        source: RendererInput = object.__getattribute__(self, "_source")
        setattr(source, name, value)


def adapt_renderer_input(window: RendererInput) -> RendererInputAdapter:
    if isinstance(window, RendererInputAdapter):
        return window
    return RendererInputAdapter(window)

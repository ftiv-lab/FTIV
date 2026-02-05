from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class UndoableConfigurable(Protocol):
    """
    Protocol for objects that support undoable property changes.
    Matches BaseOverlayWindow.set_undoable_property signature.
    """

    def set_undoable_property(
        self, property_name: str, new_value: Any, update_method_name: Optional[str] = None
    ) -> None: ...


@runtime_checkable
class TextConfigurable(UndoableConfigurable, Protocol):
    """
    Protocol for TextWindow objects explicitly supporting text-specific features.
    """

    def update_text(self) -> None: ...


@runtime_checkable
class ImageConfigurable(UndoableConfigurable, Protocol):
    """
    Protocol for ImageWindow objects.
    """

    def update_image(self) -> None: ...

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


@runtime_checkable
class NoteMetadataEditableTarget(Protocol):
    """
    Minimal contract for note metadata operations used by PropertyPanel.
    This contract intentionally excludes rendering/UI concerns.
    """

    def set_title_and_tags(self, title: str, tags: list[str]) -> None: ...

    def set_starred(self, value: bool) -> None: ...

    def set_due_at(self, value: str) -> None: ...

    def clear_due_at(self) -> None: ...

    def set_archived(self, value: bool) -> None: ...


@runtime_checkable
class RendererInput(Protocol):
    """
    Minimal renderer boundary contract (Phase 9B Step 3, first stage).

    Notes:
    - TextRenderer still reads many dynamic attributes for backward compatibility.
    - Core fields are validated by adapter-side checks in TextRenderer.
    """

    def pos(self) -> Any: ...

    def setGeometry(self, rect: Any) -> None: ...

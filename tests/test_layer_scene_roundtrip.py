from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QPoint

from managers.file_manager import FileManager


class _DummyWindow:
    def __init__(
        self,
        uuid: str,
        x: int,
        y: int,
        *,
        layer_order: int | None = None,
        layer_offset: dict[str, int] | None = None,
    ) -> None:
        self.uuid = uuid
        self.parent_window_uuid = None
        self.child_windows: list[_DummyWindow] = []
        self._pos = QPoint(x, y)
        self.config = SimpleNamespace(
            layer_order=layer_order,
            layer_offset=layer_offset,
            position={"x": x, "y": y},
        )

    def pos(self) -> QPoint:
        return QPoint(self._pos)

    def move(self, pos: QPoint) -> None:
        self._pos = QPoint(pos)

    def add_child_window(self, child: "_DummyWindow") -> None:
        child.parent_window_uuid = self.uuid
        if child not in self.child_windows:
            self.child_windows.append(child)


class _DummyWindowManager:
    def __init__(self) -> None:
        self.text_windows: list[_DummyWindow] = []
        self.image_windows: list[_DummyWindow] = []
        self.connectors: list = []


class _DummyMainWindow:
    def __init__(self) -> None:
        self.window_manager = _DummyWindowManager()
        self.json_directory = "."


def _build_file_manager() -> tuple[FileManager, _DummyMainWindow]:
    main_window = _DummyMainWindow()
    file_manager = FileManager(main_window)

    def _create_text_window_from_data(data: dict) -> _DummyWindow:
        pos = data.get("position", {}) if isinstance(data.get("position"), dict) else {}
        window = _DummyWindow(
            str(data.get("uuid", "")),
            int(pos.get("x", 0)),
            int(pos.get("y", 0)),
            layer_order=data.get("layer_order"),
            layer_offset=data.get("layer_offset"),
        )
        main_window.window_manager.text_windows.append(window)
        return window

    file_manager.create_text_window_from_data = _create_text_window_from_data  # type: ignore[attr-defined]
    file_manager.create_image_window_from_data = lambda _data: None  # type: ignore[attr-defined]
    return file_manager, main_window


def test_load_scene_applies_layer_offset_to_child_position() -> None:
    fm, mw = _build_file_manager()
    scene = {
        "format_version": 1,
        "windows": [
            {"uuid": "parent", "type": "text", "position": {"x": 100, "y": 200}},
            {
                "uuid": "child",
                "type": "text",
                "parent_uuid": "parent",
                "position": {"x": 5, "y": 6},
                "layer_order": 0,
                "layer_offset": {"x": 30, "y": -10},
            },
        ],
        "connections": [],
    }

    fm.load_scene_from_data(scene)

    parent = next(w for w in mw.window_manager.text_windows if w.uuid == "parent")
    child = next(w for w in mw.window_manager.text_windows if w.uuid == "child")
    assert child.parent_window_uuid == parent.uuid
    assert child.pos() == QPoint(130, 190)
    assert child.config.position == {"x": 130, "y": 190}


def test_load_scene_keeps_absolute_position_when_layer_offset_is_invalid() -> None:
    fm, mw = _build_file_manager()
    scene = {
        "format_version": 1,
        "windows": [
            {"uuid": "parent", "type": "text", "position": {"x": 10, "y": 20}},
            {
                "uuid": "child",
                "type": "text",
                "parent_uuid": "parent",
                "position": {"x": 5, "y": 6},
                "layer_order": 0,
                "layer_offset": {"x": "bad", "y": 3},
            },
        ],
        "connections": [],
    }

    fm.load_scene_from_data(scene)

    child = next(w for w in mw.window_manager.text_windows if w.uuid == "child")
    assert child.pos() == QPoint(5, 6)
    assert child.config.position == {"x": 5, "y": 6}

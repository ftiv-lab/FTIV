from __future__ import annotations

from pathlib import Path

from managers.info_index_manager import InfoQuery


def _read_text(relative_path: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / relative_path).read_text(encoding="utf-8")


def test_text_renderer_stays_ui_independent() -> None:
    src = _read_text("windows/text_renderer.py")

    # Renderer must not depend on UI-layer modules or orchestration objects.
    assert "from ui." not in src
    assert "import ui." not in src
    assert "main_window" not in src
    assert "property_panel" not in src
    assert "window_manager" not in src


def test_main_window_does_not_directly_use_text_renderer() -> None:
    src = _read_text("ui/main_window.py")

    # Rendering must stay behind TextWindow -> TextRenderer delegation.
    assert "from windows.text_renderer import" not in src
    assert "TextRenderer(" not in src


def test_property_panel_does_not_call_text_renderer_directly() -> None:
    src = _read_text("ui/property_panel.py")
    lowered = src.lower()

    assert "text_renderer" not in lowered
    # Property updates should flow through TextWindow.set_undoable_property.
    assert "set_undoable_property(" in src


def test_dialog_only_edit_symbols_are_not_reintroduced() -> None:
    text_window_src = _read_text("windows/text_window.py")
    connector_src = _read_text("windows/connector.py")

    # Dialog-only policy: no inline-edit mode menu or inline starter.
    assert "menu_text_editing_mode" not in text_window_src
    assert "_start_inline_edit" not in text_window_src
    assert "_start_inline_edit" not in connector_src
    # ConnectorLabel should keep dialog route.
    assert "edit_text_realtime(" in connector_src


def test_info_query_legacy_mode_filter_is_not_reintroduced() -> None:
    query = InfoQuery()
    assert not hasattr(query, "mode_filter")

from __future__ import annotations

from pathlib import Path

from managers.info_index_manager import InfoQuery


def _read_text(relative_path: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / relative_path).read_text(encoding="utf-8")


def _extract_method_block(src: str, method_name: str) -> str:
    marker = f"def {method_name}("
    start = src.find(marker)
    assert start >= 0, f"method not found: {method_name}"
    next_def = src.find("\n    def ", start + len(marker))
    if next_def < 0:
        next_def = len(src)
    return src[start:next_def]


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


def test_text_window_does_not_directly_chain_main_window_managers() -> None:
    src = _read_text("windows/text_window.py")

    forbidden = (
        "main_window.window_manager",
        "main_window.file_manager",
        "main_window.style_manager",
        "main_window.undo_stack",
        "main_window.settings_manager",
    )
    for token in forbidden:
        assert token not in src


def test_text_renderer_uses_renderer_input_contract() -> None:
    src = _read_text("windows/text_renderer.py")

    assert "from models.protocols import RendererInput" in src
    assert "def _adapt_renderer_input" in src
    assert "def render(self, window: RendererInput)" in src
    assert "def paint_direct(" in src and "window: RendererInput" in src
    assert "def get_task_line_rects(self, window: RendererInput)" in src


def test_property_panel_note_meta_path_uses_contracts() -> None:
    src = _read_text("ui/property_panel.py")

    assert "from models.protocols import NoteMetadataEditableTarget, UndoableConfigurable" in src
    block = _extract_method_block(src, "_apply_note_metadata_to_target")
    assert "isinstance(target, NoteMetadataEditableTarget)" in block
    assert "isinstance(target, UndoableConfigurable)" in block

    # Guard against reintroducing dynamic capability checks in this contractized path.
    forbidden = (
        'hasattr(target, "set_title_and_tags")',
        'hasattr(target, "set_starred")',
        'hasattr(target, "set_due_at")',
        'hasattr(target, "clear_due_at")',
        'hasattr(target, "set_archived")',
        'hasattr(target, "set_undoable_property")',
    )
    for token in forbidden:
        assert token not in block


def test_text_window_routes_manager_ops_via_runtime_services() -> None:
    src = _read_text("windows/text_window.py")
    assert "from managers.runtime_services import TextWindowRuntimeServices" in src

    for method_name in (
        "keyPressEvent",
        "add_text_window",
        "clone_text",
        "hide_all_other_windows",
        "close_all_other_windows",
        "save_text_to_json",
        "load_text_from_json",
        "load_text_defaults",
        "show_context_menu",
        "open_style_gallery",
    ):
        block = _extract_method_block(src, method_name)
        assert "_runtime_services(" in block, f"{method_name} should use runtime services"


def test_info_query_legacy_mode_filter_is_not_reintroduced() -> None:
    query = InfoQuery()
    assert not hasattr(query, "mode_filter")

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


def test_text_renderer_keeps_decomposition_entrypoints() -> None:
    src = _read_text("windows/text_renderer.py")
    adapter_src = _read_text("windows/text_rendering/adapter.py")
    layout_src = _read_text("windows/text_rendering/layout.py")

    assert "from windows.text_rendering import" in src
    for symbol in (
        "RendererInputAdapter",
        "adapt_renderer_input",
        "calculate_shadow_padding",
        "get_blur_radius_px",
    ):
        assert symbol in src
    assert "class _RendererInputAdapter" not in src
    assert "class RendererInputAdapter" in adapter_src
    assert "def adapt_renderer_input(" in adapter_src
    assert "def calculate_shadow_padding(" in layout_src
    assert "def get_blur_radius_px(" in layout_src


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


def test_text_window_task_and_selection_are_delegated_to_parts() -> None:
    src = _read_text("windows/text_window.py")
    task_src = _read_text("windows/text_window_parts/task_ops.py")
    selection_src = _read_text("windows/text_window_parts/selection_ops.py")

    assert "from .text_window_parts import task_ops as text_window_task_ops" in src
    assert "from .text_window_parts import selection_ops as text_window_selection_ops" in src
    assert "def task_progress_counts(" in task_src
    assert "def toggle_task_line_by_index(" in task_src
    assert "def hit_test_task_checkbox(" in selection_src

    expected_calls = (
        ("set_selected", "text_window_selection_ops.after_set_selected("),
        ("_task_progress_counts", "text_window_task_ops.task_progress_counts("),
        ("_toggle_task_line_by_index", "text_window_task_ops.toggle_task_line_by_index("),
        ("iter_task_items", "text_window_task_ops.iter_task_items("),
        ("get_task_line_state", "text_window_task_ops.get_task_line_state("),
        ("set_task_line_state", "text_window_task_ops.set_task_line_state("),
        ("toggle_task_line_state", "text_window_task_ops.toggle_task_line_state("),
        ("bulk_set_task_done", "text_window_task_ops.bulk_set_task_done("),
        ("complete_all_tasks", "text_window_task_ops.complete_all_tasks("),
        ("uncomplete_all_tasks", "text_window_task_ops.uncomplete_all_tasks("),
        ("mousePressEvent", "text_window_selection_ops.mouse_press("),
        ("mouseReleaseEvent", "text_window_selection_ops.mouse_release_should_toggle("),
        ("mouseMoveEvent", "text_window_selection_ops.mouse_move("),
        ("_hit_test_task_checkbox", "text_window_selection_ops.hit_test_task_checkbox("),
    )
    for method_name, token in expected_calls:
        block = _extract_method_block(src, method_name)
        assert token in block, f"{method_name} should delegate to extracted part"


def test_property_panel_text_sections_are_delegated() -> None:
    src = _read_text("ui/property_panel.py")
    content_src = _read_text("ui/property_panel_sections/text_content_section.py")
    style_src = _read_text("ui/property_panel_sections/text_style_section.py")

    assert "from ui.property_panel_sections import build_text_content_section, build_text_style_section" in src
    assert "def build_text_content_section(" in content_src
    assert "def build_text_style_section(" in style_src

    block = _extract_method_block(src, "build_text_window_ui")
    assert "build_text_content_section(self, target)" in block
    assert "build_text_style_section(self, target)" in block

    forbidden = (
        "mode_row = QWidget()",
        "text_content_layout = self.create_collapsible_group(",
        "text_style_layout = self.create_collapsible_group(",
    )
    for token in forbidden:
        assert token not in block


def test_info_query_legacy_mode_filter_is_not_reintroduced() -> None:
    query = InfoQuery()
    assert not hasattr(query, "mode_filter")

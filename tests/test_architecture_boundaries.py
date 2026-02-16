from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional

from managers.info_index_manager import InfoQuery


def _read_text(relative_path: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / relative_path).read_text(encoding="utf-8")


def _parse_module(relative_path: str) -> ast.Module:
    return ast.parse(_read_text(relative_path))


def _iter_python_files(relative_dir: str) -> list[str]:
    root = Path(__file__).resolve().parents[1]
    base = root / relative_dir
    return sorted(str(path.relative_to(root).as_posix()) for path in base.glob("*.py"))


def _imported_module_names(module_ast: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(module_ast):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


def _contains_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(prefix + ".")


def _imported_symbols(
    module_ast: ast.Module,
    *,
    module_name: str,
    level: int = 0,
) -> set[tuple[str, Optional[str]]]:
    symbols: set[tuple[str, Optional[str]]] = set()
    for node in module_ast.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != module_name or node.level != level:
            continue
        for alias in node.names:
            symbols.add((alias.name, alias.asname))
    return symbols


def _find_class(module_ast: ast.Module, class_name: str) -> ast.ClassDef:
    for node in module_ast.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"class not found: {class_name}")


def _find_method(module_ast: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    cls = _find_class(module_ast, class_name)
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    raise AssertionError(f"method not found: {class_name}.{method_name}")


def _find_function(module_ast: ast.Module, function_name: str) -> ast.FunctionDef:
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    raise AssertionError(f"function not found: {function_name}")


def _dotted_name(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def _function_has_call(func: ast.FunctionDef, call_path: str) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and _dotted_name(node.func) == call_path:
            return True
    return False


def _method_argument_annotation(
    module_ast: ast.Module,
    *,
    class_name: str,
    method_name: str,
    arg_name: str,
) -> Optional[str]:
    method = _find_method(module_ast, class_name, method_name)
    for arg in method.args.args:
        if arg.arg != arg_name:
            continue
        ann = arg.annotation
        if isinstance(ann, ast.Name):
            return ann.id
        if isinstance(ann, ast.Attribute):
            return _dotted_name(ann)
        return None
    return None


def test_text_renderer_stays_ui_independent() -> None:
    src = _read_text("windows/text_renderer.py")
    module_ast = _parse_module("windows/text_renderer.py")

    # Renderer must not depend on UI-layer modules or orchestration objects.
    for node in ast.walk(module_ast):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("ui.")
        if isinstance(node, ast.ImportFrom):
            imported_module = node.module or ""
            assert not imported_module.startswith("ui.")
    assert "main_window" not in src
    assert "property_panel" not in src
    assert "window_manager" not in src


def test_main_window_does_not_directly_use_text_renderer() -> None:
    module_ast = _parse_module("ui/main_window.py")
    source = _read_text("ui/main_window.py")

    # Rendering must stay behind TextWindow -> TextRenderer delegation.
    assert not _imported_symbols(module_ast, module_name="windows.text_renderer")
    assert "TextRenderer(" not in source


def test_property_panel_does_not_call_text_renderer_directly() -> None:
    module_ast = _parse_module("ui/property_panel.py")
    source = _read_text("ui/property_panel.py")

    for node in ast.walk(module_ast):
        if isinstance(node, ast.ImportFrom):
            assert node.module != "windows.text_renderer"
    assert "text_renderer" not in source.lower()
    # Property updates should flow through TextWindow.set_undoable_property.
    assert any(
        isinstance(node, ast.Call) and _dotted_name(node.func) == "target.set_undoable_property"
        for node in ast.walk(module_ast)
    )


def test_text_rendering_modules_do_not_import_ui_layer() -> None:
    for relative_path in _iter_python_files("windows/text_rendering"):
        module_ast = _parse_module(relative_path)
        imported_names = _imported_module_names(module_ast)
        forbidden = sorted(name for name in imported_names if _contains_prefix(name, "ui"))
        assert not forbidden, f"{relative_path} should not import ui.* (found: {forbidden})"


def test_text_window_parts_do_not_import_ui_layer() -> None:
    for relative_path in _iter_python_files("windows/text_window_parts"):
        module_ast = _parse_module(relative_path)
        imported_names = _imported_module_names(module_ast)
        forbidden = sorted(name for name in imported_names if _contains_prefix(name, "ui"))
        assert not forbidden, f"{relative_path} should not import ui.* (found: {forbidden})"


def test_property_panel_sections_do_not_import_text_renderer_directly() -> None:
    for relative_path in _iter_python_files("ui/property_panel_sections"):
        module_ast = _parse_module(relative_path)
        imported_names = _imported_module_names(module_ast)
        forbidden = sorted(name for name in imported_names if _contains_prefix(name, "windows.text_renderer"))
        assert not forbidden, f"{relative_path} should not import windows.text_renderer directly (found: {forbidden})"


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
    module_ast = _parse_module("windows/text_renderer.py")

    imported = _imported_symbols(module_ast, module_name="models.protocols")
    assert ("RendererInput", None) in imported

    _find_method(module_ast, "TextRenderer", "_adapt_renderer_input")
    assert (
        _method_argument_annotation(
            module_ast,
            class_name="TextRenderer",
            method_name="render",
            arg_name="window",
        )
        == "RendererInput"
    )
    assert (
        _method_argument_annotation(
            module_ast,
            class_name="TextRenderer",
            method_name="paint_direct",
            arg_name="window",
        )
        == "RendererInput"
    )
    assert (
        _method_argument_annotation(
            module_ast,
            class_name="TextRenderer",
            method_name="get_task_line_rects",
            arg_name="window",
        )
        == "RendererInput"
    )


def test_text_renderer_keeps_decomposition_entrypoints() -> None:
    module_ast = _parse_module("windows/text_renderer.py")
    adapter_ast = _parse_module("windows/text_rendering/adapter.py")
    layout_ast = _parse_module("windows/text_rendering/layout.py")

    imported = _imported_symbols(module_ast, module_name="windows.text_rendering")
    for symbol in {
        "RendererInputAdapter",
        "adapt_renderer_input",
        "calculate_shadow_padding",
        "get_blur_radius_px",
    }:
        assert any(name == symbol for name, _ in imported)

    assert all(
        not (isinstance(node, ast.ClassDef) and node.name == "_RendererInputAdapter") for node in module_ast.body
    )
    _find_class(adapter_ast, "RendererInputAdapter")
    _find_function(adapter_ast, "adapt_renderer_input")
    _find_function(layout_ast, "calculate_shadow_padding")
    _find_function(layout_ast, "get_blur_radius_px")


def test_property_panel_note_meta_path_uses_contracts() -> None:
    module_ast = _parse_module("ui/property_panel.py")
    imported = _imported_symbols(module_ast, module_name="models.protocols")
    assert ("NoteMetadataEditableTarget", None) in imported
    assert ("UndoableConfigurable", None) in imported

    method = _find_method(module_ast, "PropertyPanel", "_apply_note_metadata_to_target")
    isinstance_targets: set[str] = set()
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        if _dotted_name(node.func) != "isinstance" or len(node.args) != 2:
            continue
        first, second = node.args
        if isinstance(first, ast.Name) and first.id == "target":
            name = _dotted_name(second)
            if name:
                isinstance_targets.add(name)
    assert "NoteMetadataEditableTarget" in isinstance_targets
    assert "UndoableConfigurable" in isinstance_targets

    # Guard against reintroducing dynamic capability checks in this contractized path.
    forbidden = {
        "set_title_and_tags",
        "set_starred",
        "set_due_at",
        "clear_due_at",
        "set_archived",
        "set_undoable_property",
    }
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        if _dotted_name(node.func) != "hasattr" or len(node.args) < 2:
            continue
        first, second = node.args[:2]
        if isinstance(first, ast.Name) and first.id == "target" and isinstance(second, ast.Constant):
            assert second.value not in forbidden


def test_text_window_routes_manager_ops_via_runtime_services() -> None:
    module_ast = _parse_module("windows/text_window.py")
    imported = _imported_symbols(module_ast, module_name="managers.runtime_services")
    assert ("TextWindowRuntimeServices", None) in imported

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
        method = _find_method(module_ast, "TextWindow", method_name)
        assert _function_has_call(method, "self._runtime_services"), f"{method_name} should use runtime services"


def test_text_window_task_and_selection_are_delegated_to_parts() -> None:
    module_ast = _parse_module("windows/text_window.py")
    task_ast = _parse_module("windows/text_window_parts/task_ops.py")
    selection_ast = _parse_module("windows/text_window_parts/selection_ops.py")

    imported = _imported_symbols(module_ast, module_name="text_window_parts", level=1)
    assert ("task_ops", "text_window_task_ops") in imported
    assert ("selection_ops", "text_window_selection_ops") in imported
    _find_function(task_ast, "task_progress_counts")
    _find_function(task_ast, "toggle_task_line_by_index")
    _find_function(selection_ast, "hit_test_task_checkbox")

    expected_calls = (
        ("set_selected", "text_window_selection_ops.after_set_selected"),
        ("_task_progress_counts", "text_window_task_ops.task_progress_counts"),
        ("_toggle_task_line_by_index", "text_window_task_ops.toggle_task_line_by_index"),
        ("iter_task_items", "text_window_task_ops.iter_task_items"),
        ("get_task_line_state", "text_window_task_ops.get_task_line_state"),
        ("set_task_line_state", "text_window_task_ops.set_task_line_state"),
        ("toggle_task_line_state", "text_window_task_ops.toggle_task_line_state"),
        ("bulk_set_task_done", "text_window_task_ops.bulk_set_task_done"),
        ("complete_all_tasks", "text_window_task_ops.complete_all_tasks"),
        ("uncomplete_all_tasks", "text_window_task_ops.uncomplete_all_tasks"),
        ("mousePressEvent", "text_window_selection_ops.mouse_press"),
        ("mouseReleaseEvent", "text_window_selection_ops.mouse_release_should_toggle"),
        ("mouseMoveEvent", "text_window_selection_ops.mouse_move"),
        ("_hit_test_task_checkbox", "text_window_selection_ops.hit_test_task_checkbox"),
    )
    for method_name, call_path in expected_calls:
        method = _find_method(module_ast, "TextWindow", method_name)
        assert _function_has_call(method, call_path), f"{method_name} should delegate to extracted part"


def test_property_panel_text_sections_are_delegated() -> None:
    module_ast = _parse_module("ui/property_panel.py")
    content_ast = _parse_module("ui/property_panel_sections/text_content_section.py")
    style_ast = _parse_module("ui/property_panel_sections/text_style_section.py")

    imported = _imported_symbols(module_ast, module_name="ui.property_panel_sections")
    assert ("build_text_content_section", None) in imported
    assert ("build_text_style_section", None) in imported
    _find_function(content_ast, "build_text_content_section")
    _find_function(style_ast, "build_text_style_section")

    method = _find_method(module_ast, "PropertyPanel", "build_text_window_ui")
    assert _function_has_call(method, "build_text_content_section")
    assert _function_has_call(method, "build_text_style_section")

    assigned_names: set[str] = set()
    for node in ast.walk(method):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id)
    assert "mode_row" not in assigned_names
    assert "text_content_layout" not in assigned_names
    assert "text_style_layout" not in assigned_names


def test_info_query_legacy_mode_filter_is_not_reintroduced() -> None:
    query = InfoQuery()
    assert not hasattr(query, "mode_filter")

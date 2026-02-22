from types import SimpleNamespace
from unittest.mock import MagicMock

from managers.runtime_services import TextWindowRuntimeServices


def test_window_manager_delegation_methods() -> None:
    wm = MagicMock()
    services = TextWindowRuntimeServices(SimpleNamespace(window_manager=wm))
    target = MagicMock()

    assert services.create_related_node(target, "child") is True
    wm.create_related_node.assert_called_once_with(target, "child")

    assert services.navigate_selection(target, 16777235) is True
    wm.navigate_selection.assert_called_once_with(target, 16777235)

    assert services.clone_text_window(target) is True
    wm.clone_text_window.assert_called_once_with(target)


def test_add_text_window_returns_window_from_manager() -> None:
    created = object()
    wm = MagicMock()
    wm.add_text_window.return_value = created
    services = TextWindowRuntimeServices(SimpleNamespace(window_manager=wm))

    got = services.add_text_window("hello", pos=MagicMock(), suppress_limit_message=False)
    assert got is created


def test_file_manager_delegation_methods() -> None:
    fm = MagicMock()
    target = MagicMock()
    services = TextWindowRuntimeServices(SimpleNamespace(file_manager=fm))

    assert services.save_window_to_json(target) is True
    fm.save_window_to_json.assert_called_once_with(target)

    assert services.load_window_from_json(target) is True
    fm.load_window_from_json.assert_called_once_with(target)

    assert services.load_scene_from_json() is True
    fm.load_scene_from_json.assert_called_once_with()


def test_style_manager_delegation_methods() -> None:
    sm = MagicMock()
    target = MagicMock()
    services = TextWindowRuntimeServices(SimpleNamespace(style_manager=sm))

    assert services.save_text_style(target) is True
    sm.save_text_style.assert_called_once_with(target)

    assert services.load_text_style(target) is True
    sm.load_text_style.assert_called_once_with(target)

    assert services.load_text_style(target, "style.json") is True
    sm.load_text_style.assert_called_with(target, "style.json")


def test_undo_macro_delegation_methods() -> None:
    stack = MagicMock()
    services = TextWindowRuntimeServices(SimpleNamespace(undo_stack=stack))

    assert services.begin_undo_macro("Macro") is True
    stack.beginMacro.assert_called_once_with("Macro")

    assert services.end_undo_macro() is True
    stack.endMacro.assert_called_once_with()


def test_missing_components_are_safe_noop() -> None:
    services = TextWindowRuntimeServices(SimpleNamespace())
    target = MagicMock()

    assert services.has_window_manager() is False
    assert services.has_file_manager() is False
    assert services.has_style_manager() is False
    assert services.has_settings_manager() is False
    assert services.has_undo_stack() is False

    assert services.create_related_node(target, "child") is False
    assert services.navigate_selection(target, 0) is False
    assert services.add_text_window("x", pos=MagicMock()) is None
    assert services.clone_text_window(target) is False
    assert services.hide_all_other_text_windows(target) is False
    assert services.close_all_other_text_windows(target) is False
    assert services.save_window_to_json(target) is False
    assert services.load_window_from_json(target) is False
    assert services.load_scene_from_json() is False
    assert services.save_text_style(target) is False
    assert services.load_text_style(target) is False
    assert services.begin_undo_macro("x") is False
    assert services.end_undo_macro() is False
    assert services.load_text_archetype() is None
    assert services.get_style_manager() is None
    assert services.get_json_directory() == ""

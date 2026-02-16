import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TextWindowRuntimeServices:
    """TextWindow が利用するランタイム依存（manager群）への薄いアクセサ。"""

    def __init__(self, main_window: Any) -> None:
        self._main_window = main_window

    def _get_component(self, name: str) -> Any | None:
        mw = self._main_window
        if mw is None:
            return None
        return getattr(mw, name, None)

    def has_window_manager(self) -> bool:
        return self._get_component("window_manager") is not None

    def has_file_manager(self) -> bool:
        return self._get_component("file_manager") is not None

    def has_style_manager(self) -> bool:
        return self._get_component("style_manager") is not None

    def has_settings_manager(self) -> bool:
        return self._get_component("settings_manager") is not None

    def has_undo_stack(self) -> bool:
        return self._get_component("undo_stack") is not None

    def begin_undo_macro(self, title: str) -> bool:
        stack = self._get_component("undo_stack")
        if stack is None or not hasattr(stack, "beginMacro"):
            return False
        stack.beginMacro(title)
        return True

    def end_undo_macro(self) -> bool:
        stack = self._get_component("undo_stack")
        if stack is None or not hasattr(stack, "endMacro"):
            return False
        stack.endMacro()
        return True

    def create_related_node(self, source: Any, relation: str) -> bool:
        manager = self._get_component("window_manager")
        if manager is None or not hasattr(manager, "create_related_node"):
            return False
        manager.create_related_node(source, relation)
        return True

    def navigate_selection(self, source: Any, key: int) -> bool:
        manager = self._get_component("window_manager")
        if manager is None or not hasattr(manager, "navigate_selection"):
            return False
        manager.navigate_selection(source, key)
        return True

    def add_text_window(self, text: str, pos: Any, suppress_limit_message: bool = False) -> Any | None:
        manager = self._get_component("window_manager")
        if manager is None or not hasattr(manager, "add_text_window"):
            return None
        return manager.add_text_window(text=text, pos=pos, suppress_limit_message=suppress_limit_message)

    def clone_text_window(self, source: Any) -> bool:
        manager = self._get_component("window_manager")
        if manager is None or not hasattr(manager, "clone_text_window"):
            return False
        manager.clone_text_window(source)
        return True

    def hide_all_other_text_windows(self, source: Any) -> bool:
        manager = self._get_component("window_manager")
        if manager is None or not hasattr(manager, "hide_all_other_text_windows"):
            return False
        manager.hide_all_other_text_windows(source)
        return True

    def close_all_other_text_windows(self, source: Any) -> bool:
        manager = self._get_component("window_manager")
        if manager is None or not hasattr(manager, "close_all_other_text_windows"):
            return False
        manager.close_all_other_text_windows(source)
        return True

    def save_window_to_json(self, source: Any) -> bool:
        manager = self._get_component("file_manager")
        if manager is None or not hasattr(manager, "save_window_to_json"):
            return False
        manager.save_window_to_json(source)
        return True

    def load_window_from_json(self, source: Any) -> bool:
        manager = self._get_component("file_manager")
        if manager is None or not hasattr(manager, "load_window_from_json"):
            return False
        manager.load_window_from_json(source)
        return True

    def load_scene_from_json(self) -> bool:
        manager = self._get_component("file_manager")
        if manager is None or not hasattr(manager, "load_scene_from_json"):
            return False
        manager.load_scene_from_json()
        return True

    def save_text_style(self, source: Any) -> bool:
        manager = self._get_component("style_manager")
        if manager is None or not hasattr(manager, "save_text_style"):
            return False
        manager.save_text_style(source)
        return True

    def load_text_style(self, source: Any, json_path: Optional[str] = None) -> bool:
        manager = self._get_component("style_manager")
        if manager is None or not hasattr(manager, "load_text_style"):
            return False
        if json_path:
            manager.load_text_style(source, json_path)
        else:
            manager.load_text_style(source)
        return True

    def get_style_manager(self) -> Any | None:
        return self._get_component("style_manager")

    def load_text_archetype(self) -> dict[str, Any] | None:
        manager = self._get_component("settings_manager")
        if manager is None or not hasattr(manager, "load_text_archetype"):
            return None
        raw = manager.load_text_archetype()
        return raw if isinstance(raw, dict) else None

    def get_json_directory(self) -> str:
        mw = self._main_window
        if mw is None:
            return ""
        raw = getattr(mw, "json_directory", "")
        return str(raw or "")

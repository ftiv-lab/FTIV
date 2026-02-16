from __future__ import annotations

from pathlib import Path

from utils.app_settings import _sanitize_user_info_presets


def _read_text(relative_path: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / relative_path).read_text(encoding="utf-8")


def test_runtime_legacy_method_names_are_removed() -> None:
    assert "_legacy_open_align_dialog" not in _read_text("ui/main_window.py")
    assert "_clear_legacy_absolute_move_fields" not in _read_text("windows/base_window.py")
    assert "_clear_legacy_absolute_move_fields" not in _read_text("managers/file_manager.py")


def test_info_preset_sanitizer_drops_mode_filter_on_save_contract() -> None:
    presets = _sanitize_user_info_presets(
        [
            {
                "id": "user:1",
                "name": "legacy",
                "filters": {"mode_filter": "task", "due_filter": "today"},
            }
        ]
    )
    assert len(presets) == 1
    filters = presets[0]["filters"]
    assert filters["item_scope"] == "tasks"
    assert filters["content_mode_filter"] == "task"
    assert "mode_filter" not in filters

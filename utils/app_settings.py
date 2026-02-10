# utils/app_settings.py
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtWidgets import QMessageBox

from utils.paths import get_base_dir
from utils.translator import tr

logger = logging.getLogger(__name__)

_INFO_DUE_FILTERS = {"all", "today", "overdue", "upcoming", "dated", "undated"}
_INFO_MODE_FILTERS = {"all", "task", "note"}
_INFO_SORT_FIELDS = {"updated", "due", "created", "title"}
_INFO_ARCHIVE_SCOPES = {"active", "archived", "all"}


def _sanitize_info_filters(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    return {
        "text": str(raw.get("text", "") or "").strip(),
        "tag": str(raw.get("tag", "") or "").strip(),
        "starred_only": bool(raw.get("starred_only", False)),
        "open_tasks_only": bool(raw.get("open_tasks_only", False)),
        "archive_scope": (
            str(raw.get("archive_scope", "active")).strip().lower()
            if str(raw.get("archive_scope", "active")).strip().lower() in _INFO_ARCHIVE_SCOPES
            else "active"
        ),
        "due_filter": (
            str(raw.get("due_filter", "all")).strip().lower()
            if str(raw.get("due_filter", "all")).strip().lower() in _INFO_DUE_FILTERS
            else "all"
        ),
        "mode_filter": (
            str(raw.get("mode_filter", "all")).strip().lower()
            if str(raw.get("mode_filter", "all")).strip().lower() in _INFO_MODE_FILTERS
            else "all"
        ),
        "sort_by": (
            str(raw.get("sort_by", "updated")).strip().lower()
            if str(raw.get("sort_by", "updated")).strip().lower() in _INFO_SORT_FIELDS
            else "updated"
        ),
        "sort_desc": bool(raw.get("sort_desc", True)),
    }


def _sanitize_user_info_presets(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        preset_id = str(entry.get("id", "") or "").strip()
        if not preset_id.startswith("user:") or preset_id in seen:
            continue
        name = str(entry.get("name", "") or "").strip()[:32]
        filters = _sanitize_info_filters(entry.get("filters", {}))
        if filters is None:
            continue
        if not name:
            name = preset_id.replace("user:", "", 1) or "Preset"
        out.append({"id": preset_id, "name": name, "filters": filters})
        seen.add(preset_id)
    return out


def _sanitize_info_operation_logs(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []

    out: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        at = str(entry.get("at", "") or "").strip()
        action = str(entry.get("action", "") or "").strip()
        try:
            target_count = int(entry.get("target_count", 0))
        except Exception:
            continue
        detail = str(entry.get("detail", "") or "").strip()[:80]
        if not at or not action or target_count < 1:
            continue
        out.append(
            {
                "at": at,
                "action": action,
                "target_count": target_count,
                "detail": detail,
            }
        )

    return out


@dataclass
class AppSettings:
    """アプリ全体の設定。"""

    main_window_frontmost: bool = True
    # パフォーマンス設定
    render_debounce_ms: int = 25  # 描画遅延(ms): 25=標準(高速), 大きい=軽量
    wheel_debounce_ms: int = 50  # ホイール操作中: 50=バランス, 大きい=操作性優先
    glyph_cache_size: int = 512  # 文字キャッシュ数
    info_view_presets: list[dict[str, Any]] = field(default_factory=list)
    info_last_view_preset_id: str = "builtin:all"
    info_operation_logs: list[dict[str, Any]] = field(default_factory=list)


def _get_settings_path(base_directory: str) -> str:
    """設定ファイルのパスを返す。"""
    # 引数が空なら自動取得
    if not base_directory:
        base_directory = get_base_dir()

    json_dir: str = os.path.join(base_directory, "json")
    os.makedirs(json_dir, exist_ok=True)
    return os.path.join(json_dir, "app_settings.json")


def save_app_settings(parent: Any, base_directory: str, settings: AppSettings) -> bool:
    """アプリ設定を保存する。"""
    path: str = _get_settings_path(base_directory)
    try:
        data: dict[str, Any] = {
            "main_window_frontmost": bool(settings.main_window_frontmost),
            "render_debounce_ms": int(settings.render_debounce_ms),
            "wheel_debounce_ms": int(settings.wheel_debounce_ms),  # ★追加
            "glyph_cache_size": int(settings.glyph_cache_size),
            "info_view_presets": _sanitize_user_info_presets(settings.info_view_presets),
            "info_last_view_preset_id": str(settings.info_last_view_preset_id or "builtin:all"),
            "info_operation_logs": _sanitize_info_operation_logs(settings.info_operation_logs)[-200:],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        QMessageBox.critical(
            parent,
            tr("msg_error"),
            tr("msg_failed_to_save_app_settings").format(err=str(e)),
        )
        return False


def load_app_settings(parent: Any, base_directory: str) -> AppSettings:
    """アプリ設定を読み込む。"""
    path: str = _get_settings_path(base_directory)
    if not os.path.exists(path):
        return AppSettings()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        s = AppSettings()
        if isinstance(data.get("main_window_frontmost"), bool):
            s.main_window_frontmost = bool(data["main_window_frontmost"])

        # パフォーマンス設定
        if isinstance(data.get("render_debounce_ms"), int):
            s.render_debounce_ms = int(data["render_debounce_ms"])
        if isinstance(data.get("wheel_debounce_ms"), int):  # ★追加
            s.wheel_debounce_ms = int(data["wheel_debounce_ms"])
        if isinstance(data.get("glyph_cache_size"), int):
            s.glyph_cache_size = int(data["glyph_cache_size"])

        s.info_view_presets = _sanitize_user_info_presets(data.get("info_view_presets", []))
        raw_preset_id = str(data.get("info_last_view_preset_id", "") or "").strip()
        if raw_preset_id:
            s.info_last_view_preset_id = raw_preset_id
        s.info_operation_logs = _sanitize_info_operation_logs(data.get("info_operation_logs", []))

        return s

    except Exception as e:
        try:
            QMessageBox.warning(
                parent,
                tr("msg_warning"),
                tr("msg_failed_to_load_app_settings").format(err=str(e)),
            )
        except Exception as msg_err:
            logger.warning(f"Failed to show load error message: {msg_err}")
        return AppSettings()

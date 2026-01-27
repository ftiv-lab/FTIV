# utils/app_settings.py
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import QMessageBox

from utils.paths import get_base_dir
from utils.translator import tr

logger = logging.getLogger(__name__)


@dataclass
class AppSettings:
    """アプリ全体の設定。"""

    main_window_frontmost: bool = True
    # パフォーマンス設定
    render_debounce_ms: int = 25  # 描画遅延(ms): 25=標準(高速), 大きい=軽量
    wheel_debounce_ms: int = 50  # ホイール操作中: 50=バランス, 大きい=操作性優先
    glyph_cache_size: int = 512  # 文字キャッシュ数


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

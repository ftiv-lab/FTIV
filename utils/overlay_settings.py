# utils/overlay_settings.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import QMessageBox

from utils.paths import get_base_dir
from utils.translator import tr


@dataclass
class OverlaySettings:
    """選択枠（オーバーレイ）の見た目設定。"""

    selection_frame_enabled: bool = True
    selection_frame_color: str = "#C800FFFF"  # AARRGGBB（例：シアン気味）
    selection_frame_width: int = 4


def _get_settings_path(base_directory: str) -> str:
    """設定ファイルのパスを返す。"""
    # 引数が空なら自動取得
    if not base_directory:
        base_directory = get_base_dir()

    json_dir: str = os.path.join(base_directory, "json")
    os.makedirs(json_dir, exist_ok=True)
    return os.path.join(json_dir, "overlay_settings.json")


def load_overlay_settings(parent: Any, base_directory: str) -> OverlaySettings:
    """オーバーレイ設定を読み込む。

    Args:
        parent (Any): QMessageBox 親。
        base_directory (str): アプリ基準ディレクトリ。

    Returns:
        OverlaySettings: 読み込んだ設定（失敗時はデフォルト）。
    """
    path: str = _get_settings_path(base_directory)
    if not os.path.exists(path):
        return OverlaySettings()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        s = OverlaySettings()
        if isinstance(data.get("selection_frame_enabled"), bool):
            s.selection_frame_enabled = data["selection_frame_enabled"]
        if isinstance(data.get("selection_frame_color"), str):
            s.selection_frame_color = data["selection_frame_color"]
        if isinstance(data.get("selection_frame_width"), int):
            s.selection_frame_width = int(data["selection_frame_width"])
        return s

    except Exception as e:
        QMessageBox.warning(parent, tr("msg_warning"), f"Failed to load overlay settings: {e}")
        return OverlaySettings()


def save_overlay_settings(parent: Any, base_directory: str, settings: OverlaySettings) -> bool:
    """オーバーレイ設定を保存する。

    Args:
        parent (Any): QMessageBox 親。
        base_directory (str): アプリ基準ディレクトリ。
        settings (OverlaySettings): 保存する設定。

    Returns:
        bool: 成功したら True。
    """
    path: str = _get_settings_path(base_directory)
    try:
        data: dict[str, Any] = {
            "selection_frame_enabled": bool(settings.selection_frame_enabled),
            "selection_frame_color": str(settings.selection_frame_color),
            "selection_frame_width": int(settings.selection_frame_width),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        QMessageBox.critical(parent, tr("msg_error"), f"Failed to save overlay settings: {e}")
        return False

# utils/edition.py
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from PySide6.QtWidgets import QMessageBox

from utils.paths import get_base_dir
from utils.translator import tr


class Edition(str, Enum):
    """アプリのエディション種別。"""

    STANDARD = "standard"


@dataclass(frozen=True)
class Limits:
    """エディション別の制限値（v1.0以降は実質無制限）。"""

    max_text_windows: int
    max_image_windows: int
    max_save_slots: int


def _get_settings_path(base_directory: str) -> str:
    """設定ファイルのパスを返す。"""
    # 引数が空なら自動取得
    if not base_directory:
        base_directory = get_base_dir()

    json_dir: str = os.path.join(base_directory, "json")
    os.makedirs(json_dir, exist_ok=True)
    return os.path.join(json_dir, "app_settings.json")


def get_edition(parent: Optional[Any] = None, base_directory: Optional[str] = None) -> Edition:
    """現在のエディションを返す。

    Returns:
        Edition: 常時 STANDARD を返す。
    """
    return Edition.STANDARD


def get_limits(edition: Optional[Edition] = None) -> Limits:
    """エディションに応じた制限値を返す。

    v1.0からは全ユーザー無制限。
    """
    # 実質無限
    return Limits(
        max_text_windows=10**9,
        max_image_windows=10**9,
        max_save_slots=10**9,
    )


def is_over_limit(current: int, maximum: int) -> bool:
    """上限超過かどうか。"""
    return int(current) >= int(maximum)


def show_limit_message(parent: Any, message_key: str, suppress: bool = False) -> None:
    """制限に達したことをユーザーに通知する。

    Args:
        parent (Any): QMessageBox の親。
        message_key (str): 翻訳キー。
        suppress (bool): True の場合は通知しない。
    """
    if suppress:
        return
    QMessageBox.information(parent, tr("msg_info"), tr(message_key))


# 将来的にここを実際の販売ページURLに書き換えてください
SHOP_URL = "https://booth.pm/"

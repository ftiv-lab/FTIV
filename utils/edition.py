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

    FREE = "free"
    PRO = "pro"


@dataclass(frozen=True)
class Limits:
    """エディション別の制限値。"""

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
    """現在のエディションを返す（開発用：固定）。

    開発段階では「ここを1行変える」方式が最も直感的なので固定にする。
    販売段階でライセンス導入する場合は、この関数内部を差し替える。

    Args:
        parent (Optional[Any]): 将来用（未使用）。
        base_directory (Optional[str]): 将来用（未使用）。

    Returns:
        Edition: 現在のエディション。
    """
    # ★開発用切替：ここを FREE / PRO に変えるだけ
    return Edition.PRO


def get_limits(edition: Optional[Edition] = None) -> Limits:
    """エディションに応じた制限値を返す。

    Args:
        edition (Optional[Edition]): 指定がなければ PRO を仮定する（呼び出し側が get_edition して渡す推奨）。

    Returns:
        Limits: 制限値。
    """
    ed: Edition = edition or Edition.PRO

    if ed == Edition.PRO:
        return Limits(
            max_text_windows=10**9,
            max_image_windows=10**9,
            max_save_slots=10**9,
        )

    return Limits(
        max_text_windows=5,
        max_image_windows=5,
        max_save_slots=5,
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

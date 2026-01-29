# utils/error_reporter.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QMessageBox

from utils.translator import tr

logger = logging.getLogger(__name__)


@dataclass
class ErrorNotifyState:
    """同じ例外の連続通知を抑制するための状態。"""

    last_signature: str = ""
    last_shown_ts_ms: int = 0


def _signature(title: str, exc: BaseException) -> str:
    """例外通知の抑制判定に使う署名文字列を作る。

    Args:
        title (str): エラーの文脈。
        exc (BaseException): 例外。

    Returns:
        str: 署名文字列。
    """
    return f"{title}:{type(exc).__name__}:{str(exc)}"


def report_unexpected_error(
    parent: Any,
    title: str,
    exc: BaseException,
    state: Optional[ErrorNotifyState] = None,
    cooldown_ms: int = 2000,
) -> None:
    """予期しない例外をログに残し、必要なら QMessageBox でユーザー通知する。

    Args:
        parent (Any): QMessageBox の親（通常は MainWindow）。
        title (str): どの操作で起きたかの説明（ログ/通知用）。
        exc (BaseException): 捕捉した例外。
        state (Optional[ErrorNotifyState]): 連続通知抑制用の状態。
        cooldown_ms (int): 同一例外の通知を抑制する時間(ms)。
    """
    logger.exception("%s: %s", title, exc)

    # 連打抑制（同じ例外を短時間で何度も出さない）
    if state is not None:
        now_ms: int = int(QDateTime.currentMSecsSinceEpoch())
        sig: str = _signature(title, exc)

        if sig == state.last_signature and (now_ms - state.last_shown_ts_ms) < cooldown_ms:
            return

        state.last_signature = sig
        state.last_shown_ts_ms = now_ms

    try:
        QMessageBox.critical(
            parent,
            tr("msg_error"),
            f"{title}\n\n{exc}\n\n(詳細はログを確認してください)",
        )
    except Exception:
        # 通知で落ちない
        pass

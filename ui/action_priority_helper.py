from __future__ import annotations

from typing import Any


class ActionPriorityHelper:
    """Compact/Comfortable でのボタン文言切り替えを共通化する。"""

    @staticmethod
    def apply_label_mode(entries: list[tuple[Any, str, str]], compact: bool) -> None:
        for widget, full_text, short_text in entries:
            if widget is None:
                continue
            text = short_text if compact else full_text
            if hasattr(widget, "setText"):
                widget.setText(text)
            if hasattr(widget, "setToolTip"):
                widget.setToolTip(full_text)

    @staticmethod
    def mark_compact_actions(entries: list[tuple[Any, str, str]]) -> None:
        for widget, _, _ in entries:
            if widget is None:
                continue
            if hasattr(widget, "setProperty"):
                widget.setProperty("compactAction", True)

"""
tests/test_shortcut_contract.py

ショートカット契約の静的チェック。
Layer/Connector が Shift 系ショートカットを使っていないことを確認する。

契約定義: docs/RUNBOOK.md §11
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Shift系キーが Layer操作に使われていないことを確認する対象ファイル
LAYER_FILES_TO_CHECK = [
    "ui/tabs/layer_tab.py",
]


class TestShortcutContract:
    """Layer機能のショートカット契約テスト。"""

    def test_layer_tab_does_not_use_shift_as_primary_trigger(self) -> None:
        """
        layer_tab.py が Shift を Layer操作のトリガーとして使っていないこと。
        ファイルが存在しない場合はスキップ（未実装フェーズ）。
        """
        layer_tab_path = REPO_ROOT / "ui" / "tabs" / "layer_tab.py"
        if not layer_tab_path.exists():
            # 未実装フェーズではスキップ
            return

        source = layer_tab_path.read_text(encoding="utf-8")

        # ShiftModifier が attach/detach のトリガーとして直接使われていないこと
        # (コメント内は除外)
        lines = source.splitlines()
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # コメント行はスキップ
            # ShiftModifier が attach/detach 判定の直接条件になっていないか
            if "ShiftModifier" in line and ("attach" in line.lower() or "detach" in line.lower()):
                raise AssertionError(
                    f"layer_tab.py:{lineno}: ShiftModifierをLayer操作トリガーに使用しています。"
                    " Shiftは接続作成（ConnectorLine）に予約済みです。"
                    " Layerの主導線はLayerタブUI/右クリックメニューにしてください。"
                )

    def test_layer_alt_shortcuts_are_not_bound(self) -> None:
        """
        Layer操作は UI導線が契約であり、Alt 系ショートカットを未割り当てとして維持する。
        """
        forbidden_tokens = [
            "Qt.Key_P",
            "Qt.Key_D",
            "Qt.Key_BracketRight",
            "Qt.Key_BracketLeft",
        ]
        check_dirs = ["windows", "ui", "managers", "utils"]
        violations: list[str] = []
        for dir_name in check_dirs:
            dir_path = REPO_ROOT / dir_name
            if not dir_path.exists():
                continue
            for py_file in dir_path.rglob("*.py"):
                try:
                    source = py_file.read_text(encoding="utf-8")
                except Exception:
                    continue
                if "AltModifier" not in source:
                    continue
                if any(token in source for token in forbidden_tokens):
                    violations.append(str(py_file.relative_to(REPO_ROOT)))
        if violations:
            raise AssertionError(
                "Layerで未割り当てにしている Alt ショートカット候補が実装に混入しています:\n"
                + "\n".join(f"  - {v}" for v in violations)
            )

    def test_base_window_does_not_bind_shift_shortcut(self) -> None:
        """
        base_window.py で ShiftModifier をショートカットとして使っていないこと。
        """
        base_window_path = REPO_ROOT / "windows" / "base_window.py"
        assert base_window_path.exists(), "base_window.py が見つかりません"

        source = base_window_path.read_text(encoding="utf-8")
        assert "ShiftModifier" not in source, (
            "base_window.py に ShiftModifier のバインドが残っています。"
            " 現契約では Shift 系ショートカットは未割り当てです。"
        )

    def test_shortcut_contract_documentation_exists(self) -> None:
        """RUNBOOK.md に Layer Shortcut Contract セクションが存在すること。"""
        runbook_path = REPO_ROOT / "docs" / "RUNBOOK.md"
        assert runbook_path.exists(), "docs/RUNBOOK.md が見つかりません"
        content = runbook_path.read_text(encoding="utf-8")
        assert "Layer / Connector Shortcut Contract" in content, (
            "docs/RUNBOOK.md に '## 11. Layer / Connector Shortcut Contract' セクションがありません。"
            " Layer操作のショートカット契約を文書化してください。"
        )
        assert "Shift shortcuts are intentionally unassigned" in content, (
            "RUNBOOK.md に Shift 未割り当て契約が記載されていません。"
        )

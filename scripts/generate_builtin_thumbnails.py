# -*- coding: utf-8 -*-
"""SP5: ビルトインプリセットのサムネイル一括生成.

json/presets/*.json に対応するPNGサムネイルを生成する。
QApplication が必要なためGUIコンテキストで実行。

使い方:
    uv run python scripts/generate_builtin_thumbnails.py
"""

import glob
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication  # noqa: E402

from managers.style_manager import StyleManager  # noqa: E402


def main() -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # StyleManager のインスタンスを作成（json_directory を指定）
    from unittest.mock import MagicMock

    mw = MagicMock()
    mw.json_directory = os.path.join(PROJECT_ROOT, "json")
    sm = StyleManager(mw)

    presets_dir = os.path.join(PROJECT_ROOT, "json", "presets")
    json_files = sorted(glob.glob(os.path.join(presets_dir, "*.json")))

    success = 0
    fail = 0
    for json_path in json_files:
        base = os.path.splitext(os.path.basename(json_path))[0]
        ok = sm.generate_thumbnail(json_path)
        if ok:
            success += 1
            print(f"  OK: {base}")
        else:
            fail += 1
            print(f"  FAIL: {base}")

    print(f"\nThumbnail generation complete: {success} OK, {fail} FAIL (total {len(json_files)})")


if __name__ == "__main__":
    main()

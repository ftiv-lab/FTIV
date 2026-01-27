# 初期化リグレッション修正計画

## 問題
`MainWindow` が起動時に「細く」（おそらくデフォルトの最小幅で）表示され、直後に正常なサイズに戻るという現象が報告された。
この挙動は、設定ロジックを `SettingsManager` にリファクタリングした後に発生した。
現状では、`init_window_settings()`（`resize(380, 700)` を呼ぶ）が `setup_ui()` の **前** に呼ばれている。`setup_ui()` 内でのレイアウト構築処理が、一時的に初期サイズを上書きしている可能性が高い。

## 修正案

### `ui/main_window.py`
`self.settings_manager.init_window_settings()` の呼び出しを、`__init__` の冒頭から **`self.setup_ui()` の後** に移動する。

**現在の順序:**
1.  `settings_manager.load_settings()`
2.  `settings_manager.init_window_settings()` (サイズ/タイトル/アイコンを設定)
3.  ... 各マネージャー初期化 ...
4.  `setup_ui()` (レイアウト構築)
5.  `show()`

**新しい順序:**
1.  `settings_manager.load_settings()`
2.  ... 各マネージャー初期化 ...
3.  `setup_ui()`
4.  `settings_manager.init_window_settings()` (サイズ/タイトル/アイコンを最後に設定し、レイアウトデフォルトを上書き)
5.  `show()`

これにより、380x700 への明示的なリサイズがウィンドウ表示前の最終的なコマンドとなることを保証する。

## 検証
- アプリケーションを再起動する。
- ウィンドウが視覚的なサイズ変動（グリッチ）なしで、即座に正しいサイズ (380x700) で表示されることを確認する。

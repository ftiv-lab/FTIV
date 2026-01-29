# Phase 3: 設定ロジックの分離計画

## 目的
グローバルな設定管理（`AppSettings`, `OverlaySettings` と関連UIロジック）を `MainWindow` から抽出し、新しい `SettingsManager` クラスに移動する。

## 新規コンポーネント: `managers/settings_manager.py` (SettingsManager)
このクラスは以下を担当する:
1.  **設定のロード/保存**: `load_app_settings`, `save_app_settings`, `load_overlay_settings`, `save_overlay_settings` のラッパー。
2.  **アプリ状態管理**: `toggle_main_frontmost`（最前面トグル）、ウィンドウフラグの操作。
3.  **パフォーマンス設定**: `apply_performance_settings`（各ウィンドウへの設定配布）。
4.  **オーバーレイ設定**: `apply_overlay_settings_to_all_windows`。

## 変更案

### 1. `managers/settings_manager.py` の作成
```python
class SettingsManager:
    def __init__(self, main_window):
        self.mw = main_window
        # 設定オブジェクトの参照を保持
        self.app_settings = None
        self.overlay_settings = None

    def load_settings(self):
        # _init_paths / __init__ から移行
        from utils.app_settings import load_app_settings
        from utils.overlay_settings import load_overlay_settings
        # ... ロジック ...

    def save_app_settings(self): ...
    def save_overlay_settings(self): ...

    def toggle_main_frontmost(self):
        # 移行ロジック
        pass

    def update_frontmost_button_style(self):
        # 移行ロジック
        pass

    def apply_performance_settings(self, debounce, wheel, cache):
        # 各ウィンドウへ設定を配布するロジック
        pass

    def apply_overlay_settings_to_all_windows(self):
        # 移行ロジック
        pass
```

### 2. `ui/main_window.py` のリファクタリング
*   `__init__` で `self.settings_manager = SettingsManager(self)` を初期化する。
*   `self.app_settings` と `self.overlay_settings` へのアクセスを `self.settings_manager.app_settings` に委譲する（または、リファクタリングの影響範囲を抑えるためプロパティ経由でアクセスさせる）。
    *   **決定**: ロジックメソッドを移動する。`MainWindow` が他のタブ等で頻繁に `self.app_settings` を参照している場合、`SettingsManager` がインスタンスを所有し、`MainWindow` はプロパティまたは `self.settings_manager.app_settings` 経由でアクセスする。

### 3. 他ファイルへの影響
*   `GeneralTab` などが `self.mw.app_settings` を参照している場合、`self.mw.settings_manager.app_settings` に更新するか、`MainWindow` 側にプロパティを作成して委譲する。
*   **戦略**: 修正コストとリスクを下げるため、`MainWindow` にプロパティを追加するのが最も安全である:
    ```python
    @property
    def app_settings(self):
        return self.settings_manager.app_settings
    ```

## 移行対象メソッド
*   `_init_window_settings` (部分または全部)
*   `toggle_main_frontmost`
*   `update_main_frontmost_button_style`
*   `apply_performance_settings`
*   `apply_overlay_settings_to_all_windows`

## 検証
1.  メインウィンドウの「最前面固定」トグルを確認。
2.  パフォーマンス設定（遅延時間など）の適用を確認。
3.  「オーバーレイ設定を適用」ボタンの動作を確認。
4.  設定の永続化（アプリ再起動での保持）を確認。

# Phase 9: Event Handling Separation & Controller Pattern Implementation

Phase 8 で品質基盤（型安全・テスト）が整いました。Phase 9 では、`MainWindow` に残っている「コントローラー的責務（イベントハンドリング、シグナル接続の接着剤）」を分離し、**MVC (Model-View-Controller)** パターンの "Controller" を本格導入します。

## Goal
`MainWindow` (View) からイベント処理ロジックを `MainController` (Controller) へ移動し、`MainWindow` を純粋な UI コンテナ（View）に近づける。

## User Review Required
> [!NOTE]
> これにより `MainWindow` のコード行数が削減され、ロジックの見通しが良くなります。既存機能への影響が出ないよう、段階的に移行します。

## Proposed Changes

### 1. New Controller: `MainController`
`ui/controllers/main_controller.py` を新規作成し、以下の責務を持たせます。
*   **初期化フロー制御**: アプリ起動時の設定適用など。
*   **シグナル接続の統括**: `WindowManager` (Model) と `MainWindow`/`PropertyPanel` (View) の間のシグナル接続を管理。
*   **アプリレベルイベント**: `ApplicationState` (Active/Inactive) の変更処理など。

### 2. Refactoring `MainWindow`
`ui/main_window.py` から以下のロジックを削除・委譲します。
*   `handle_app_state_change`: コントローラーへ移動。
*   `on_manager_selection_changed`: コントローラーが仲介。
*   `on_request_property_panel`: コントローラーが仲介。
*   `_legacy_connect_window_signals`: 完全削除（もし残っていれば）。

### 3. Dependency Injection
`MainWindow` の `__init__` で `MainController` をインスタンス化し、自身 (`self`) と `WindowManager` を渡して制御を委ねます。

#### [NEW] ui/controllers/main_controller.py
```python
class MainController:
    def __init__(self, main_window: "MainWindow", window_manager: "WindowManager"):
        self.view = main_window
        self.model = window_manager
        
    def setup_connections(self):
        # WindowManager のシグナルを View に繋ぐ
        self.model.sig_selection_changed.connect(self._on_selection_changed)
        # ...

    def _on_selection_changed(self, window):
        # PropertyPanel の更新ロジック
        self.view.property_panel.update_target(window)
```

## Verification Plan

### Automated Tests
*   `tests/test_main_controller.py` を作成し、シグナル受信時に View のメソッドが呼ばれるかを Mock で検証する。

### Manual Verification
*   アプリを起動し、ウィンドウ選択時にプロパティパネルが正しく切り替わるか確認。
*   アプリのフォーカス切り替え（Active/Inactive）時にオーバーレイのスタイル変更が追従するか確認。

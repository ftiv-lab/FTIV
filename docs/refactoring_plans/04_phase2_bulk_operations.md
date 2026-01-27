# Phase 2: 一括操作ロジックの分離計画

## 目的
`MainWindow` から一括操作ロジック（すべてのウィンドウやそのグループに対する操作）を抽出し、新しい `BulkOperationManager` クラスに移動する。これにより、`MainWindow` の責任範囲とコードサイズを引き続き削減する。

## 新規コンポーネント: `managers/bulk_manager.py` (BulkOperationManager)
このクラスは以下を担当する:
1.  **全体的な表示操作** (すべて表示/非表示)
2.  **全体的なライフサイクル操作** (すべて閉じる)
3.  **一括プロパティ操作** (フォント一括変更、縦書き/横書き一括設定など)

`MainWindow` から `window_manager` または `text_windows`/`image_windows` リストへのアクセスが必要となる（`window_manager` 経由または直接アクセス）。

## 変更案

### 1. `managers/bulk_manager.py` の作成
```python
class BulkOperationManager:
    def __init__(self, main_window):
        self.mw = main_window

    # --- 表示 & ライフサイクル ---
    def show_all_everything(self): ...
    def hide_all_everything(self): ...
    def stop_all_animations(self): ... # AnimationManagerにもあるため、重複を確認
    def close_all_everything(self): ...
    
    # --- テキスト一括操作 ---
    def disable_all_click_through(self): ...
    def close_all_text_windows(self): ...
    def show_all_text_windows(self): ...
    def hide_all_text_windows(self): ...
    def toggle_text_click_through(self): ...
    def toggle_all_frontmost_text_windows(self): ...
    
    # --- スタイル操作 ---
    def change_all_fonts(self): ... 
    def set_all_text_vertical(self): ...
    def set_all_text_horizontal(self): ...
    def set_all_offset_mode_a(self): ...
    def set_all_offset_mode_b(self): ...
    def set_default_text_spacing(self): ...
```

### 2. `ui/main_window.py` のリファクタリング
*   `__init__` で `self.bulk_manager = BulkOperationManager(self)` を初期化する。
*   特定されたメソッド類を削除する。
*   シグナル接続先を `self.bulk_manager.method_name` に更新する。

## 移行対象メソッド
`ui/main_window.py` の 670行目 - 771行目付近:
- `show_all_everything`
- `hide_all_everything`
- `stop_all_animations` -> **注記**: `AnimationManager` にも既に `stop_all_animations` がある。`MainWindow.stop_all_animations` が冗長かファサードか確認する。冗長なら削除し `AnimationManager` を使う。
- `close_all_everything`
- `disable_all_click_through`
- `add_text_window` (維持？ 単体操作だが、WindowManagerラッパーに入れるべきか) -> **実装段階では維持、または別コントローラへ。**
- `add_related_text_window` -> **維持または移動。**
- `close_all_text_windows`
- `show_all_text_windows`
- `hide_all_text_windows`
- `toggle_text_click_through`
- `toggle_all_frontmost_text_windows`
- `stop_all_text_animations` -> **AnimationManager または WindowManager を使用。**
- `change_all_fonts`
- `set_all_text_vertical`
- `set_all_text_horizontal`
- `set_all_offset_mode_a`
- `set_all_offset_mode_b`

## 検証
1.  ツールバー/メニューの「すべて表示/非表示/閉じる」ボタンが機能することを確認。
2.  「フォント一括変更」ダイアログが機能し、全ウィンドウに適用されることを確認。
3.  全ウィンドウに対する縦書き/横書きトグルを確認。

## 補足: `stop_all_animations`
Phase 1 で `AnimationManager.stop_all_animations` を作成済み。`MainWindow.stop_all_animations` (L678) は現在 `window_manager` に委譲している。これを統一すべき。`AnimationManager` が高レベルなアニメーション停止の責務を持つのが適切。ロジックの重複を避ける。

## 補足: Undo Stack
`change_all_fonts` は `self.undo_stack` を使用している。`BulkOperationManager` は `self.mw.undo_stack` へのアクセスが必要。

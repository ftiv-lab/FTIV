# Phase 11 (Resumed) 実装計画書 - 最終的な疎結合化 (Final Logic Decoupling)

## 目標概要 (Goal Description)
Nuitka と Python 3.13 ビルドパイプラインの統合成功を受け、`MainWindow` のリファクタリングを再開します。
目標は、`MainWindow` に残っているビジネスロジックを、専用の Action Controllers (`ImageActions`, `SceneActions`) に移動し、完全な「関心の分離 (Separation of Concerns)」を達成することです。

## ユーザーレビュー事項 (User Review Required)
> [!NOTE]
> エンドユーザー向けの破壊的変更はありません。内部リファクタリングのみです。
> `pyproject.toml` は `.venv313` と `dist_test` を除外するように更新されました。

## 変更内容 (Proposed Changes)

### 画像ロジックの分離 (Image Logic Decoupling)
#### [MODIFY] [image_actions.py](file:///o:/Tkinter用/FTIV/ui/controllers/image_actions.py)
- [x] `pack_all_left_top(screen_index, space)` の実装
- [x] `pack_all_center(screen_index, space)` の実装
- [x] ロジックは `self.mw.window_manager.image_windows` と標準の `QApplication.screens()` を使用
- [x] `undo_stack` の使用確認

#### [MODIFY] [main_window.py](file:///o:/Tkinter用/FTIV/ui/main_window.py)
- [x] `img_pack_all_left_top` を `self.img_actions.pack_all_left_top` への委譲に変更
- [x] `img_pack_all_center` を `self.img_actions.pack_all_center` への委譲に変更
- [x] 元の約150行の整列ロジックを削除

### シーンロジックの分離 (Scene Logic Decoupling)
#### [VERIFY] [scene_actions.py](file:///o:/Tkinter用/FTIV/ui/controllers/scene_actions.py)
- [x] `add_new_category`, `add_new_scene`, `load_selected_scene`, `update_selected_scene`, `delete_selected_item` が実装されていることを確認
- [x] UI更新が `scene_tab` コールバック経由で処理されることを確認

#### [MODIFY] [main_window.py](file:///o:/Tkinter用/FTIV/ui/main_window.py)
- [x] `add_new_category` -> `self.scene_actions.add_new_category()`
- [x] `add_new_scene` -> `self.scene_actions.add_new_scene()`
- [x] `load_selected_scene` -> `self.scene_actions.load_selected_scene()`
- [x] `update_selected_scene` -> `self.scene_actions.update_selected_scene()`
- [x] `delete_selected_item` -> `self.scene_actions.delete_selected_item()`
- [x] 元のロジック削除（不要な `QInputDialog` インポート削除含む）

## 検証計画 (Verification Plan)

### 自動テスト (Automated Tests)
- [x] `verify_all.bat` の実行
    - Linter が通過すること（MainWindowの不要インポート修正）
    - 既存テストが通過すること（インスタンス化のリグレッションなし）

### 手動検証 (Manual Verification)
- [ ] アプリ起動 (`python main.py`)
- [ ] "Arrangement" > "Pack Left-Top" / "Pack Center" を画像タブでテスト（画像移動確認）
- [ ] "Scene" > "Add Category", "Add Scene", "Save/Load" をテスト（DB連携確認）

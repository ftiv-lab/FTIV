# リファクタリング計画 03: ロジックとビューの完全分離

## 目的
Antigravity プログラミング・スタンダードの「Logic & View Separation」に基づき、`MainWindow` や各 `Tab` クラスに残存しているビジネスロジックを、独立した「Controller」または「Manager」クラスに分離する。
マルチウィンドウ同期、設定適用、一括編集などのロジックをUIから切り離す。

## 現状の課題
`MainWindow` 内に以下のロジックが残存している：
1.  **アニメーション同期**: `_anim_sync_from_selected`, `_anim_apply_offset` など。
2.  **一括操作**: `change_all_fonts`, `set_all_image_opacity` など。
3.  **設定適用**: `AboutTab` 内のパフォーマンス設定ロジック。

## リファクタリング計画

### Phase 1: アニメーションロジックの分離 (AnimationManager)
- **作成**: `managers/animation_manager.py`
    - アニメーションパラメータの同期、適用、一括停止などのロジックを集約。
- **修正**:
    - `MainWindow` から `_anim_*` メソッドを削除。
    - `AnimationTab` は `AnimationManager` を介して操作を行う。

### Phase 2: 一括操作ロジックの分離 (BulkOperationManager)
- **作成**: `managers/bulk_manager.py`
    - `change_all_fonts`, `set_all_opacity` などの全ウィンドウ操作を集約。
- **修正**:
    - `MainWindow` の対応メソッドを削除し、メニュー/ショートカットから `BulkOperationManager` を呼ぶ。

### Phase 3: 設定ロジックの分離 (SettingsManager)
- **作成**: `managers/settings_manager.py`
    - 設定の読み込み・保存・適用ロジックを集約。
- **修正**:
    - `AboutTab`, `GeneralTab` から直接の設定変更ロジックを排除。

## メリット
- ロジックの単体テストが可能になる。
- UIコードの肥大化を防ぎ、可読性を向上させる。

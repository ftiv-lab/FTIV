# Phase 6: ビジネスロジックの抽出 (Business Logic Extraction)

## 概要
Phase 5 までで、`MainWindow` は UIコンポーネントの直接操作から解放されました。しかし、依然として「画像の整列計算」や「一括プロパティ変更」などの **ビジネスロジック** が `MainWindow` クラス内に実装されています。
本フェーズでは、これらのロジックを適切な Controller や Manager クラスに移動し、`MainWindow` を真に「UI構築とイベントの配線」のみを行うクラスに昇華させます。

## 目標
1. **レイアウトロジックの分離**: 画像の整列（Pack Left-Top, Center, Grid）を行う計算ロジックを分離する。
2. **一括操作ロジックの分離**: 全画像の不透明度変更、全コネクタの色変更などの一括操作を Controller に移動する。
3. **MainWindow の軽量化**: コード行数を削減し、見通しを良くする。

## 実施計画

### 1. レイアウトロジックの移動
`MainWindow` にある以下のメソッド群を、新しいクラス `LayoutManager` (または `ImageUtil` / `ImageActions`) に移動します。
今回は `managers/layout_manager.py` を新規作成するか、既存の `ImageActions` を拡張するかを検討します。
-> 状態を持たない計算ロジックが大半であるため、`ui/controllers/image_actions.py` または `managers/layout_calculator.py` への移動が妥当ですが、`ImageActions` はUI操作コントローラとしての役割が強いため、純粋な配置計算は切り出した方が疎結合になります。
-> **方針**: `ui/controllers/layout_actions.py` (新規) を作成し、そこに移動します。

- **移動対象**:
    - `img_pack_all_left_top`
    - `img_pack_all_center`
    - `align_images_on_multiple_displays` (グリッド整列)
    - `normalize_all_images_by_selected` (これは既に `ImageActions` にあるか確認)

### 2. コネクタ一括操作の移動
`MainWindow` にある以下のメソッドを `ui/controllers/connector_actions.py` へ移動します。

- **移動対象**:
    - `change_all_connector_colors`
    - `change_all_connector_widths`
    - `change_all_connector_opacities`

### 3. 画像一括操作の移動
`MainWindow` にある以下のメソッドを `ui/controllers/image_actions.py` へ移動します。

- **移動対象**:
    - `set_all_image_opacity`
    - `set_all_image_opacity_realtime`
    - `set_all_image_size_percentage`
    - `set_all_image_size_realtime`
    - `set_all_image_rotation`
    - `set_all_image_rotation_realtime`
    - `reset_all_flips`
    - `reset_all_animation_speeds`
    - `toggle_all_image_animation_speed`
    - `stop_all_image_animations`
    - `set_all_gif_apng_playback_speed`

## 作業手順

1. **`ui/controllers/layout_actions.py` の作成**: レイアウト計算ロジックを実装。
2. **`ui/controllers/connector_actions.py` の拡張**: 一括コネクタ操作メソッドを移植。
3. **`ui/controllers/image_actions.py` の拡張**: 一括画像操作メソッドを移植。
4. **`MainWindow` の修正**:
    - 移植したメソッドを削除。
    - メニューやボタンからの呼び出し先を、各 `actions` インスタンスのメソッドに変更。
    - `setup_ui` や `_build_main_tabs` でのアクション接続先を更新。

## 検証
- 画像の自動整列機能が以前と同様に動作するか。
- コネクタの一括色変更などが機能するか。
- 画像の一括サイズ変更などが機能するか。

---
**Status**: Planning

# controllers Package (ui/controllers)

`ui/controllers` パッケージは、`MainWindow` から分離された「ビジネスロジック」や「一括操作（Batch Operations）」を担当するクラス群です。
これらは純粋なロジックに近い責務を持ちますが、QtのAPI（`QWidget.move`, `QPainterPath`等）を操作するため、`ui` 配下に配置されています。

## クラス構成

### `LayoutActions` (`ui/controllers/layout_actions.py`)
画像の配置・整列ロジックを担当します。
- **責務**:
    - `pack_all_left_top`: 全画像を左上詰めで配置。
    - `pack_all_center`: 全画像を中央に集める。
    - `align_images_grid`: 指定列数・間隔でグリッド整列。
- **依存関係**: `MainWindow` (ウィンドウリスト取得用), `ImageWindow` (移動対象)

### `ImageActions` (`ui/controllers/image_actions.py`)
複数の画像ウィンドウに対する一括操作、および単一画像選択時の複雑なアクションを担当します。
- **責務**:
    - `set_all_image_opacity/size/rotation`: 全画像の一括変更。
    - `fit_selected_to_display`: 選択画像のディスプレイフィット。
    - `run_selected_visibility_action`: 選択画像の表示/非表示/前面トグル。
- **依存関係**: `MainWindow` (選択状態管理), `WindowManager` (ウィンドウリスト), `ImageWindow`

### `ConnectorActions` (`ui/controllers/connector_actions.py`)
コネクタ（`ConnectorLine`, `ConnectorLabel`）に関する操作を担当します。
- **責務**:
    - `bulk_change_color/width/opacity`: 全コネクタの一括変更。
    - `delete_selected`: 選択中コネクタの削除。
    - `set_arrow_style_selected`: 矢印スタイルの変更。
- **依存関係**: `MainWindow` (選択状態管理), `ConnectorLine`

## 設計方針
- **Strict Type Safety**: すべての引数・戻り値に型ヒントを記述し、循環参照は `TYPE_CHECKING` で回避しています。
- **MainWindowへの依存**: コンストラクタで `mw: MainWindow` を受け取りますが、UIウィジェット自体（ボタン等）を直接操作することは避け、状態（`last_selected_window` 等）やマネージャー経由での操作を原則とします。

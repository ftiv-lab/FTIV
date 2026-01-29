# FTIV Codebase Documentation: `ui/controllers` Package (詳細版)

このドキュメントは `ui/controllers` パッケージ内のアクションクラス群の詳細仕様を解説するものです。
これらは `MainWindow` の巨大化を防ぐために、機能単位（テキスト、画像、接続）でロジックを分離したコントローラー群です。

各クラスは `MainWindow` インスタンスを `self.mw` として保持し、そこから `WindowManager` や UI状態にアクセスする設計となっています。

## 1. `ui/controllers/text_actions.py`

### クラス: `TextActions`

`TextWindow` および `ConnectorLabel` に対する操作を担当します。

#### クラス構成
*   **初期化**: `__init__(self, mw)` - `MainWindow` のリファレンスを保持。
*   **ユーティリティ**:
    *   `_get_selected_obj()`: 現在選択されているウィンドウ（`mw.last_selected_window`）を取得。
    *   `_is_text_window(obj)`: オブジェクトが `TextWindow` か判定（`ConnectorLabel` は含まない）。
    *   `_is_text_like(obj)`: オブジェクトが `TextWindow` または `ConnectorLabel` か判定。

#### アクションメソッド
これらは主にメインメニューやツールバー、ショートカットキーから呼び出されます。

*   **`clone_selected()`**
    選択中の `TextWindow` を複製します。`ConnectorLabel` はコネクタの一部であるため複製対象外としてガードしています。

*   **`save_selected_to_json()`**
    選択中のオブジェクトのプロパティを単独の JSON ファイルとしてエクスポートします。

*   **`save_png_selected()`**
    選択中の `TextWindow` の描画内容を PNG 画像として保存します（背景透過）。

*   **`run_selected_visibility_action(action: str, checked: bool = None)`**
    表示状態を操作します。
    *   `action`: "show", "hide", "frontmost" (最前面固定), "click_through" (クリック透過), "close"。
    *   UIのチェックボックスと連動する場合、`checked` で明示的な状態指定が可能です。

*   **`run_selected_layout_action(action: str, checked: bool = None)`**
    レイアウトやスタイル設定を操作します。
    *   `set_vertical`: 縦書きモードの ON/OFF。
    *   `set_offset_mode_mono`: 縦書き時の等幅フォント用配置モード (Type A)。
    *   `set_offset_mode_prop`: 縦書き時のプロポーショナルフォント用配置モード (Type B)。
    *   `open_spacing_settings`: マージン設定ダイアログを開く。

*   **一括操作系 (Others Action)**
    選択中のウィンドウ以外に対する操作です。
    *   `hide_other_text_windows()`: 自分以外を隠す。
    *   `show_other_text_windows()`: 自分以外を表示する。
    *   `close_other_text_windows()`: 自分以外を閉じる。

---

## 2. `ui/controllers/image_actions.py`

### クラス: `ImageActions`

`ImageWindow` に対する操作を担当します。

#### クラス構成
*   **初期化**: `__init__(self, mw)`
*   **ユーティリティ**: `_get_selected_image()` - 現在選択中の `ImageWindow` を取得（型チェック付き）。

#### アクションメソッド

*   **`run_selected_transform_action(action: str)`**
    変形ダイアログを表示します。
    *   "size": サイズ変更ダイアログ。
    *   "opacity": 不透明度ダイアログ。
    *   "rotation": 回転角度ダイアログ。

*   **`run_selected_visibility_action(action: str, checked: bool = None)`**
    表示状態操作。
    *   "show", "hide", "frontmost", "click_through" に加え、画像の各種トグル機能に対応。

*   **`run_selected_playback_action(action: str)`**
    GIF/APNGアニメーション操作。
    *   "toggle": 再生/一時停止。
    *   "speed": 再生速度調整ダイアログ。
    *   "reset": 標準速度に戻す。

*   **`run_selected_manage_action(action: str)`**
    管理系操作。
    *   "reselect": 画像ファイルの再読み込み/変更。
    *   "clone": 画像ウィンドウの複製。
    *   "save_json": 設定のエクスポート。

*   **ディスプレイ関連 (Multi-Monitor Support)**
    *   `fit_selected_to_display(screen_index)`: 指定画面サイズに合わせて拡大縮小。
    *   `center_selected_on_display(screen_index)`: 指定画面の中央へ移動。
    *   `snap_selected_to_display_edge(screen_index, edge)`: 上下左右の端へスナップ。
    *   `snap_selected_to_display_corner(screen_index, corner)`: 四隅へスナップ。

*   **`normalize_all_images_by_selected(mode: str)`**
    正規化機能。選択中の画像を基準に、他の全画像のスケールを調整します。
    *   "same_pct": 倍率を統一。
    *   "same_width": 見た目の幅を統一。
    *   "same_height": 見た目の高さを統一。

*   **`flip_selected(axis: str)`**, **`set_selected_rotation_angle(angle)`**, **`reset_selected_transform(kind)`**
    反転、回転指定、各種リセット機能を提供します。

---


---

## 3. `ui/controllers/connector_actions.py`

### クラス: `ConnectorActions`

`ConnectorLine`（およびその付属の `ConnectorLabel`）に対する操作を担当します。
選択中のコネクタだけでなく、一括変更（Bulk Change）機能も持ちます。

#### クラス構成
*   **初期化**: `__init__(self, mw)`
*   **ユーティリティ**:
    *   `_get_selected_line()`: 選択中のコネクタを取得。`mw.last_selected_connector` または `mw.last_selected_window` （コネクタの場合）から解決。
    *   `_get_all_lines()`: シーン内の全コネクタを取得。

#### アクションメソッド（選択中対象）

*   **`delete_selected()`**: 選択中のコネクタを削除。
*   **`change_color_selected()`**: カラーダイアログを開いて色を変更。
*   **`open_width_dialog_selected()`**: 線幅調整ダイアログ（`PreviewCommitDialog`）を開く。スライダー操作中のプレビューが可能。
*   **`open_opacity_dialog_selected()`**: 不透明度調整ダイアログを開く。
*   **`set_arrow_style_selected(style_key)`**: 矢印の形状（なし/始点/終点/両端）を変更。

*   **`label_action_selected(action)`**
    コネクタ上のラベルに対する操作。
    *   "edit": ラベルを編集モードにする（非表示なら表示する）。
    *   "toggle": ラベルの表示/非表示（実体はテキストを空にする処理）をトグル。

#### アクションメソッド（一括操作）

*   **`bulk_change_color()`**: 全コネクタの色を統一。
*   **`bulk_open_width_dialog()`**: 全コネクタの太さを統一。
*   **`bulk_open_opacity_dialog()`**: 全コネクタの不透明度を統一。

#### 実装上の特徴
*   **Undo/Redo対応**: ダイアログからの変更時、`undo_stack` にマクロとして登録し、キャンセル可能にしています。
*   **エラーハンドリング**: `report_unexpected_error` を使用し、操作中の例外を安全にキャッチしてユーザーに通知します。
*   **UI同期**: アクション実行後、`MainWindow` 側の `_conn_on_selection_changed` などを呼び出して、ボタンの有効/無効状態などを即座に更新しています。

---

## 4. `ui/controllers/scene_actions.py` (Phase 11 追加)

### クラス: `SceneActions`

シーンおよびカテゴリのCRUD（作成・読み込み・更新・削除）操作を担当します。
`DataManager` (FileManager) と UI (SceneTab) の橋渡し役です。

#### アクションメソッド

*   **`add_new_category()`**: 新規カテゴリ作成ダイアログを表示・保存。
*   **`add_new_scene()`**: 選択中カテゴリに新規シーンを保存。
*   **`load_selected_scene()`**: 選択中シーンのデータをロードし、画面全体を復元。
*   **`update_selected_scene()`**: 現在の画面状態で選択中シーンを上書き保存。
*   **`delete_selected_item()`**: 選択中のシーンまたはカテゴリを削除（確認ダイアログ付き）。

---

## 5. `ui/controllers/main_controller.py` (Phase 9 追加)

### 概要
`MainWindow` と各 `Actions/Managers` の間の「接着剤」および「中央管制塔」として機能します。UIの信号 (Signals) を受け取り、適切なアクションやモデルのメソッドへとルーティングします。

### クラス: `MainController`

#### 主な責務
*   **シグナル結線 (`setup_connections`)**: `MainWindow` 上のボタン、メニュー、ショートカットキーの信号を一斉に各 Actions (Text, Image, etc.) へ接続。
*   **状態管理 (`handle_app_state_change`)**: OS のアプリケーション状態（アクティブ/非アクティブ）を監視し、オーバーレイの表示/隠蔽を統括。
*   **セレクション連携**: `WindowManager` の選択変更シグナルを受け取り、アクティブなタブ（TextTab, ImageTab 等）の UI 更新メソッドをキック。

#### 実装上の特徴
*   **疎結合化**: `MainWindow` からイベントハンドリングロジックを分離することで、UI 定義とボタンの挙動を切り離します。

---

## 6. 品質保証ツール (`tools/`)

### `tools/check_ui_refs.py`
**静的解析監査ツール**。
`managers/` や `ui/controllers/` から `self.mw.btn_xxx` のように、`MainWindow` の UI 部品に「直接触れている」箇所を検出します。
原則として UI へのアクセスは「各 Tab クラス」を介して行うべきというルールを強制するためのバリデーターです。

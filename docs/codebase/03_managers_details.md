# FTIV Codebase Documentation: `managers` Package (詳細版)

このドキュメントは `managers` パッケージ内の各ファイル、クラスの**完全な詳細仕様**を解説するものです。
アプリ全体のコアロジック（ウィンドウ管理、ファイル永続化、プリセット管理）を担当する重要な部分です。

---

## 1. `managers/window_manager.py`

### 概要
シーン内の全オブジェクト（`TextWindow`, `ImageWindow`, `ConnectorLine`）の**ライフサイクル**（生成・削除・管理）を一元管理します。
`MainWindow` の役割を軽量化し、ビジネスロジックを分離するために設計されています。

### クラス: `WindowManager(QObject)`

#### データ構造 (`data containers`)
`WindowManager` のインスタンス変数がアプリ内の全実体データの「正 (Source of Truth)」となります。
*   `self.text_windows: List[TextWindow]`
*   `self.image_windows: List[ImageWindow]`
*   `self.connectors: List[ConnectorLine]`
*   `self.last_selected_window: Optional[QObject]`: 現在選択されているオブジェクト（フォーカス）。
*   `self.main_window`: 親となる `MainWindow` インスタンス。シグナル接続やダイアログ表示に使用。

#### シグナル
*   `sig_selection_changed(object)`: 選択ウィンドウが切り替わった時に発行。UI更新用。
*   `sig_status_message(str)`: ステータスバーにメッセージを表示したい時に発行。
*   `sig_undo_command_requested(object)`: コマンド（`QUndoCommand`）が発行された時にメインウィンドウのスタックへ転送するためのシグナル。

---

### メソッド詳細: 生成 (Creation)

#### `add_text_window(text=None, pos=None, suppress_limit_message=False) -> Optional[TextWindow]`
*   **制限チェック**: FREE版の個数制限 (`utils.edition.get_limits`) をチェックし、超過時はメッセージを出して `None` を返します。
*   **生成**: `TextWindow(main_window, text, pos)` をインスタンス化。
*   **セットアップ**:
    1.  `_setup_window_connections(window)` でシグナルを結線。
    2.  `text_windows` リストに追加。
    3.  `window.show()` で表示。
    4.  `set_selected_window(window)` で選択状態にする。

#### `add_image_window(...)`
*   同様のプロセスで `ImageWindow` を生成します。
*   例外発生時は `traceback` をログに出力し、`QMessageBox` でユーザーに通知します（画像読み込み失敗など）。

#### `add_connector(start_window, end_window) -> Optional[ConnectorLine]`
*   **重複チェック**: 既に同じペアのコネクタが存在する場合、警告ログを出して生成しません。
*   **生成**: `ConnectorLine` を生成し、リストに追加。
*   **双方登録**: `start_window.connected_lines` と `end_window.connected_lines` の両方に自身を追加します。

#### `_setup_window_connections(window)`
生成されたウィンドウからのシグナルをマネージャーやメインウィンドウのスロットに接続します。
*   `safe_connect` ヘルパーを使用し、ウィンドウクラスに属性（シグナル）が存在しない場合でもエラーにせず無視する「ダックタイピング的」な安全設計となっています。
*   **接続イベント例**: 選択、閉じる、Undo要求、クローン、スタイル保存、ナビゲーション、プロパティ変更通知など。

---

### メソッド詳細: 削除 (Removal)

#### `remove_window(window: Any) -> None`
ウィンドウを安全に削除し、関連リソースをクリーンアップします。
1.  **親子関係の解除**:
    *   自分が子の場合: 親から自分を登録解除。
    *   自分が親の場合: 子ウィンドウの `parent_window_uuid` を `None` に設定（孤児化）。
2.  **リストからの除去**: `text_windows` または `image_windows` から削除。
3.  **選択解除**: 自分が選択されていたら解除。
4.  **コネクタ削除**: 自分に接続されているコネクタがあれば `delete_connector` で削除。
5.  **ログ出力**: UUIDとともに削除完了を記録。

#### `delete_connector(connector: Any) -> None`
コネクタを削除する際の**正規ルート**です。
1.  **即時隠蔽**: `hide()` を呼んで画面から消す。
2.  **参照解除 (`remove_connector`)**: 内部リストやウィンドウの接続リストから参照を消す。
3.  **遅延破棄**: `QTimer.singleShot(0, ...)` を使い、イベントループの最後で `close()` を呼ぶ。
    *   **理由**: 同期処理中に `close()` すると、Qt内部でまだイベント処理中のポインタが不正になりクラッシュすることがあるため（特にマウスイベント中の削除）。

---

### メソッド詳細: ロジック・操作

#### `set_selected_window(window)`
選択対象を切り替えます。
*   旧選択ウィンドウの `set_selected(False)` を呼ぶ。
*   新ウィンドウの `set_selected(True)` を呼び、`raise_()` で最前面に出す。
*   この直後 `sig_selection_changed` を発行。
*   **`_prune_invalid_refs` の実行**: 選択切り替えのタイミングで、定期的に無効なオブジェクト参照（C++側で削除済み）をリストから除去します。

#### `clone_text_window(source) / clone_image_window(source)`
既存ウィンドウを複製します。
*   **Configコピー**: Pydanticの `model_dump` でデータを辞書化し、新しいウィンドウの config に流し込みます。
    *   UUIDなどの個体識別子は除外 (`exclude`)。
*   **イージング/アニメ**: 保存された設定に基づいて再開 (`_resume_window_animations`)。
*   **画像ウィンドウ**: 可能な場合、読み込み済みの `frames`（アニメーションGIFのコマ）をメモリコピーしてロード時間を短縮する最適化が入っています。

#### `create_related_node(source_window, relation_type="child"|"sibling")`
マインドマップ操作用。
*   現在のウィンドウの隣（子なら右下、兄弟なら下など）に新しいノードを生成し、自動的にコネクタで接続してグループ化します。

#### `clear_all()`
全てのウィンドウとコネクタを削除します（File -> New 相当）。
*   まずコネクタを全削除し、次にウィンドウを削除することで、依存関係の問題を防ぎます。

---

## 2. `managers/file_manager.py`

### 概要
データの保存・読み込み（シリアライズ/デシリアライズ）を担当します。`WindowManager` のデータを JSON に変換したり、逆に JSON からオブジェクトを復元します。

### クラス: `FileManager`

#### メソッド詳細: シリアライズ (保存)

#### `get_scene_data() -> Dict`
現在のアプリ状態を辞書データとして出力します。
*   **フォーマット**: `format_version: 1`
*   `windows`: 各ウィンドウの config をダンプしたリスト。
*   `connections`: コネクタ情報（from_uuid, to_uuid, 色, 線種, 矢印設定, ラベルデータ）のリスト。

#### `_save_json_atomic(path, data)`
**実装上の重要ポイント**。
*   ファイル保存時の破損を防ぐため、以下の手順を踏みます（Atomic Save）。
    1.  `path + ".tmp"` という一時ファイルに書き込む。
    2.  `os.replace(temp, final)` でアトミックに差し替える。
    *   これにより、書き込み中の電源断やクラッシュが発生しても、元のファイルは無傷で残ります。

#### `save_window_to_json(window)`
単一ウィンドウの設定をエクスポートします。
*   ファイル名のサニタイズ処理（OS使用禁止文字の除去）が含まれています。

---

#### メソッド詳細: デシリアライズ (読み込み)

#### `load_scene_from_data(data)`
辞書データからシーン全体を復元します。
1.  **正規化 (`_normalize_scene_data`)**: 旧バージョン（v0.9以前）のデータ構造や、プロジェクト形式のデータを読み取れる形式（v1.0 Scene形式）に変換します。
2.  **全クリア**: 既存のウィンドウを消去。
3.  **ウィンドウ生成**: `create_text_window_from_data` / `create_image_window_from_data` を呼び出して実体化。
    *   UUIDをキーにした辞書マップを作成。
4.  **親子関係復元**: `parent_uuid` を見て再リンク。
5.  **接続復元 (`_restore_connections`)**: UUIDマップを使ってコネクタを再生成。
6.  **描画遅延対策**: 最後に `QTimer` でコネクタの位置更新 (`update_position`) をキックし、ロード直後の線のズレを修正します。

#### `_restore_connections(connections_list)`
*   `from_uuid` と `to_uuid` が現在のシーンに存在する場合のみ線を引きます。
*   コネクタのプロパティ（色、線種、矢印）および**ラベルデータ（TextWindowConfig）**を復元します。

---

## 3. `managers/style_manager.py`

### 概要
テキストスタイルの「プリセット」を管理します。一括適用やサムネイル生成の機能を持ちます。

### クラス: `StyleManager`

#### `save_text_style(window)`
現在のテキスト装飾をプリセットとして保存します。
*   **サムネイル生成**: 実際に `TextWindow` を画面に出すと邪魔になるため、`_TextRenderDummy` というダミーオブジェクトと `TextRenderer` を使ってオフスクリーンレンダリングを行い、PNG画像を生成して保存します。

#### `apply_style_to_text_windows(windows, json_path)`
複数のウィンドウに一括でスタイルを適用します。
*   **Undoマクロ**: `undo_stack.beginMacro` を使い、複数回のアクションを「1回のUndo」で戻せるようにまとめています。
*   **適用除外**: `font_size`, `is_vertical`, `offset_mode` はスタイル適用時に無視されます。これは「スタイル（色や装飾）」だけを変えたいというユーザーの意図を汲むためです（サイズや縦書き設定まで変わるとレイアウトが崩れるため）。

### クラス: `_TextRenderDummy` (内部クラス)
*   `TextRenderer` は `TextWindow` インスタンスを要求しますが、本物のウィンドウを作るコストを避けるため、`TextWindowConfig` を持ったこのダミーを渡して描画させます。
*   `TextWindow` と同じプロパティ（`font_size`, `shadow_enabled` 等）を `property` で公開し、config の値を返します。

---

## 4. `managers/animation_manager.py`

### 概要
アニメーションパラメータ（移動、フェード、イージング）の適用、同期、一括制御を担当します。
`MainWindow` からアニメーション関連の複雑なロジックを分離するために作成されました。

### クラス: `AnimationManager`

#### `apply_move_params(target_type, ...)` / `apply_fade_params(...)`
*   UIから受け取ったパラメータを、選択中のウィンドウ（または全ウィンドウ）に適用します。
*   変更後、即座にアニメーションを再開させ、イージング設定も同時に更新します。

#### `stop_move()` / `stop_fade()`
*   アニメーションの停止制御を行います。
*   `window.stop_animation("move")` などを呼び出し、安全に停止させます。

#### `sync_from_selected(window)`
*   選択されたウィンドウのアニメーション設定を読み取り、UI（AnimationTab）に反映するための値を返します。

---

## 5. `managers/bulk_manager.py`

### 概要
ウィンドウの一括操作（すべて表示/閉じる、スタイル一括変更など）を担当します。

### クラス: `BulkOperationManager`

#### `show_all_everything()` / `hide_all_everything()`
*   テキストウィンドウと画像ウィンドウのすべての表示状態を切り替えます。

#### `change_all_fonts()`
*   フォントダイアログを表示し、選択されたフォントを全テキストウィンドウに適用します。
*   `undo_stack` を使用して、一連の変更を1回の Undo 操作で戻せるようにしています。

#### `set_default_text_spacing()`
*   テキストの間隔設定（パディングなど）をJSONに保存し、現在開いている全ウィンドウにも即時適用します。

---

## 6. `managers/settings_manager.py`

### 概要
アプリケーション全体の設定（`AppSettings`）とオーバーレイ共通設定（`OverlaySettings`）の永続化と適用を担当します。

### クラス: `SettingsManager`

#### `load_settings()`, `save_app_settings()`
*   `utils.app_settings` / `utils.overlay_settings` のロード・セーブ関数のラッパーです。
*   `MainWindow` 起動時に呼ばれ、設定インスタンスを保持します。

#### `toggle_main_frontmost()`
*   メインウィンドウの「最前面固定」フラグを切り替えます。
*   設定変更後、即座に設定ファイルへ保存します。

#### `apply_performance_settings(debounce, ...)`
*   描画デバウンスやキャッシュサイズの設定を、既存の全ウィンドウ（テキスト、コネクタラベル等）に配布・適用します。

---

## 7. `managers/config_guardian.py` (Phase 13 追加)

### 概要
アプリケーション起動時に、環境の「健康診断」と自動修復を行います。設定ファイルの破損による「起動不能」を防ぐための強力なセーフティネットです。

### クラス: `ConfigGuardian`

#### `validate_all() -> bool`
以下の項目を順次チェックし、修復が必要だった場合に `True` を返します。
1.  **JSONディレクトリの存在確認**: なければ作成。
2.  **`settings.json` の構造検証**:
    *   ファイルが存在しない場合はデフォルト設定で新規作成。
    *   JSONとしての文法エラーがある場合は、破損ファイルを `.bak` として保存した上でデフォルト値でリセット。
    *   必須キー (`app_settings`, `overlay_settings`) が欠落している場合もリセット。

#### `get_report_text() -> str`
修復・検知された内容のサマリを返します。`main.py` はこれを受け取り、ユーザーに警告ダイアログを表示します。

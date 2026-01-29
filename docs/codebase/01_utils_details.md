# FTIV Codebase Documentation: `utils` Package (詳細版)

このドキュメントは `utils` パッケージ内の各ファイル、クラス、関数の**完全な詳細仕様**を解説するものです。
開発者がコードリーディングなしに機能や仕様を把握し、外部API連携やリファクタリングに利用できるレベルを目指します。

---

## 1. `utils/app_settings.py`

### 概要
アプリケーション全体の設定（ウィンドウの挙動、パフォーマンス設定など）を管理するクラスと、そのJSON永続化機能を提供します。

### 依存関係
*   標準ライブラリ: `json`, `os`, `dataclasses`
*   プロジェクト内: `utils.paths`, `utils.translator`
*   PySide6: `QMessageBox`

### クラス: `AppSettings`
設定値を保持するデータクラス (`dataclass`)。

#### プロパティ詳細
| プロパティ名 | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `main_window_frontmost` | `bool` | `True` | メインウィンドウ（操作パネル）を常に最前面に表示するかどうか。`MainWindow` の `toggle_main_frontmost` で使用される。 |
| `render_debounce_ms` | `int` | `25` | **テキストレンダリングのデバウンス時間 (ミリ秒)**。<br>フォントサイズ変更などの重い処理を間引き、UI応答性を確保する。小さいほど即応性が高いがCPU負荷が増える。 |
| `wheel_debounce_ms` | `int` | `50` | **マウスホイール操作時のイベント処理デバウンス時間 (ミリ秒)**。<br>連続的なホイールスクロールによる過剰なイベント発火を抑制する。 |
| `glyph_cache_size` | `int` | `512` | **`TextRenderer` で使用するグリフキャッシュのサイズ**。<br>文字の描画パス (`QPainterPath`) をキャッシュする数。大きいほど再描画負荷が下がるがメモリ消費が増える。 |

### 関数

#### `_get_settings_path(base_directory: str) -> str`
*   **引数**:
    *   `base_directory`: アプリの基準ディレクトリ (通常は `utils.paths.get_base_dir()` の値)。
*   **戻り値**: 設定ファイルの絶対パス (例: `.../json/app_settings.json`)。ディレクトリが存在しない場合は自動生成します。

#### `save_app_settings(parent: Any, base_directory: str, settings: AppSettings) -> bool`
*   **機能**: `AppSettings` オブジェクトの内容を JSON ファイルに保存します。
*   **エラー処理**: 保存に失敗した場合、`parent` を親とする `QMessageBox.critical` を表示し、`False` を返します。
*   **保存フォーマット**: `utf-8`, `indent=2`, `ensure_ascii=False` (日本語可読)。

#### `load_app_settings(parent: Any, base_directory: str) -> AppSettings`
*   **機能**: JSON ファイルから設定を読み込み、`AppSettings` オブジェクトを返します。
*   **フォールバック**:
    *   ファイルが存在しない場合: デフォルト値で初期化された `AppSettings` を返します。
    *   JSONキーが欠損している場合: そのフィールドはデフォルト値のまま維持されます。
    *   読み込みエラー時: `QMessageBox.warning` を表示し（サイレントでない）、デフォルト設定を返します。

---

## 2. `utils/commands.py`

### 概要
`QUndoStack` で利用するための `QUndoCommand` サブクラス群を定義しています。これにより「元に戻す (Ctrl+Z) / やり直し (Ctrl+Y)」機能を実現しています。

### 依存関係
*   PySide6: `QUndoCommand`, `QPoint`
*   ライブラリ: `shiboken6` (オブジェクトの有効性チェック用)

### クラス: `PropertyChangeCommand`
汎用的なプロパティ変更コマンドです。

#### コンストラクタ
```python
__init__(self, target, property_name, old_value, new_value, update_method_name=None)
```
*   `target`: 変更対象のオブジェクト (例: `TextWindow` インスタンス)。内部で `shiboken6.isValid(target)` による生存チェックが行われます。
*   `property_name` (str): 変更する属性名 (例: `"font_size"`).
*   `old_value` (Any): 変更前の値。
*   `new_value` (Any): 変更後の値。
*   `update_method_name` (Optional[str]): プロパティ変更後に呼び出すメソッド名 (例: `"update_text"`).

#### メソッド
*   `redo()`:
    1.  `setattr(target, property_name, new_value)` を実行。
    2.  `_update_target()` を呼び出して画面反映。
*   `undo()`:
    1.  `setattr(target, property_name, old_value)` を実行。
    2.  `_update_target()` を呼び出して画面反映。
*   `_update_target()`:
    *   `update_method_name` があればそれを実行。
    *   なければ `update_text` (TextWindow用), `update_image` (ImageWindow用), `update_position` (共通) の存在をチェックして実行。

### クラス: `MoveWindowCommand`
ウィンドウの移動操作コマンドです。ドラッグ終了時に生成されます。

#### コンストラクタ
```python
__init__(self, target, old_pos: QPoint, new_pos: QPoint)
```
*   `target`: 移動したウィンドウオブジェクト。
*   `old_pos`, `new_pos`: 移動前後の `QPoint` (グローバル座標または親相対座標)。

#### メソッド
*   `redo()` / `undo()`:
    *   `target.move(pos)` を実行。
    *   `target.config.position` (辞書型 `{'x':..., 'y':...}`) も同期して更新。
    *   `target.sig_window_moved` シグナルを発行 (UI側の数値表示更新などのため)。

---

## 3. `utils/translator.py`

### 概要
多言語対応 (i18n) を提供するシングルトン管理クラスです。JSONベースの翻訳ファイルを読み込みます。

### クラス: `Translator` (QObject)

#### シグナル
*   `languageChanged()`: 言語が切り替わった瞬間に発行されます。全UIコンポーネントはこのシグナルを受け取って `retranslateUi()` 相当の処理（`refresh_ui_text`など）を行う必要があります。

#### 内部ロジック (`_load_all_translations`)
*   探索パス:
    1.  `utils.paths.resolve_path("locales")` (リソースディレクトリ下)
    2.  `utils/locales` (開発環境用)
    3.  実行ファイルと同階層の `locales` (Nuitka/PyInstallerの構成対策)
*   読み込み対象: `en.json`, `jp.json`。読み込みに失敗した言語は空辞書となります。

#### メソッド
*   `set_language(lang: str)`: 言語を変更し、変更があった場合のみ `languageChanged` シグナルを発行します。
*   `tr(key: str) -> str`:
    1.  現在の言語の辞書から `key` を検索。
    2.  見つからなければ `en` (英語) の辞書から検索 (フォールバック)。
    3.  それでもなければ `key` そのものを返す (デバッグログに出力)。

### グローバルヘルパー関数
UI実装時はクラスメソッドではなく、これらを使うことが推奨されています。
*   `tr(key: str) -> str`: 翻訳取得のショートカット。
*   `set_lang(lang: str)`
*   `get_lang() -> str`

---

## 4. `utils/logger.py`

### 概要
標準 `logging` モジュールのラッパーおよび初期化スクリプトです。また、未捕捉例外のグローバルハンドラを提供します。

### 定義
*   `LOG_DIR`: ログ保存先ディレクトリ (`{base_dir}/logs`).
*   `log_filename`: `ftiv_YYYYMMDD.log` 形式の現在日時のファイル名。

### 関数

#### `setup_logging() -> None`
*   ルートロガーのレベルを `INFO` に設定。
*   **出力先**:
    1.  `logging.FileHandler`: 指定されたログファイル (UTF-8)。
    2.  `logging.StreamHandler`: 標準出力 (コンソール)。
*   フォーマット: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
*   実行時に `log_diagnostics()` を呼び出し、OS、Pythonバージョン、アプリバージョンなどの環境情報を記録します。

#### `handle_exception(exc_type, exc_value, exc_traceback)`
*   `sys.excepthook` に登録される関数。
*   `KeyboardInterrupt` 以外のアプリアボート級の例外を捕捉し、ログに `CRITICAL` レベルで出力します。
*   かつ、`QMessageBox.critical` を表示してユーザーにログファイルの確認を促します。

---

## 5. `utils/overlay_settings.py`

### 概要
ウィンドウを選択した時に表示される「枠線」のスタイル設定を管理します。

### クラス: `OverlaySettings`
データクラス。
*   `selection_frame_enabled` (bool): 表示ON/OFF (デフォルト True).
*   `selection_frame_color` (str): 色コード (デフォルト `#C800FFFF` / アルファ付き).
*   `selection_frame_width` (int): 線幅 (デフォルト 4).

### ファイルパス
*   設定ファイルの保存先: `json/overlay_settings.json`
*   **変更履歴**: 以前は `app_settings.json` を共有していましたが、設定競合を避けるため独立したファイルに分離されました。

---

## 6. `utils/edition.py`

### 概要
将来的な有償版/無償版の切り替えを見越したエディション判定モジュール。

### Enum: `Edition`
*   `FREE = "free"`
*   `PRO = "pro"`

### クラス: `Limits`
*   `max_text_windows`: テキストウィンドウの最大数。
*   `max_image_windows`: 画像ウィンドウの最大数。
*   `max_save_slots`: セーブスロット数。

### 関数
*   `get_edition(...) -> Edition`:
    *   **現状の実装**: 無条件で `Edition.PRO` を返します。ここを変更することでFREE版制限を有効化できます。
*   `get_limits(edition) -> Limits`:
    *   `PRO`: 全て `10^9` (事実上の無制限)。
    *   `FREE` (未有効化): 各要素 5個 までの強烈な制限。

---

## 7. `utils/paths.py`

### 概要
実行環境（ソースコード実行 vs コンパイル済みexe）の違いを吸収し、正しいファイルパスを提供する重要モジュールです。

### 関数

#### `is_compiled() -> bool`
*   `sys.frozen` (PyInstaller/Nuitka) または `globals()["__compiled__"]` の存在チェック。

#### `get_base_dir() -> str`
**書き込み可能**なデータの保存先ルートを返します。
*   **コンパイル時**: exeが存在するディレクトリ。ただし、ディレクトリ名が `bin` の場合はその親ディレクトリ（`bin`の外）を返します。
*   **非コンパイル時**: プロジェクトのルートディレクトリ。

#### `get_resources_dir() -> str`
**読み込み専用**リソース（画像、翻訳）のルートを返します。
*   マニュアルで `utils.locales` などへアクセスする際に使用されます。
*   コンパイル時は `sys._MEIPASS` (一時フォルダ) ではなく、exeと同階層の静的リソースフォルダを指すように実装されています（可搬性重視）。

---

## 8. `utils/error_reporter.py`

### 概要
特定操作中のエラー通知用ヘルパー。特に「エラー通知の連打」を防ぐ機構を持っています。

### 関数: `report_unexpected_error(...)`
```python
report_unexpected_error(parent, title, exc, state: Optional[ErrorNotifyState], cooldown_ms=2000)
```
*   引数 `state` に `ErrorNotifyState` インスタンスを渡すと、前回の通知時刻とエラー内容（署名）を記憶します。
*   同じエラーが `cooldown_ms` (2秒) 以内に再発した場合、ログ出力のみ行い、`QMessageBox` のポップアップを抑制します。
*   これにより、描画ループ内などでエラーが起きた際にポップアップ地獄になるのを防ぎます。

---

## 9. `utils/docs.py`

### 概要
ヘルプタブやAboutダイアログに表示するための静的なHTMLテキストモジュール。外部ファイルにせずPythonコード内に埋め込むことで、exe化時のファイル欠落リスクを回避しています。

### 定数内容
*   `MANUAL_TEXT_JP`: 日本語マニュアル（第1部：基本編, 第2部：応用編）。
*   `MANUAL_TEXT_EN`: 英語マニュアル。
*   `LICENSE_TEXT`: 利用規約および使用しているOSS（Qt, Python, Pillow, Nuitka）のライセンス表記。
*   `ABOUT_TEXT_TEMPLATE`: バージョン情報を差し込むためのHTMLテンプレート。

---

## 10. `utils/version.py`

### 概要
バージョン定義。

### 定数: `APP_VERSION`
*   `name`: "FTIV"
*   `version`: "0.10.0-dev"
*   `data_format_version`: `1` (セーブデータの互換性チェック用)

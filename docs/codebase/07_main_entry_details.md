# 07. Main Entry Documentation (メインエントリ)

## 1. 概要 (Overview)
`main_entry` パッケージは、アプリケーションの起動ロジックと主要なユーザーインターフェース・コンテナを構成します。Qtアプリケーションコンテキストを初期化するエントリポイントスクリプト (`main.py`) と、アプリケーションのライフサイクル全体、UI構成、コンポーネント間の通信を統括する中心的な `MainWindow` クラス (`ui/main_window.py`) が含まれます。

---

## 2. ファイル (Files)

### 2.1. `main.py`
**パス**: `o:/Tkinter用/FTIV/main.py`

#### 説明 (Description)
"Future Text Interface View" アプリケーションの実行エントリポイントです。グローバルな例外処理、ロギングの初期化、Qtイベントループの開始など、安全なブートストラップを担当します。

#### 関数 (Functions)

##### `run_app()`
*   **説明**: アプリケーションを初期化して実行するメイン関数です。コンソールがないexe環境でも致命的なエラーがユーザーに表示されるよう、実行全体を `try-except` ブロックでラップしています。
*   **プロセス**:
    1.  `QApplication` をインスタンス化します。
    2.  `utils.logger.setup_logging` でロギングを設定します。
    3.  デフォルト言語を日本語 (`"jp"`) に設定します。
    4.  **[Phase 13 追加] `ConfigGuardian` による自己診断**: 設定ファイルの破損をチェックし、必要に応じて自動修復を行います。
    5.  `MainWindow` をインスタンス化します。
    6.  Qtイベントループ (`app.exec()`) を開始します。
*   **エラーハンドリング**: `Exception` をキャッチします。トレースバックを "root" ロガーに記録し、ステータスコード 1 で終了する前に `QMessageBox.critical` でエラーの詳細を表示します。

#### 使用法 (Usage)
スクリプトが `__main__` として実行された場合に自動的に呼び出されます。

---

### 2.2. `ui/main_window.py`
**パス**: `o:/Tkinter用/FTIV/ui/main_window.py`

#### 説明 (Description)
アプリケーションのハブとなる `MainWindow` クラスを定義します。メインダッシュボードウィンドウを管理し、コアマネージャー (`WindowManager`, `FileManager`) を初期化し、グローバルショートカットを処理し、すべてのアプリケーション機能 (テキスト、画像、アニメーション、シーン) のUI統合を提供します。

#### クラス: `MainWindow(QMainWindow)`

##### 主な責務 (Core Responsibility)
*   **UIコンテナ**: タブインターフェース (一般、接続、テキスト、画像、シーン、アニメーション、バージョン情報) をホストします。
*   **マネージャーの統括**: `WindowManager`, `FileManager`, `StyleManager` に加え、`AnimationManager`, `BulkOperationManager`, `SettingsManager`, `ConfigGuardian` などのインスタンスを保持。
*   **[Phase 9 追加] `MainController` への委譲**: 複雑なイベントハンドリングやシグナル接続ロジックを `MainController` に委譲し、自身のコードを軽量化。
*   **シグナルルーティング**: UIイベントを受け取り、適切なマネージャーにロジックを委譲します。
*   **状態同期**: 選択されたウィンドウの状態を反映するようにUI要素 (スライダー、ボタン) を更新します。

##### 初期化 (`__init__`)
*   **引数**: なし。
*   **ロジック**:
    1.  パスとロギングの初期化。
    2.  `MainController` のインスタンス化と DI (Dependency Injection)。
    3.  各 Actions クラス (`text_actions`, `image_actions` 等) の初期化。
    4.  UI の構築と設定の復元。

##### UI構築メソッド (UI Construction Methods)

###### `_init_ui(self)`
*   ウィンドウのタイトル、アイコン、フラグを設定します (フレームレス化はオプションですが、現在は標準的なウィンドウ)。
*   中央の `QTabWidget` (`self.tabs`) を作成します。
*   各タブの構築メソッド (`build_general_tab`, `build_text_tab` など) を呼び出します。

###### `build_general_tab(self)`
*   グローバル設定を含む「一般 (General)」タブを構築します:
    *   アプリケーション設定 (保存/読み込み)。
    *   全体操作 (すべて表示/非表示、すべて削除)。
    *   オーバーレイ設定 (選択枠の表示切り替え)。
    *   パフォーマンス設定 (デバウンス、キャッシュサイズ)。

###### `build_text_tab(self)`
*   テキスト操作用の「テキスト (Text)」タブを構築します:
    *   **追加**: 新しいテキストウィンドウ追加ボタン。
    *   **選択対象の操作**: フォント、色、スタイル、表示切り替え、レイヤー順序。
    *   **レイアウト**: 縦書き/横書き切り替え、パディング/余白設定ダイアログ。
    *   **管理 (Manage)**: 特定テキストのJSON保存/読み込み、スタイルギャラリー。

###### `build_image_tab(self)`
*   「画像 (Image)」タブを構築します:
    *   **追加**: 新しい画像追加ボタン。
    *   **管理 (Manage)**: 複製、再選択、JSON保存。
    *   **変形 (Transform)**: サイズ (%), 不透明度, 回転, 反転 (H/V)。
    *   **整列 (Arrange)**: ディスプレイに合わせる、ディスプレイ中央揃え、スナップ、パッキング整列 (詰め込み/中央寄せ)。
    *   **再生 (Playback)**: GIF/APNGの速度制御と再生切り替え。

###### `build_scene_tab(self)`
*   レイアウト全体を保存/復元するための「シーン (Scenes)」タブを構築します。
*   **構造**: カテゴリごとの `QTabWidget` を使用し、各タブ内にシーンの `QListWidget` を配置します。

###### `build_animation_tab(self)`
*   モーションを割り当てるための「アニメーション (Animation)」タブを構築します:
    *   **適用対象 (Target Selection)**: 選択中のみ、全テキスト、全画像、全ウィンドウ。
    *   **相対移動 (Relative Move)**: 方向 (X/Y), 速度, 待機時間, イージング, ループ/片道。
    *   **絶対移動 (Absolute Move)**: 速度, 待機時間, イージング (固定座標への移動)。
    *   **フェード (Fade)**: フェードイン/アウトのループ、速度、待機時間。

###### `build_connections_subtab(self)`
*   (`ui.tabs.scene_tab` に委譲) コネクタ (線/ラベル) を管理するためのUIを構築します。UI更新ロジックは `ConnectionsTab` クラスに移動済みです。

##### コア機能メソッド (Core Functionality Methods)

###### `refresh_ui_text(self)`
*   **説明**: すべてのUIラベルとボタンのテキストを現在の言語に更新します。
*   **ロジック**: すべての静的文字列に対して `tr()` を呼び出します。各タブのヘルパー `_refresh_xxx_tab_text` を呼び出します。
*   **トリガー**: `utils.translator` が `languageChanged` シグナルを発行した際に呼び出されます。

###### `toggle_property_panel(self)`
*   **説明**: フローティングウィンドウ `PropertyPanel` の表示/非表示を切り替えます。
*   **ロジック**: 複数の切り替えボタン (一般タブ、画像タブなどに点在) の状態を同期させ、すべてが同じ On/Off 状態を反映するようにします。

###### `apply_performance_settings(self, debounce_ms, wheel_debounce_ms, cache_size)`
*   **説明**: 描画の最適化設定を、再起動することなくすべての既存ウィンドウに即座に適用します。
*   **ロジック**: `SettingsManager.apply_performance_settings` に委譲し、`AppSettings` を更新して全ウィンドウに配布します。

##### 緊急・安全対策メソッド (Emergency & Safety Methods)

###### `_register_emergency_shortcuts(self)`
*   **説明**: 復旧用のグローバルホットキーを登録します。
*   **ショートカット**:
    *   `Ctrl+Alt+Shift+R`: 全クリック透過解除 (レスキュー)。
    *   `Ctrl+Alt+Shift+M`: メインウィンドウを最前面へ。
    *   `Ctrl+Alt+Shift+H`: 全ウィンドウを表示。

###### `emergency_disable_all_click_through(self)`
*   **説明**: クリック可能性を回復するために、すべてのウィンドウ (コネクタを含む) の `click_through` を強制的に無効にします。

##### イベントハンドラ (Event Handlers)

###### `closeEvent(self, event)`
*   **説明**: アプリケーションの終了処理を行います。
*   **ロジック**: 終了イベントを受け入れる前に、現在の `app_settings` と `scenes` データベースをディスクに保存します。

###### `dragEnterEvent(self, event) / dropEvent(self, event)`
*   **説明**: 画像ファイルをメインウィンドウに直接ドラッグしてインポートすることを許可します。

---

## 3. 関係性と依存関係 (Relationships & Dependencies)
*   **継承**: `QMainWindow` (PySide6)。
*   **構成要素**:
    *   `WindowManager`: ウィンドウの作成/削除に関するビジネスロジックを処理。
    *   `FileManager`: シーン/JSONの入出力を処理。
    *   `StyleManager`: テキストスタイルギャラリーを処理。
    *   `PropertyPanel`: 選択されたオブジェクトの詳細プロパティ用フローティングインスペクタ。
    *   **[Phase 11] Actions**: `ImageActions`, `SceneActions`, `TextActions` などのコントローラーにビジネスロジックを委譲。
*   **オブザーバー**: `TextWindow`, `ImageWindow`, `Connector`, `Translator` からのシグナルを監視します。

## 4. 既知の問題 / メモ (Known Issues / Notes)
*   **設定の重複**: `overlay_settings.py` と `app_settings.py` の両方が `json/app_settings.json` に書き込んでいました (現在は `overlay_settings.json` に分離修正済み)。
*   **巨大なクラス (解決済み)**: Phase 11 のリファクタリングにより、数千行に及んでいたロジック（特にタブ構築やイベント処理）が `ui/controllers/` パッケージに分散され、保守性が大幅に向上しました。

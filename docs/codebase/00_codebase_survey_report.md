# FTIV コードベース調査報告書

**作成日時**: 2026-01-15
**対象**: Future Text Interface View (FTIV) Project
**作成者**: Antigravity Agent

---

## 1. プロジェクト概要
FTIVは、PySide6 (Qt) を使用した、Windows向けの高度なデスクトップオーバーレイアプリケーションです。テキスト、画像、コネクタ（接続線）をデスクトップ上に自由に配置し、アニメーションやスタイリングを適用して、情報の可視化、プレゼンテーション、装飾を行うことができます。

### 主な機能
*   **テキストオーバーレイ**: 高度な装飾（多重アウトライン、シャドウ、グラデーション）を持つテキストの表示。
*   **画像オーバーレイ**: 静止画およびGIF/APNGアニメーションの表示、不透明度・回転・反転の制御。
*   **コネクタ**: ウィンドウ間を繋ぐベジェ曲線と、それに追従するラベル。
*   **アニメーション**: 移動（相対/絶対）、フェード、GIF再生制御。
*   **シーン管理**: 配置状態の保存と復元（JSON/DB）。
*   **Undo/Redo**: ほぼ全ての操作に対する取り消し/やり直し機能。

---

## 2. アーキテクチャ構成

### 2.1. ディレクトリ構造と責務
プロジェクトは機能ごとに明確にパッケージ分割された、保守性の高い構造を持っています。

| パッケージ | パス | 責務・役割 |
| :--- | :--- | :--- |
| **root** | `./` | アプリ起動 (`main.py`)、リソースフォルダ (`assets/`, `json/` 等) |
| **ui** | `ui/` | メイン画面 (`main_window.py`)、プロパティ操作 (`property_panel.py`)、カスタムウィジェット |
| **ui.controllers** | `ui/controllers/` | ビジネスロジック (`MainController`, `ImageActions`, `SceneActions`, etc.) |
| **windows** | `windows/` | ドメインの中核となるオーバーレイウィンドウの実装 (`TextWindow`, `ImageWindow`, `ConnectorLine`) |
| **managers** | `managers/` | `WindowManager`, `FileManager`, `StyleManager`, `AnimationManager`, `BulkOperationManager`, `SettingsManager` |
| **models** | `models/` | データクラス (`AppSettings`), 定数 (`enums.py`) |
| **utils** | `utils/` | 汎用ユーティリティ (`paths.py`, `settings.py`, `translator.py`, `commands.py`) |

### 2.2. クラス設計の特徴
*   **Controllerパターンによる分離 (Separation of Concerns)**:
    *   `MainWindow` (View) からビジネスロジックを完全に分離しました。
    *   `ImageActions` (画像整列・操作), `SceneActions` (シーンCRUD), `LayoutActions` (整列), `ConnectorActions` (接続管理) などが実装を担当します。
    *   `MainController` がこれらを統括し、アプリ全体のイベントフローを管理します。
*   **継承ベースのウィンドウ設計**:
    *   `BaseOverlayWindow(QLabel)` が全ての基底となり、共通のドラッグ移動、フォーカス制御、Undo連携を提供しています。
    *   これを継承して `TextWindow`, `ImageWindow`, `ConnectorLabel` が実装されています。
*   **Command パターンによる Undo/Redo**:
    *   `QUndoStack` を中心に、全ての状態変更操作（移動、プロパティ変更、生成、削除）が `QUndoCommand` のサブクラスとしてカプセル化されています。
*   **Manager パターン**:
    *   `WindowManager` (ウィンドウ管理), `FileManager` (I/O), `SettingsManager` (設定) など、ドメインごとの管理クラスが責務を分担しています。

---

## 3. 主要なデータフロー

### 3.1. 設定 (Settings)
*   設定データは `models` や `utils` 内の Pydantic データクラス (`AppSettings`, `OverlaySettings`, `WindowConfig`) で定義されます。
*   保存・読み込みは `json/` ディレクトリ以下のJSONファイルに対して行われます。
*   UI操作 → 設定データ更新 → JSON保存 という流れが即座に行われる設計です。
*   **Atomic Save**: データの破損を防ぐため、一時ファイルへの書き込みとリネームによる安全な保存が行われます。

### 3.2. テキスト描画パイプライン
1.  **プロパティ変更**: ユーザーがフォントや色を変更。
2.  **Debounce**: 高速入力を間引くため `QTimer` で遅延更新。
3.  **Renderer**: `TextRenderer` クラスが `QPainterPath` を生成し、LRUキャッシュを利用して描画コストを削減。
4.  **描画**: QPixmap にレンダリングし、QLabel (`TextWindow`) にセット。

---

## 4. 品質と課題の分析

### 4.1. 評価すべき点 (Pros)
*   **堅牢性**: 例外ハンドリングが `sys.excepthook` レベルで統一され、安全なパス解決 (`utils.paths`) やクラッシュ防止策（タイマーによる遅延削除など）が随所に施されています。
*   **品質保証**: `verify_all.bat` により、静的解析 (Ruff)、UI構造監査、ユニットテスト (30件) がワンクリックで実行可能です。
*   **ビルド環境**: Python 3.14 (開発) と 3.13 (Nuitkaビルド) のハイブリッド環境が確立されており、最新機能を使いつつ安定したEXE生成が可能です。
*   **UI/UX**: 多言語対応 (i18n) が一貫して実装されており、ツールチップやステータスバーによるフィードバックも充実しています。

### 4.2. 発見された課題・修正点 (Cons & Fixes)
今回のドキュメント作成プロセスを通じて、以下の点が発見・修正されました。

1.  **設定ファイルの競合 (修正済)**:
    *   `app_settings.py` と `overlay_settings.py` が同一ファイルに書き込みを行い、互いの設定を消し合うバグがありました。
    *   **対策**: `overlay_settings.py` の保存先を `json/overlay_settings.json` に分離することで解決しました。

2.  **`MainWindow` の肥大化 (解決済)**:
    *   かつて数千行に及んだ `MainWindow` は、`ui/controllers/` へのロジック移譲（Image/Scene/Layout/Connector Actions）により大幅にスリム化されました。
    *   現在は純粋な「View」としての役割に特化しています。

3.  **ファイル保存ロジックの分散 (解決済)**:
    *   `SettingsManager` が導入され、設定の保存・読み込みロジックが集約されました。

---

## 5. 総括
FTIVのコードベースは、個人開発のツールとしては極めて高い品質基準（型ヒント、ドキュメント、エラー処理、アーキテクチャ分離）で維持されています。特に「ユーザー設定の保存」と「Undo/Redo」への配慮が深く、使い勝手を重視した設計になっています。
直近の「Phase 11 リファクタリング」の完了により、コードの見通しが劇的に改善され、Nuitkaによる配布準備も整いました。

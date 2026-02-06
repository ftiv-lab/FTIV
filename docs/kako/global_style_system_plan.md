# P1: Global Style System Reform Plan (High Resolution)

## 1. Vision & Goals (目的とビジョン)

現在の「各ファイルに散らばった `setStyleSheet`」という無秩序な状態（Inline Chaos）を脱却し、
**「Single Source of Truth（真実の単一ソース）」** に基づくスタイル管理システムを構築します。

### 🎯 Success Metrics (成功定義)
*   **Zero Hardcoded Colors**: Pythonコード内に `#3a6ea5` などのHex値が存在しないこと（動的なものを除く）。
*   **Hot Reload**: アプリを再起動せずにスタイルの変更を反映できること（開発効率向上）。
*   **Theming Ready**: 将来的な「ダークモード/ライトモード切替」が、変数の差し替えだけで可能な構造になっていること。

---

## 2. Architecture: "The Preprocessor Strategy"

標準のQSSは変数（CSS Variables）をサポートしていません。
そのため、**Python側で簡易プリプロセッサ** を実装し、変数を解決してからQtに適用するアーキテクチャを採用します。

### 🏗️ Components

1.  **`assets/style/theme.qss.template`**
    *   変数プレースホルダー（例: `@PRIMARY_COLOR`）を使用したスタイル定義ファイル。
2.  **`utils/theme_manager.py`**
    *   **Palette Definition**: 色定義を持つ辞書（`ThemeColors`）。
    *   **Engine**: テンプレートを読み込み、変数を置換して `QApplication` に適用する。
    *   **Hot Loader**: 開発中、特定のキー操作（例: F5）でリロードする機能。

### 🎨 Design System (Variables)

デザイナー視点で定義された以下の変数をシステム全体で使用します。

| Variable | Value (Default) | Usage |
|---|---|---|
| `@bg_primary` | `#f0f0f0` | ウィンドウ背景 |
| `@bg_secondary` | `#ffffff` | 入力欄、パネル背景 |
| `@text_primary` | `#000000` | 主なテキスト |
| `@text_dim` | `#666666` | 補足テキスト |
| `@accent_primary` | `#0078d7` | プライマリボタン、アクティブタブ |
| `@accent_hover` | `#005a9e` | ホバー時のアクセント |
| `@danger` | `#d9534f` | 削除・警告ボタン |
| `@border` | `#cccccc` | 枠線 |

---

## 3. Implementation Steps (実装ステップ)

### Phase 1: Infrastructure (基盤構築)
*   [ ] `utils/theme_manager.py` の作成。
*   [ ] `assets/style/theme.qss` (テンプレート) の作成。
*   [ ] `main.py` での初期ロード実装。

### Phase 2: Component Extraction (コンポーネント抽出)
UI上の共通パーツをQSSクラス（`ObjectName` ではなく `Property` または `Class`）に置き換えます。

*   **Buttons**:
    *   Old: `btn.setStyleSheet("background: #0078d7; ...")`
    *   New: `btn.setProperty("class", "primary")`
    *   QSS: `QPushButton[class="primary"] { ... }`
*   **Labels**: Needs, Headers, Warnings.

### Phase 3: Tab Migration (タブ移行)
各タブファイル (`ui/tabs/*.py`) から `setStyleSheet` を削除し、構造化します。
*   `ImageTab`
*   `TextTab`
*   `GeneralTab`

### Phase 4: Dynamic Cleanup (動的スタイルの整理)
*   ユーザーが色を選ぶ場合（Color Picker）などはインラインスタイルのままにする必要がありますが、それ以外の「固定デザイン」を徹底的に排除します。

---

## 4. DX Improvement (開発者のためのルール)

今後、UIを追加する際は以下のルールを厳守します：

1.  **Stop Inline Styling**: Pythonコードに色を書かない。
2.  **Use Semantic Classes**: `setProperty("class", "danger")` のように意味を持たせる。
3.  **Edit QSS, Not Py**: デザイン調整は `.qss` ファイルのみで行う。

---

## 5. Verification Plan (検証計画)

*   **Visual Check**: 全画面のスクリーンショットを撮り、崩れがないか確認。
*   **Reload Check**: アプリ起動中にQSSを書き換え、即座に反映されるかテスト。

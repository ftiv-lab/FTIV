# グローバルスタイルシステム (Global Style System) 解説

## 🎨 概要
「グローバルスタイルシステム (P1)」の実装が完了しました！
これまでの **「インラインスタイルの混沌」** (各所に散らばった `setStyleSheet`) から、**「管理されたグローバルテーマ」** へと移行しました。

### 🏗️ アーキテクチャ
*   **テーママネージャー** (`utils/theme_manager.py`):
    *   テンプレート (`assets/style/theme.qss.template`) を読み込みます。
    *   変数 (`@accent_primary` → `#3a6ea5` など) を置換します。
    *   処理済みの QSS を `QApplication` 全体に適用します。
*   **テンプレート** (`theme.qss.template`):
    *   意味論的なクラス (`.primary`, `.danger`, `.large-button`, `.hint` など) を定義します。
    *   色やスペースのルールを一元管理します。

## 🛠️ 変更内容まとめ

### 1. 新規ファイル
*   `assets/style/theme.qss.template`: スタイルの「唯一の信頼できる情報源 (SSOT)」。
*   `utils/theme_manager.py`: スタイル適用のエンジン。

### 2. リファクタリングされたコンポーネント
Python コード内のスタイル定義を、意味論的なクラス (Semantic Classes) として抽出しました：
*   **タブ**: `ImageTab`, `TextTab`, `GeneralTab`, `AnimationTab`, `SceneTab`
*   **パネル**: `PropertyPanel` (QSS 内では `#PropertyPanel` として識別)
*   **要素**: ボタン (`large`, `emphasized`), ラベル (`dim`, `small`, `hint`)

### 3. ビジュアルの一貫性
*   **ボタン**: 全ての主要アクションボタンが、標準化された `@accent_primary` カラーを使用するようになりました。
*   **変数**:
    *   `@bg_primary` = `#f0f0f0`
    *   `@accent_primary` = `#3a6ea5`
    *   `@text_dim` = `#666666`

## 🚀 検証方法
1.  アプリを起動: `uv run main.py`
2.  **画像タブ**を開く: "+" ボタンが大きく太字になっていることを確認 (Class: `large-button`)。
3.  **プロパティパネル**を開く: 背景が白であることを確認 (Class: `#PropertyPanel`)。
4.  **ホットリロード**: 実行中に `assets/style/theme.qss.template` を編集して即座に反映されるか確認 (トリガーを追加した場合)。

## 📝 次のステップ (Phase 3以降)
*   マイナーなダイアログ (`ui/dialogs.py`) のリファクタリング。
*   ダークモードの実装 (`assets/style/dark_theme.json` パレットの作成)。

# Comprehensive Project Audit Plan (High Resolution)

## 1. Objectives (目的)
最近の「文字周り」「開発環境」の修正を経て、FTIV はv1.0.1+としての安定期に入りました。
しかし、"Super Senior" の視点では「動いている＝完了」ではありません。
さらなる「堅牢性」「拡張性」「ユーザー体験」の向上を目指し、プロジェクト全体を4つのスペシャリスト視点で精密診断（Audit）します。

---

## 2. Audit Roles & Scope (診断の視点)

### 🎨 A. UX/Product Design Specialist (体験設計)
> **"機能はあるが、ユーザーは気づけるか？"**
*   **Focus Area**:
    *   **Onboarding**: 初回起動時の「何もない」状態からの誘導。
    *   **Consistency**: `MainWindow` (設定画面) と `PropertyPanel` (サイドバー) の機能重複・同期ズレ。
    *   **Hidden Features**: 右クリックメニューなどに埋もれた重要機能（透過切替、ロック等）の可視性。
    *   **Error Feedback**: 制限エラーやバリデーション時のメッセージの親切さ。

### 🏗️ B. Software Architect (構造設計)
> **"そのコードは、3年後もメンテナンスできるか？"**
*   **Focus Area**:
    *   **Complexity**: `TextRenderer` などの巨大化したクラスの責務分離（God Object化の阻止）。
    *   **Data Models**: `WindowConfigBase` と `SettingsManager` の JSON 保存構造の整合性と将来性。
    *   **Coupling**: `WindowManager` が `MainWindow` の UI 詳細を知りすぎていないか（Dependency Injection の不足）。
    *   **Legacy Code**: `utils/` 内に残存する不要なヘルパー関数や、使用されていない `constants.py` の定義。

### 🛡️ C. QA & Reliability Engineer (品質保証)
> **"エッジケースで死なないか？"**
*   **Focus Area**:
    *   **Input Validation**: 数値入力欄（SpinBox）への「ありえない値（マイナス、極大値）」の入力。
    *   **Concurrency**: アニメーション中の設定変更や、大量ウィンドウ生成時の負荷。
    *   **High DPI**: 4KモニタやOSのスケーリング変更時の表示崩れ（QtHighDpiScale）。
    *   **File Corruption**: 壊れた JSON 設定ファイルを読み込んだ時の復旧挙動（Rescue Mode）。

### 👨‍💻 D. Dev Experience (DX) Specialist (開発体験)
> **"新しい開発者は、初日にコードを書けるか？"**
*   **Focus Area**:
    *   **Type Coverage**: `Any` 型で逃げている箇所の特定と撲滅。
    *   **Test Coverage**: `tests/test_interactive/` の網羅率。特に「画像機能」「コネクタ機能」のテスト不足。
    *   **Documentation Check**: `docs/` 内の情報が古くなっていないか（特にセットアップ手順）。

---

## 3. Execution Steps (実行手順)

1.  **Static Analysis (静的解析)**:
    *   `verify_all.bat` はパスしている前提で、より深いコードメトリクス（行数、複雑度）を目視確認。
2.  **Structural Review (構造レビュー)**:
    *   主要ファイル (`text_renderer.py`, `window_manager.py`, `main_controller.py`) の依存関係をチェック。
3.  **UI/UX Walkthrough (脳内シミュレーション)**:
    *   主要なユーザーストーリー（インストール→起動→文字出し→装飾→保存→終了→再開）をトレースし、違和感を抽出。
4.  **Reporting**:
    *   発見された課題を **[Code Smells]**, **[UX Gaps]**, **[Risks]** に分類し、優先度付きでレポート化。

---

## 4. Output
*   最終成果物: `project_health_report_v2.md` (仮)
*   ネクストアクション提案書

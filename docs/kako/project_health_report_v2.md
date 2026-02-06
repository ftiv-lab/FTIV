# Project Health Report v2.0 (Super Senior Audit)

## 📊 Executive Summary (診断要約)

**Overall Health: B+ (Good)**
機能実装は非常に充実しており、v1.0.1 としての安定性も高いレベルにあります。
ただし、急ピッチな開発により、一部の「一貫性」「拡張性」において技術的負債が蓄積し始めています。
特に **Style管理の分散** と **Testカバレッジの偏り** が中長期的なリスクです。

---

## 🏗️ 1. Architecture & Code Quality (構造・品質)

### ✅ Strengths
*   **Data Model**: `window_config.py` (Pydantic) によるデータ定義は堅牢。型の恩恵を最大限に受けている。
*   **Renderer**: `TextRenderer` へのロジック集約が成功しており、縦書き・影・縁取りの計算が一元化されている。
*   **Cleanup**: `constants.py` や `utils/` 内の死蔵コードが適切に削除されており、見通しが良い。

### ⚠️ Risks / Issues
*   **[High] Styling Fragmentation (スタイル分散)**:
    *   グローバルな `.qss` ファイルが存在しません。
    *   `ImageTab` や `TextTab` 内で `setStyleSheet("font-weight: bold; ...")` のように個別にスタイルがハードコードされています。
    *   **Impact**: ダークモード対応やデザイン変更時に、全ファイルを修正するコストが発生します。
*   **[Medium] Controller Coupling**:
    *   `MainController` が `getattr(self.view, "animation_tab", None)` のように View の内部構造を "推測" してアクセスしています。
    *   `RULES_AND_STANDARDS.md` の "Explicit Path" 思想と比較すると、やや安全性に欠けます（UIリファクタリングで壊れやすい）。

---

## 🎨 2. UX & Product Design (ユーザー体験)

### ✅ Strengths
*   **Property Panel**: リアルタイム調整機能は非常に強力で、モダンなアプリ体験を提供している。
*   **Text Rendering**: 縦書きプレビューの品質が高く、DIP対応も考慮されている。

### ⚠️ Risks / Issues
*   **[Medium] Missing "Reset" in UI**:
    *   `scripts/reset_defaults.py` は開発者には便利ですが、一般ユーザー（非エンジニア）が設定を壊した時のリカバリ手段がアプリ内にありません。
    *   **Proposal**: 「設定」タブ内に「初期設定に戻す（ファクトリーリセット）」ボタンを配置すべきです。
*   **[Low] Context Menu Hidden Features**:
    *   「クリック透過」などの強力な機能が、右クリックメニューの深い階層にあります。
    *   初心者が見つけられない可能性があります。

---

## 🛡️ 3. QA & Reliability (品質保証)

### ✅ Strengths
*   **Type Safety**: `mypy --strict` 準拠は非常に高い品質基準です。
*   **Rescue Logic**: `WindowManager._prune_invalid_refs` など、Qtのクラッシュを防ぐ防衛的プログラミングが随所に見られます。

### ⚠️ Risks / Issues
*   **[High] Test Gaps (Persistence)**:
    *   「設定変更 → 保存 → 再起動 → 読み込み」というサイクルを検証する自動テスト（E2E）が不足しています。
    *   `test_archetype_persistence.py` はありますが、アプリ全体の `AppSettings` との連動は見えていません。
*   **[Medium] Flaky Animation Tests**:
    *   過去にアニメーションテストで `time.sleep` に依存した不安定な挙動がありました。`test_interactive` 内の非同期処理が適切か再点検が必要です。

---

## 👨‍💻 4. Dev Experience (開発体験)

### ✅ Strengths
*   **Modern Stack**: `uv`, `ruff`, `pre-commit` の導入により、開発環境のセットアップ速度は爆速です。
*   **Documentation**: `AGENT_READING_LIST.md` 等のドキュメント整備状況は極めて良好です。

### ⚠️ Risks / Issues
*   **[Low] Lack of Asset Pipeline**:
    *   アイコンや翻訳ファイルが増えた際的管理ルールが曖昧です。

---

## 🚀 Next Action Proposals (改善提案)

優先度順に提案します。

| Priority | Action | Description | Role |
|---|---|---|---|
| **P1** | **Global Style System** | `assets/style/theme.qss` を作成し、散らばったインラインスタイルを集約・変数化する。 | Frontend |
| **P2** | **App-Internal Reset** | `scripts/reset_defaults.py` のロジックをラップし、アプリ内設定画面から安全に呼び出せるようにする（要再起動ダイアログ）。 | UX/Arch |
| **P3** | **Persistence E2E Test** | 設定保存のサイクルを保証する `test_e2e_persistence.py` を追加する。 | QA |
| **P4** | **Controller Refactor** | `MainController` と View の結合を疎にする（Signal/Slot または Protocol パターンの徹底）。 | Architect |

このレポートに基づき、次のフェーズ計画を立てることを推奨します。

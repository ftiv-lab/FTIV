---
description: FTIV (PySide6 Desktop App) 開発用の標準ワークフロー。verify_all.bat / verify_debug.bat による完全品質保証。
---

# FTIV 開発ワークフロー v2.0

## 0. 基本哲学: Reliability First (信頼性第一)

> **"Measurement Validity" (測定の妥当性)**
> テスト環境が不安定であれば、機能の正しさは証明できない。
> ログが途切れる、クラッシュする等の「環境のノイズ」を放置せず、`verify_debug.bat` で確実なエビデンスを得ること。

---

## Phase 1: 調査 (Investigation)

// turbo
1. **環境健全性チェック**:
   - まず仮想環境とテスト環境が正常か確認する。
   ```powershell
   .\verify_debug.bat
   ```
   - ログ (`logs/test_execution.log`) が最後まで出力され、`Exit code: 0` であることを確認。

2. **変更対象の特定**:
   - `view_file` / `view_file_outline` で構造把握。
   - `docs/codebase/` のドキュメント確認。

---

## Phase 2: 計画策定 (Planning)

3. **実装計画の作成**:
   - 複雑なタスクは `implementation_plan.md` を作成。
   - **Quality Strategy**: テスト困難なUI操作（アニメーション等）が含まれる場合、`FTIV_TEST_MODE` でどう制御するか計画に含める。

---

## Phase 3: 実装 (Execution)

4. **Code with Awareness**:
   - **Global Animation Switch**: `LayoutManager` 等のアニメーションを含むクラスは、`os.environ.get("FTIV_TEST_MODE")` を検知し、即時完了できるように実装する。
   - **Explicit Types**: 型ヒントは必須。循環参照は `TYPE_CHECKING` で回避。

5. **Qt/PySide6 Patterns**:
   - `Signal/Slot` による疎結合を維持。
   - `QWidget` は親を知らない状態を保つ。

---

## Phase 4: 品質ゲート (Quality Gate)

実装後は以下の順で検証を行う。

// turbo
6. **標準検証 (Fast)**:
   ```powershell
   .\verify_all.bat
   ```
   - Lint, UI Audit, Pytest (Standard) を一括実行。
   - ここでパスすればOK。

// turbo
7. **詳細検証 (Deep/Robust)**:
   - `verify_all.bat` が途中で止まる、ログが切れる等の不安定な挙動を見せた場合、**即座に切り替える**。
   ```powershell
   .\verify_debug.bat
   ```
   - `faulthandler` 有効化、バッファリング無効化。
   - クラッシュ原因を特定し、ログファイル (`logs/test_execution.log`) で全テストの合否を確認する。

---

## Phase 5: 記録と同期 (Sync & Log)

8. **進捗ログ更新**:
   - `docs/refactoring_plans/00_task_progress_log.md` 更新。

9. **ドキュメント更新**:
   - 設計変更があった場合、`docs/codebase/` を更新。

---

## 禁止事項 (NEVER DO)

> [!CAUTION]
> - `verify_all.bat` / `verify_debug.bat` のどちらも通らない状態でコミット・プッシュしない
> - テストコード内で `time.sleep()` を使ってアニメーションを待機しない（`FTIV_TEST_MODE` を使う）
> - ログが途切れているのに「多分パスした」と判断しない

---

## コマンドリファレンス

| コマンド | 用途 | 特徴 |
|:---|:---|:---|
| `.\verify_all.bat` | 日常的な検証 | 高速、標準出力 |
| `.\verify_debug.bat` | **確実な検証・デバッグ** | クラッシュ検知、ログファイル出力、アニメーション無効化 |
| `verify_stress.bat` | 高負荷テスト | メモリリーク、大量生成テスト |
| `ruff check --fix .` | コード整形 | import順序、未使用変数削除 |

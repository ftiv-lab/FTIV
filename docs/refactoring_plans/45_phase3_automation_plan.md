# Implementation Plan: Everything Claude Code Phase III - Virtual Hooks for FTIV

## 1. 概要 (Overview)
「Everything Claude Code」の Phase III: Automation (Hooks) を、現在のFTIV開発環境（Antigravity）に適応させるための詳細計画です。

**課題:**
Antigravity環境では、ツール実行をイベントとしてフックする（例: `Edit` 実行直前にスクリプトを走らせる）ネイティブ機能はユーザー側で制御できません。

**解決策: "Virtual Hooks"**
「エージェントが自律的に実行するスクリプト群」と「それを強制する憲法（Rules）」を組み合わせることで、**擬似的な自動化フック**を実現します。

## 2. 実装コンセプト (Concept)

### The "Virtual Hook" Mechanism
1.  **Script**: チェック処理の実体（例: `scripts/hook_pre_commit.py`）。
2.  **Trigger**: エージェントの行動（コミット前、ファイル保存後）。
3.  **Enforcement**: `Antigravity Rules` による強制。「コミット前には必ずスクリプトXを実行せよ」と定義。

## 3. 具体的な実装対象 (Deliverables)

### A. Pre-Commit Hook (`scripts/hook_pre_commit.py`)
> **目的**: "汚いコード" の混入を物理的に阻止する。

このスクリプトは以下のチェックを順次実行し、**一つでも失敗すれば終了コード 1 を返します**（＝エージェントはコミットを中止しなければならない）。

1.  **Debug Residue Scan**:
    *   `print(...)` (Python)
    *   `console.log(...)` (JS/TS)
    *   `Pyside6.QtCore.qDebug(...)` 以外のデバッグ出力
    *   `import pdb; pdb.set_trace()`
2.  **Conflict Marker Scan**:
    *   `<<<<<<< HEAD`, `>>>>>>>` の残存チェック
3.  **Critical Lint**:
    *   `ruff check --select E9,F63,F7,F82` (Syntax Error, Undefined variables)
    *   ※ 全Lint修正は強制しない（ノイズになるため）。致命的なもののみ。
4.  **Forbidden Patterns**:
    *   `time.sleep()` (テストコード以外での使用禁止)
    *   `parent().child()` (密結合パターンの簡易検知)

### B. Smart Context Hook (`scripts/suggest_context.py`)
> **目的**: "ファイルを開いたが、関連テストを見るのを忘れた" を防ぐ。

ファイルパスを引数に渡すと、関連度が高いファイルを推奨するスクリプト。
（将来的にMCPサーバー化も検討できるが、まずはスクリプトとして実装）

*   **入力**: `ui/main_window.py`
*   **出力**:
    *   `tests/ui/test_main_window.py` (Unit Test)
    *   `ui/styles.qss` (Related Style)

### C. Rule & Workflow Updates
これらのスクリプトを運用に乗せるためのドキュメント更新。

1.  **`.agent/workflows/feature_dev_lifecycle.md`**:
    *   "Commit" ステップの前に `Verify Code (Run Hooks)` を追加。
    *   `// turbo` コマンドとして定義。
2.  **`Antigravity Rules v2.3` (User Global Memory)**:
    *   "3. コーディング標準" に以下を追加:
        > **Pre-Commit Hook**: コミット前に必ず `python scripts/hook_pre_commit.py` を実行し、Passすることを確認せよ。

## 4. 実行手順 (Execution Plan)

### Step 1: スクリプト基盤の作成
- [ ] `scripts/utils/code_scanner.py`: 汎用的な正規表現スキャナ作成
- [ ] `scripts/hook_pre_commit.py`: メインロジック実装

### Step 2: テスト導入
- [ ] 意図的に `print` を含んだファイルを作成し、Hookが正しくFailするか検証。

### Step 3: ルール適用
- [ ] `workflows/feature_dev_lifecycle.md` 更新
- [ ] ユーザーへのルール更新依頼（Memory更新）

## 5. 検証計画 (Verification)

### Manual Verification
1.  ダミーの変更（`print("debug")` を含む）を行う。
2.  `python scripts/hook_pre_commit.py` を実行。
3.  **期待値**: エラーが出力され、検出箇所（行番号）が表示されること。

### Integration
1.  実際のFTIV開発フロー（適当なリファクタリング）を実行。
2.  ワークフローに従ってHookを使用し、スムーズに開発できるか確認（誤検知で開発が止まらないか）。

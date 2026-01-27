---
description: Standard lifecycle for feature development and refactoring (Investigate -> Plan -> Execute -> Sync).
---

# Workflow: Feature Development Lifecycle

> [!NOTE]
> `tdd.md` (Red-Green-Refactor) は「コードを書くサイクル (Inner Loop)」です。
> このワークフローは「タスク全体を進めるサイクル (Outer Loop)」です。

## Step 1: Investigation & Analysis (Architect Role)
1.  **現状把握**: 修正対象のコードと依存関係を特定する。
2.  **リスク評価**: 「この変更が他にどのような影響を与えるか？」を `docs/investigation/` に記録する。

## Step 2: Planning (Architect Role)
1.  **計画書作成**: `implementation_plan.md` または `docs/refactoring_plans/` に詳細な手順を書く。
2.  **承認待ち**: ユーザーに計画を提示し、GOサインが出るまでコードを書かない。

## Step 3: Execution (TDD Loop)
1.  **TDD**: `.agent/workflows/tdd.md` に従い、テスト駆動で実装する。
2.  **Review**: `.agent/roles/code-reviewer.md` の観点で自己レビューする。

## Step 4: Verification & Sync (QA Role)
1.  **Run Virtual Hooks**:
    // turbo
    ```powershell
    python scripts/hook_pre_commit.py
    ```
    - コミット前の必須ゲートキーパー。`print()` 残存などを検知する。
2.  **Verify**: `verify_all.bat` を実行し、全テストパスを確認する。
3.  **Doc Sync**: `docs/refactoring_plans/00_task_progress_log.md` を更新し、実装とドキュメントの乖離をなくす。

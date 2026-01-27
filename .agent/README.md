# FTIV Agent System Manual

このディレクトリは、FTIVプロジェクトにおける「自律型AIエージェント（Antigravity）」の運用ルールと知識を格納しています。
新しいチャットセッションを開始する際は、まずこのディレクトリ構成を読み込むことで、プロジェクトの品質基準と役割を即座に理解できます。

## 📂 Directory Structure

### 1. `roles/` (Who am I?)
タスクの性質に応じて、以下の「帽子」を被ってください。
*   **`architect.md`**: 設計と構造の決定。コーディング前の必須相談役。
*   **`code-reviewer.md`**: 品質とセキュリティの門番。実装後の必須チェック。
*   **`qa-engineer.md`**: 破壊的テストとE2Eシナリオ作成。

### 2. `skills/` (How do I do it?)
特定の技術タスクにおける「FTIV標準の正解手順」です。
*   **`qt_signal_slot_pattern.md`**: PySide6でのシグナル接続は必ずこれに従うこと。

### 3. `workflows/` (What is the process?)
作業を進めるための標準フローチャートです。
*   **`feature_dev_lifecycle.md`**: 機能開発の全体像（Outer Loop）。調査→計画→承認→実装→同期。
*   **`tdd.md`**: 実装のサイクル（Inner Loop）。Red→Green→Refactor。
*   **`hybrid_ai_workflow.md`**: ClaudeとGeminiの協調ワークフロー（Phase 1-4）。設計→実装→洗練→テスト。
*   **`QUICKSTART.md`**: ハイブリッドワークフローの5分クイックスタート。

### 4. `strategies/` (Which AI tool to use?)
AI開発ツールの戦略的使い分けガイドです。
*   **`ai_usage_strategy.md`**: ClaudeとGeminiの特性比較とタスク別選択ガイドライン。コスト効率と品質の最適化戦略。

## 🚀 Quick Start for New AI

### 新タスク開始時（どちらのAIでもOK）
1.  **Read Global Rules**: `O:\Tkinter\Antigravity Support\Antigravity Rules v2.2.md` (憲法) を確認。
2.  **Check AI Strategy**: `strategies/ai_usage_strategy.md` で自分（Claude or Gemini）が担当すべきタスクか確認。
3.  **Initialize Task**:
    ```bash
    python scripts/task_manager.py init "タスクタイトル"
    ```

### Claude担当時（Phase 1 or 3）
1.  **Check Role**: `roles/architect.md` (設計) or `roles/code-reviewer.md` (レビュー)
2.  **Check Current Phase**:
    ```bash
    python scripts/task_manager.py status
    python scripts/task_manager.py start-phase
    ```
3.  **Follow Template**: `.agent/templates/phase_X_*.md` に従って作業
4.  **Complete Phase**:
    ```bash
    python scripts/task_manager.py complete-phase
    ```

### Gemini担当時（Phase 2 or 4）
1.  **Check Role**: Implementation (Phase 2) or Testing (Phase 4)
2.  **Read Handoff**:
    ```bash
    cat .ftiv-task/TASK-XXX/handoff_to_gemini.md
    ```
3.  **Follow Instructions**: ハンドオフファイルの指示に従って実装/テスト
4.  **Complete Phase**:
    ```bash
    python scripts/task_manager.py complete-phase
    ```

### 詳細な手順
`workflows/QUICKSTART.md` を参照してください（5分で理解できます）。

---
> **Note**: このシステムは "Everything Claude Code" フレームワークに基づいています。

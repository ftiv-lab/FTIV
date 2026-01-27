# 外部リソース分析: Everything Claude Code

## 概要
`Everything Claude Code` リポジトリは、AIコーディングアシスタント（特にClaude/Antigravityのようなエージェント）の能力を最大化するための包括的なフレームワークです。
単なるプロンプト集ではなく、開発プロセス自体を「構造化されたシステム」として定義している点が特徴です。
FTIV開発において、"Super Senior Engineer" レベルの品質を維持・強制するための具体的なヒントが多く含まれています。

## 1. 主要コンセプトとFTIVへの適用提案

### A. Agents (専門化された役割権限)
開発プロセスを単一のエージェントに任せるのではなく、役割ごとに「帽子」を切り替えるアプローチ。

*   **現状:** `Super Senior Engineer` という漠然とした人格。
*   **提案:** 以下の役割定義ファイルを作成し、タスクに応じて明示的にロードする。
    *   `architect.md`: 設計判断、トレードオフ分析担当。コードは書かない。
    *   `code-reviewer.md`: セキュリティ、可読性、計算量のみを見る担当。
    *   `qa-engineer.md`: エッジケース、E2Eテストシナリオ作成担当。

### B. Skills (ワークフローの標準化)
よくある作業手順を明確なステップ（Skill）として定義する。

*   **現状:** `.agent/workflows/` にいくつかのワークフローがある。
*   **提案:** より粒度の細かい「作業手順書」を `skills/` に配備する。
    *   `skill_add_qt_signal.md`: シグナル定義からスロット接続、切断処理までの定型手順。
    *   `skill_refactor_extract_widget.md`: 巨大ウィジェットを分割する際の安全手順。

### C. Hooks (ルールの自動強制)
ツール実行時に自動的にチェックを行う仕組み。

*   **現状:** `verify_all.bat` を手動（またはAIが自律）実行。
*   **提案:** （Antigravityのシステム制約上、完全な自動フックは難しいが）「仮想フック」として運用ルールに組み込む。
    *   **Pre-Commit Hook**: `git commit` 前に必ず `grep` で `print` / `console.log` / `TODO` をスキャンする手順を強制する。
    *   **File-Watch Hook**: 特定のファイル（`Active Document`）が開かれたら、関連する `TEST` ファイルも自動的にコンテキストに入れる。

### D. Verification Loop & TDD
「実装 → 検証」のループを厳格化。

*   **Everything Claude Code流:**
    1.  インターフェース定義
    2.  失敗するテスト作成 (RED)
    3.  最小実装 (GREEN)
    4.  リファクタリング (REFACTOR)
    5.  カバレッジ80%以上確認
*   **FTIVへの適用:**
    *   現在も方針としてはあるが、徹底されていない。
    *   `/tdd` コマンド（またはワークフロー）を定義し、このサイクルを **強制的に** 回させる。

## 2. 具体的な導入ロードマップ

### Phase I: 構造の整備
*   ルートディレクトリに `.agent/roles/` を作成し、役割定義を配置。
*   `.agent/skills/` を拡充し、Qt/PySide6特有のパターン（シグナル、イベントフィルタ等）を文書化。

### Phase II: TDDの厳格化
*   `workflows/tdd.md` を作成。
*   「テストなしの実装」を **禁止ドクトリン** として `Antigravity Rules` に追加。

### Phase III: 自動化（仮想Hooks）
*   `scripts/pre_commit_check.py` 等のスクリプトを作成し、AIがコマンド実行時に自身のミス（デバッグプリントの混入等）を検知できるようにする。

## 3. Super Senior Engineer からのコメント

> "ツールは使いようだが、この `Everything Claude Code` の**『品質をプロセスで担保する』**という思想は、我々が目指す `High Gravity Quality` と完全に合致する。
> 特に **Hooks** の概念は面白い。人間の記憶力に頼らず、仕組みでミスを防ぐ。これこそがエンジニアリングだ。
> まずは **Agents (役割分担)** と **Skills (定石ドキュメント)** から取り入れよう。"

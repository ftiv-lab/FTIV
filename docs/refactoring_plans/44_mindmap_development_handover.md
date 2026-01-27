# FTIV MindMap Development Handover (Phase 36)

## 1. Executive Summary
現在、FTIV (Focus Tree Integrated View) の **マインドマップモード** は、基本機能の実装を終え、最も困難だった「折りたたみボタン（Folding Button）の表示バグ」を **Integrated Rendering (直接描画)** 方式への移行によって完全に解決しました。
また、開発プロセス自体を見直し、"Everything Claude Code" 由来の **Agent/Skill/Rule** システムを導入して、品質保証体制を強化しました。

## 2. Technical Roadmap & Architectual Evolution

### Phase 30-34: 初期実装と苦闘
*   **Architecture**: `QGraphicsProxyWidget` を多用して、ノード内に `QPushButton` や `QTextEdit` を埋め込む設計。
*   **Problem**: `QGraphicsProxyWidget` はZ-Order管理やイベント伝播が複雑で、特に「折りたたみボタン」が特定の操作後に消失、あるいはクリック不能になるバグが頻発。描画アーティファクト（ゴミ）も残る問題があった。

### Phase 35: The "Folding" Crisis & Diagnosis
*   **Diagnosis**: 再現スクリプト (`tests/reproduction/repro_folding_invisibility.py`) により、`ProxyWidget` の `paint` イベントが正しく発火していない、またはクリッピングされていることが判明。
*   **Decision**: 「ウィジェットを埋め込む」アプローチを放棄し、QtのGraphics View Framework本来の **「直接描画 (Integrated Rendering)」** に移行する決断。

### Phase 36: Integrated Rendering & Stabilization (Current)
*   **Solution**: `MindMapNode.paint()` メソッド内で、ボタンの形状（円とアイコン）を直接描画。
*   **Interaction**: `mousePressEvent` 内でクリック位置を判定し、ボタン領域なら折りたたみロジックを発火。
*   **Result**: 描画の安定性が100%になり、消失バグが根絶された。E2Eテスト (`tests/e2e/test_mindmap_folding_interaction.py`) もパス。

## 3. Process Upgrade (New Standards)

次のチャットセッションから即座に適用される新しい開発標準です。

### A. New Directory Structure
*   **`.agent/roles/`**: 専門家エージェントのペルソナ定義。
    *   `architect.md`: 設計・構造担当
    *   `code-reviewer.md`: 品質・セキュリティ担当
    *   `qa-engineer.md`: E2Eテスト・破壊試験担当
*   **`.agent/skills/`**: 標準化された作業手順。
    *   `qt_signal_slot_pattern.md`: シグナル接続のベストプラクティス。
*   **`.agent/workflows/`**: 強制ワークフロー。
    *   `tdd.md`: **Red-Green-Refactor** の厳守 (Inner Loop)。
    *   `feature_dev_lifecycle.md`: 調査・計画・記録の全体サイクル (Outer Loop)。 旧 `wolkflows1a.md` の後継。

### B. New Tools
*   **`scripts/pre_commit_check.py`**: コミット前に実行するサニティチェック。`print()` や APIキー混入を防止。

### C. New Rules (`Antigravity Rules v2.3`)
*   **Strict TDD**: テストコードなしの実装は許可されない。
*   **Signal/Slot Only**: 親から子への直接メソッド呼び出し禁止。

## 4. Remaining Debt & Specific Next Steps

### Warning: The "God Class" (`MindMapNode`)
*   **Status**: `MindMapNode` は現在 **1100行** を超えており、スーパーシニアエンジニアから "God Object" として強い警告を受けている。
*   **Risk**: 描画、レイアウト、イベント処理、シリアライズが混在しており、これ以上の機能追加は危険。
*   **Action**: 次のセッションの最優先事項は **リファクタリング** である。

### Roadmap for Next Session
1.  **Refactor `MindMapNode` (Priority: High)**
    *   `NodeRenderer`: 描画ロジックの分離
    *   `NodeLayoutManager`: テキストとボタンの配置計算の分離
    *   `NodeInteractionHandler`: イベント処理の分離
2.  **Fix Duplicate Logic (Priority: Medium)**
    *   `DefaultNodeStyle` の適用ロジックが2箇所 (`_set_as_default_style`, `add_node`) に散らばっているのを統一する。
3.  **Expand E2E Tests (Priority: Medium)**
    *   ドラッグ移動、リサイズ、テキスト編集のE2Eテストを追加する (`QA Engineer` ロールの活用)。

## 5. Artifacts Mapping
*   `super_senior_critique.md`: 辛口批評の全文。
*   `docs/43_external_resource_analysis_everything_claude.md`: プロセス改善の詳細。
*   `.agent/`: 新プロセスシステムの中枢。

---
**Handover Status**: **GREEN**
*   Codebase: Stable (Tests Passing)
*   Docs: Updated
*   Plan: Defined

# Phase 21: MindMap Refactoring & Stabilization

## 1. Status Update & Correction

**Correction**: 前回の分析で「自動レイアウトが未実装」としましたが、コードベースを確認したところ、以下の機能が既に実装済みであることを確認しました。
*   **Strategies**: `RightLogical`, `BalancedMap`, `OrgChart` (3種類の実装を確認)
*   **Controller**: `MindMapController` がノード追加時に `arrange_tree` を呼び出している。
*   **LayoutManager**: アニメーションを含む配置ロジックが存在する。

現状の問題（User Feedback）:
*   既存の実装において「ハレーション」（競合や副作用）あるいは「ハルネーション」（不安定な挙動）が発生している可能性がある。
*   `MindMapNode` が巨大化しており、これが挙動の不安定さや保守の難しさにつながっている。

## 2. Updated Objectives (修正後の目的)

本フェーズの目的を「新規実装」から**「リファクタリングによる安定化」**に変更します。

1.  **Decoupling (責務の分離)**: `MindMapNode` (God Class) を解体し、イベント処理とロジックを分離する。これにより、レイアウトやインタラクションの挙動を明確にする。
2.  **Layout Stabilization (レイアウト安定化)**: 既存の3つのレイアウト戦略 (`Right`, `Balanced`, `OrgChart`) の挙動を検証し、副作用（ドラッグ移動との競合など）を解消する。

---

## 3. Refactoring Roadmap

### Step 1: Interaction Handler (優先度: 高)
`MindMapNode` からイベント処理を引き剥がします。
*   **Task**: `ui/mindmap/components/interaction_handler.py` を作成。
*   **Goal**: `mousePress`, `mouseMove` などのイベントロジックを移動し、`MindMapNode` を描画とデータ保持に集中させる。

### Step 2: Layout Logic Audit (優先度: 中)
既存のレイアウトロジックが正しく機能しているか監査・修正します。
*   **Task**: `MindMapController.add_child_node` 等での `arrange_tree` 呼び出しタイミングと、Animationの挙動を確認。
*   **Fix**: ユーザー操作（ドラッグ）と自動レイアウトが競合しないよう、`Manual Positioning` フラグの導入などを検討。

### Step 3: Folding Manager (優先度: 中)
折りたたみロジックを分離します。
*   **Task**: `ui/mindmap/components/folding_manager.py` を作成。

---

## 4. Why this matters?

「機能はあるのに不安定」な状態は、実装が複雑に絡み合っている（Coupling）ことが主な原因です。
Step 1 の分離を行うことで、「なぜレイアウトがおかしくなるのか」の原因特定が容易になり、結果として "Brain Speed" を支える快適な操作感が実現できます。

**Next Action**: 上記の Step 1 (Interaction Handler) から着手します。

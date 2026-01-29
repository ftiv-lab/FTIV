# Hybrid AI Workflow: Phase-Driven Development

**目的**: ClaudeとGeminiの強みを活かした、確実なハンドオフと品質保証を実現する4フェーズワークフロー。

---

## 🔄 ワークフロー全体像

```
Phase 1: Design (Claude)
   ↓ [Handoff: ADR + Design Spec]
Phase 2: Implementation (Gemini)
   ↓ [Handoff: Working Code + Implementation Log]
Phase 3: Refinement (Claude)
   ↓ [Handoff: Reviewed Code + Review Report]
Phase 4: Testing (Gemini)
   ↓ [Completion: Test Suite + Test Report]
```

---

## 📏 タスクサイズ別ワークフロー選択

**重要**: 全てのタスクに4フェーズは過剰。タスク規模に応じて適切なワークフローを選択する。

### 判定フローチャート

```
「変更規模は？」
  │
  ├─ 小（1-2ファイル、50行以下）
  │    └→ 🔥 Hotfix: Claude単独で完結
  │
  ├─ 中（3-5ファイル、100-500行）
  │    └→ 📦 Standard: 4フェーズ（設計は意図のみ）
  │
  └─ 大（10+ファイル、大量の機械的変更）
       └→ 🚀 Gemini先行: Gemini実装 → Claude洗練
```

---

### 🔥 小規模修正（Hotfix）: Claude単独

**条件**: 1-2ファイル、50行以下の変更

**ワークフロー**:
```
ユーザー要求 → [Claude] 調査+設計+実装+テスト確認 → 完了
```

**例**:
- バグ修正（1メソッド追加）
- 既存ロジックの微調整
- 設定値の変更

**使用コマンド**:
```bash
# タスク管理不要、直接実装
# テスト確認後、完了
pytest tests/ -v
```

---

### 📦 中規模機能（Standard）: 4フェーズ

**条件**: 3-5ファイル、100-500行の変更

**ワークフロー**: 通常の4フェーズ（Phase 1-2-3-4）

**Phase 1 設計粒度ガイド**:

| 書くべきこと | 書かないこと |
|------------|-------------|
| クラス名・メソッドシグネチャ | 完全な実装コード |
| 責務・入出力の説明 | 具体的なアルゴリズム |
| 「何を」「なぜ」の詳細 | 「どう」の詳細（Geminiに任せる） |

**設計例**（適切な粒度）:
```python
def _paint_background_only(self, painter: QPainter, node: "MindMapNode") -> None:
    """編集モード中に背景のみを描画する。

    責務:
    - node.config から描画パラメータを取得
    - 角丸長方形を QPainter で描画

    注意:
    - TextRenderer は使わない（編集中なので）
    - SimpleNodeRenderer の背景描画を参考に
    """
    pass  # 実装は Gemini に委ねる
```

**Geminiの役割**:
- 設計意図を理解して実装を埋める
- 高速に動くバージョンを作る
- 「どう書くか」の判断をGeminiに任せる

---

### 🚀 大規模リファクタリング: Gemini先行

**条件**: 10+ファイル、大量の機械的変更

**ワークフロー**:
```
[Gemini] 大量の機械的変更（リネーム、移動、フォーマット）
   ↓
[Claude] アーキテクチャレビュー・洗練
   ↓
[Gemini] テスト追加・修正
```

**例**:
- ファイル名一括変更
- インポート整理
- 大規模なコード移動
- 定型的な置換作業

**Geminiの強みを活かす**:
- 1Mトークンのコンテキストで大規模コードベース全体を把握
- 高速な機械的変更
- 使用量制限が緩い

---

## 📋 使用方法

### 新タスク開始時

1. **タスク初期化**:
   ```bash
   python scripts/task_manager.py init "ノードグルーピング機能"
   ```
   → `.ftiv-task/TASK-XXX/` ディレクトリが作成される

2. **Phase 1開始** (Claude):
   ```bash
   python scripts/task_manager.py start-phase 1
   ```
   → テンプレート `.agent/templates/phase_1_design.md` が表示される

3. **各フェーズ完了時**:
   ```bash
   python scripts/task_manager.py complete-phase
   ```
   → ハンドオフチェックリストが生成され、次フェーズへ

---

## Phase 1: Design (Claude担当)

### 📌 目的
曖昧な要件から具体的な設計へ落とし込み、Geminiが実装可能な仕様を作成する。

### 📝 成果物
- **ADR (Architecture Decision Record)**: `.ftiv-task/TASK-XXX/adr.md`
- **Design Spec**: `.ftiv-task/TASK-XXX/design_spec.md`

### ✅ 完了条件 (Definition of Done)
- [ ] 要件が明確化されている（曖昧さ0%）
- [ ] 影響範囲が特定されている（変更ファイルリスト）
- [ ] 設計判断とトレードオフが記録されている（ADR）
- [ ] 実装手順が具体的（Geminiが迷わない粒度）
- [ ] テスト観点がリストアップされている
- [ ] .agent ルール適合性確認済み

### 🔍 実施内容

1. **要件整理**:
   - ユーザー要求の背景・目的を理解
   - 機能仕様を具体化
   - 受け入れ基準を定義

2. **影響範囲分析**:
   ```bash
   # Claude実行コマンド例
   grep -r "class MindMapNode" --include="*.py"
   ```
   - 変更が必要なファイル特定
   - 依存関係の確認
   - リスク評価

3. **設計判断記録** (ADR):
   - 選択肢の比較（Option A vs B）
   - 選択理由とトレードオフ
   - 業界標準・.agentルールとの整合性確認

4. **実装仕様書作成** (Design Spec):
   - クラス構造（追加・変更）
   - メソッドシグネチャ
   - データフロー図
   - エラーハンドリング方針

5. **テスト観点定義**:
   - 正常系シナリオ
   - 異常系シナリオ
   - エッジケース

### 🤝 ハンドオフ準備
```bash
python scripts/task_manager.py complete-phase
```
→ 以下を生成：
- `handoff_to_gemini.md`: Geminiへの指示書
- チェックリスト確認プロンプト

---

## Phase 2: Implementation (Gemini担当)

### 📌 目的
Design Specに従って、高速に動作するコードを実装する。

### 📝 成果物
- **Implementation Code**: 実装されたPythonファイル群
- **Implementation Log**: `.ftiv-task/TASK-XXX/implementation_log.md`

### ✅ 完了条件 (Definition of Done)
- [ ] Design Specの全項目が実装済み
- [ ] コードが動作する（手動確認済み）
- [ ] 実装中の判断・変更点が記録されている
- [ ] 既存テストが全てパスする
- [ ] 明らかなバグがない（基本動作確認済み）

### 🔍 実施内容

1. **Design Spec確認**:
   ```bash
   # Gemini開始時に必ず読む
   cat .ftiv-task/TASK-XXX/design_spec.md
   cat .ftiv-task/TASK-XXX/handoff_to_gemini.md
   ```

2. **実装実行**:
   - Design Spec通りにクラス・メソッド追加
   - 高速に動くバージョンを優先（最適化は後回し）
   - 実装中の判断事項は Implementation Log に記録

3. **動作確認**:
   ```bash
   # 既存テスト実行
   pytest tests/

   # 手動確認（GUI起動）
   python main.py
   ```

4. **Implementation Log記録**:
   - 実装した内容（ファイル・行数）
   - Design Specからの変更点（あれば）
   - 気づいた問題点・改善提案
   - 未実装項目（あれば理由も）

### 🤝 ハンドオフ準備
```bash
python scripts/task_manager.py complete-phase
```
→ 以下を生成：
- `handoff_to_claude.md`: Claudeへのレビュー依頼書
- 実装ファイルリスト
- 変更差分サマリー

---

## Phase 3: Refinement (Claude担当)

### 📌 目的
Gemini実装をレビューし、品質・保守性・セキュリティを向上させる。

### 📝 成果物
- **Review Report**: `.ftiv-task/TASK-XXX/review_report.md`
- **Refined Code**: 洗練されたコード（必要に応じて修正）

### ✅ 完了条件 (Definition of Done)
- [ ] コードレビュー完了（.agent/roles/code-reviewer.md 基準）
- [ ] SOLID原則・.agentルール適合確認済み
- [ ] セキュリティ脆弱性チェック済み
- [ ] パフォーマンス問題なし
- [ ] 過剰設計・不要コードの削除済み
- [ ] ドキュメント・コメント適切
- [ ] 全テスト通過

### 🔍 実施内容

1. **Implementation Log確認**:
   ```bash
   cat .ftiv-task/TASK-XXX/implementation_log.md
   cat .ftiv-task/TASK-XXX/handoff_to_claude.md
   ```

2. **コードレビュー** (.agent/roles/code-reviewer.md):
   - アーキテクチャ整合性
   - SOLID原則違反チェック
   - セキュリティ脆弱性（OWASP Top 10）
   - エラーハンドリング適切性
   - 命名規則・可読性

3. **品質向上**:
   - 不要なコード削除
   - 重複ロジックの抽出
   - 型ヒント追加・改善
   - ドキュメント文字列の精査

4. **テスト実行**:
   ```bash
   pytest tests/ -v
   ```

5. **Review Report作成**:
   - 実装の評価（Good / Needs Improvement）
   - 修正内容（あれば）
   - 残存リスク（あれば）
   - 次フェーズへの指示

### 🤝 ハンドオフ準備
```bash
python scripts/task_manager.py complete-phase
```
→ 以下を生成：
- `handoff_to_gemini_test.md`: Geminiへのテスト指示書
- テスト観点リスト（Phase 1から引用）

---

## Phase 4: Testing (Gemini担当)

### 📌 目的
包括的なテストスイートを作成し、品質を保証する。

### 📝 成果物
- **Test Suite**: `tests/` ディレクトリ内のテストファイル
- **Test Report**: `.ftiv-task/TASK-XXX/test_report.md`

### ✅ 完了条件 (Definition of Done)
- [ ] 全テストケースが実装済み（Phase 1テスト観点カバー）
- [ ] テストが全てパス（141/141等）
- [ ] カバレッジ確認済み（重要パスは100%）
- [ ] エッジケース・異常系テスト済み
- [ ] ドキュメント更新済み（必要なら）
- [ ] タスク完了確認済み

### 🔍 実施内容

1. **Review Report確認**:
   ```bash
   cat .ftiv-task/TASK-XXX/review_report.md
   cat .ftiv-task/TASK-XXX/handoff_to_gemini_test.md
   ```

2. **テストケース実装**:
   - Phase 1のテスト観点を全てカバー
   - 正常系・異常系・エッジケース
   - pytestフィクスチャ活用（qapp等）

3. **テスト実行**:
   ```bash
   pytest tests/ -v --cov=ui --cov-report=term
   ```

4. **ドキュメント更新**:
   - README.md（必要なら）
   - 翻訳ファイル（jp.json, en.json）
   - コメント・docstring

5. **Test Report作成**:
   - テスト結果サマリー（X/X passed）
   - カバレッジ報告
   - 発見したバグ（あれば）
   - 残タスク（あれば）

### 🎉 タスク完了
```bash
python scripts/task_manager.py complete-task
```
→ タスクがアーカイブされ、完了報告が生成される

---

## 🚨 例外フロー

### Phase中に問題発見（戻る必要がある場合）

```bash
# Phase 2 → Phase 1 へ戻る（設計不足判明）
python scripts/task_manager.py rollback-phase

# 理由を記録
echo "UIライブラリ選定が不明確" >> .ftiv-task/TASK-XXX/rollback_reason.md
```

### 緊急バグ修正（ワークフローをスキップ）

```bash
# Hotfix用の簡易タスク作成
python scripts/task_manager.py init-hotfix "レイアウトクラッシュ修正"
# → Phase 1-2-3のみ（テストは既存で確認）
```

---

## 📊 品質メトリクス

各フェーズ完了時に記録される指標：

| メトリクス | 目標値 | 測定方法 |
|------------|--------|----------|
| Design完全性 | 100% | ハンドオフチェックリスト通過率 |
| 実装スピード | < 2時間 | Phase 2所要時間 |
| レビュー指摘数 | < 5件 | Review Report |
| テストカバレッジ | > 80% | pytest-cov |
| 全体完了時間 | < 1日 | Phase 1-4 合計時間 |

---

## 🔧 トラブルシューティング

### Q: Geminiが指示を無視する
**A**: `handoff_to_gemini.md` の指示を**超具体的**に書き直す
```markdown
❌ "UIを改善してください"
✅ "ui/mindmap/mindmap_widget.py の _create_toolbar メソッド（150-200行）に、
    QPushButton を3つ追加してください。ボタンラベルは ['グループ化', '解除', '色変更'] です。"
```

### Q: Claudeが過剰設計する
**A**: Design Spec に**制約**を明記
```markdown
- 抽象化レベル: 最小限（今回の要件のみ実装）
- 新規クラス追加: 不可（既存クラス拡張のみ）
- パターン適用: Strategy/Observerのみ（新規パターン導入禁止）
```

### Q: フェーズ間で情報が消失
**A**: ハンドオフファイルに**全コンテキスト**を記載
```markdown
## 前提知識
- FTIVはPySide6製マインドマップアプリ
- .agent/roles/architect.md に従った開発
- Python 3.14 環境（.venv314）

## 現在の状況
- [状態の詳細...]
```

---

## 📚 参考資料

このワークフローは以下の業界標準を統合：
- [Spec-Driven Development (GitHub)](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-using-markdown-as-a-programming-language-when-building-with-ai/)
- [ADR Templates (adr.github.io)](https://adr.github.io/adr-templates/)
- [Handoff Best Practices (Simple Thread)](https://www.simplethread.com/handing-off-a-software-project/)
- [Agent SOPs (AWS)](https://aws.amazon.com/blogs/opensource/introducing-strands-agent-sops-natural-language-workflows-for-ai-agents/)

---

**最終更新**: 2026-01-26

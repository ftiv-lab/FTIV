# Hybrid AI Workflow クイックスタート

**5分で理解する Phase-Driven Development**

---

## 🎯 これは何？

ClaudeとGeminiを**戦略的に使い分けて**、高品質なコードを効率的に開発するためのワークフローシステムです。

- **Claude**: 設計・デバッグ・レビュー（品質重視）
- **Gemini**: 実装・テスト・大量作業（スピード重視）

両AIが明確なハンドオフで連携し、各フェーズの成果物をマークダウンで管理します。

---

## 🚀 30秒クイックスタート

### 1. タスク初期化（どちらのAIでもOK）
```bash
python scripts/task_manager.py init "ノードグルーピング機能"
```
→ `.ftiv-task/TASK-001/` が作成される

---

### 2. Phase 1: Design (Claude)
```bash
python scripts/task_manager.py start-phase 1
```

**Claudeでやること**:
1. `.agent/templates/phase_1_design.md` を開く
2. 要件整理・設計判断・実装仕様を記載
3. 完了したら:
   ```bash
   python scripts/task_manager.py complete-phase
   ```

→ `.ftiv-task/TASK-001/handoff_to_gemini.md` が生成される

---

### 3. Phase 2: Implementation (Gemini)
```bash
python scripts/task_manager.py start-phase 2
```

**Geminiでやること**:
1. `.ftiv-task/TASK-001/handoff_to_gemini.md` を読む
2. Design Spec通りに実装
3. `implementation_log.md` に実装内容を記録
4. 完了したら:
   ```bash
   python scripts/task_manager.py complete-phase
   ```

→ `.ftiv-task/TASK-001/handoff_to_claude.md` が生成される

---

### 4. Phase 3: Refinement (Claude)
```bash
python scripts/task_manager.py start-phase 3
```

**Claudeでやること**:
1. `.ftiv-task/TASK-001/handoff_to_claude.md` を読む
2. コードレビュー（.agent/roles/code-reviewer.md 基準）
3. 必要なら修正・洗練
4. `review_report.md` に評価を記録
5. 完了したら:
   ```bash
   python scripts/task_manager.py complete-phase
   ```

→ `.ftiv-task/TASK-001/handoff_to_gemini_test.md` が生成される

---

### 5. Phase 4: Testing (Gemini)
```bash
python scripts/task_manager.py start-phase 4
```

**Geminiでやること**:
1. `.ftiv-task/TASK-001/handoff_to_gemini_test.md` を読む
2. テストケース実装（Phase 1の観点を全カバー）
3. 全テスト実行・パス確認
4. `test_report.md` に結果を記録
5. 完了したら:
   ```bash
   python scripts/task_manager.py complete-task
   ```

→ タスクが `.ftiv-task/archive/` にアーカイブされる

---

## 🎊 完了！

`task_completion_report.md` が生成され、全成果物がアーカイブされます。

---

## 📊 実例：ノードグルーピング機能

### Phase 1 (Claude: 30分)
```markdown
# ADR: グループ管理方法の選択
- Option A: MindMapNode内に group_id 追加
- Option B: GroupManager クラスを新規作成 ← **採用**

理由: Single Responsibility、拡張性

# Design Spec
- ui/mindmap/components/group_manager.py 新規作成
- MindMapController に group_nodes() メソッド追加
- ツールバーにボタン3つ追加
```

---

### Phase 2 (Gemini: 1時間)
```python
# 実装
class GroupManager:
    def create_group(self, nodes: list[MindMapNode]) -> Group:
        # 実装...

# Implementation Log
- group_manager.py 新規作成（150行）
- mindmap_controller.py に group_nodes() 追加
- Design Specからの変更: なし
```

---

### Phase 3 (Claude: 20分)
```markdown
# Review Report
✅ アーキテクチャ適合性: SOLID原則遵守
✅ セキュリティ: リスクなし
⚠️ 改善: group_nodes() が長い（50行） → 分割

# 修正
- extract_method: _validate_group_nodes()
- 型ヒント追加
```

---

### Phase 4 (Gemini: 30分)
```python
# tests/mindmap/test_group_manager.py
def test_create_group_normal(qapp):
    """正常系: 複数ノードをグループ化."""
    # ...

def test_create_group_error_empty(qapp):
    """異常系: 空選択でエラー."""
    # ...

# Test Report
✅ 8/8 passed
✅ カバレッジ 95%
```

---

## 🛠️ よくある質問

### Q: Phase中に「設計が不足している」と気づいたら？
**A**: ロールバック
```bash
python scripts/task_manager.py rollback-phase
echo "UIライブラリ選定が不明確" >> .ftiv-task/TASK-XXX/rollback_reason.md
```

---

### Q: 緊急バグ修正で全フェーズ不要な場合は？
**A**: Hotfix
```bash
python scripts/task_manager.py init-hotfix "レイアウトクラッシュ修正"
# → Phase 1-2-3のみ（テストは既存で確認）
```

---

### Q: 現在のタスク状態を確認したい
**A**: Status
```bash
python scripts/task_manager.py status
```

---

## 💡 成功のコツ

### 1. **Phase 1で時間をかける**
曖昧な設計 → Phase 2で迷走 → ロールバック → 時間ロス

明確な設計 → Phase 2が高速 → Phase 3の修正最小

### 2. **ハンドオフファイルは具体的に**
❌ "良い感じに実装"
✅ "ui/controllers/mindmap_controller.py の85-95行に、以下のロジックを追加"

### 3. **Implementation Logは即記録**
実装中にリアルタイムで記録。後から思い出すのは困難。

### 4. **完了条件を厳守**
Phase完了チェックリストを必ず全てチェック。

---

## 📚 詳細ドキュメント

- **ワークフロー全体**: `.agent/workflows/hybrid_ai_workflow.md`
- **AI選択ガイド**: `.agent/strategies/ai_usage_strategy.md`
- **ハンドオフ**: `.agent/handoffs/checklist.md`
- **テンプレート**: `.agent/templates/phase_*.md`

---

**最終更新**: 2026-01-26
**あなたのプロジェクトが加速しますように！** 🚀

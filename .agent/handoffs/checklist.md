# AI Handoff Checklist

**目的**: AI間のハンドオフ時に、必要な情報が全て引き継がれることを保証する。

---

## Phase 1 → Phase 2 (Claude → Gemini)

### 📤 Claude（送信側）の責任

#### 成果物確認
- [ ] `adr.md` が完成している
- [ ] `design_spec.md` が完成している
- [ ] 実装手順が**具体的**（曖昧さゼロ）
- [ ] 全ファイルパス・行数が明記されている
- [ ] テスト観点が列挙されている

#### ハンドオフファイル生成
```bash
python scripts/task_manager.py generate-handoff
```

自動生成される `.ftiv-task/{{TASK_ID}}/handoff_to_gemini.md` に以下が含まれることを確認：

- [ ] **タスク概要** - 1-2文で何を実装するか
- [ ] **実装範囲** - ファイルリストと変更内容
- [ ] **重要な制約** - "これはやらない" リスト
- [ ] **コーディング指針** - 命名規則、エラーハンドリング方針
- [ ] **動作確認方法** - 手動テストの手順
- [ ] **次フェーズへの引き継ぎ事項** - Claudeに確認してほしいこと

#### 品質確認
- [ ] .agent ルール適合性確認済み
- [ ] SOLID原則違反なし
- [ ] セキュリティリスク評価済み

---

### 📥 Gemini（受信側）の責任

#### ハンドオフ受領確認
```bash
# 必ず最初に実行
cat .ftiv-task/{{TASK_ID}}/design_spec.md
cat .ftiv-task/{{TASK_ID}}/handoff_to_gemini.md
```

- [ ] Design Specを全て読んだ
- [ ] 不明点がないことを確認した
- [ ] 実装範囲を理解した

#### 不明点がある場合
**Phase 1に戻る**（ロールバック）：
```bash
python scripts/task_manager.py rollback-phase
echo "設計が不明確: XXXの実装方法が不明" >> .ftiv-task/{{TASK_ID}}/rollback_reason.md
```

---

## Phase 2 → Phase 3 (Gemini → Claude)

### 📤 Gemini（送信側）の責任

#### 成果物確認
- [ ] `implementation_log.md` が完成している
- [ ] 実装コードが動作する（手動確認済み）
- [ ] Design Specからの変更点が記録されている
- [ ] 既存テストがパスする（or 失敗理由記載）
- [ ] 発見した問題・改善提案が記録されている

#### ハンドオフファイル生成
```bash
python scripts/task_manager.py generate-handoff
```

自動生成される `.ftiv-task/{{TASK_ID}}/handoff_to_claude.md` に以下が含まれることを確認：

- [ ] **実装サマリー** - 何を実装したか
- [ ] **変更ファイルリスト** - 追加・変更したファイル
- [ ] **Design Specからの変更** - 変更点と理由
- [ ] **Claudeに確認してほしいこと** - レビュー重点項目
- [ ] **気づいた問題** - バグ・技術的負債・改善提案
- [ ] **動作確認結果** - テスト結果・スクリーンショット

#### コミット準備（任意）
```bash
git add [変更ファイル]
git status
# → Claudeがレビュー後にコミット
```

---

### 📥 Claude（受信側）の責任

#### ハンドオフ受領確認
```bash
# 必ず最初に実行
cat .ftiv-task/{{TASK_ID}}/implementation_log.md
cat .ftiv-task/{{TASK_ID}}/handoff_to_claude.md
```

- [ ] Implementation Logを全て読んだ
- [ ] 実装内容を理解した
- [ ] レビュー重点項目を把握した

#### レビュー実行
- [ ] .agent/roles/code-reviewer.md に従ってレビュー
- [ ] SOLID原則チェック
- [ ] セキュリティチェック
- [ ] パフォーマンスチェック

---

## Phase 3 → Phase 4 (Claude → Gemini)

### 📤 Claude（送信側）の責任

#### 成果物確認
- [ ] `review_report.md` が完成している
- [ ] 修正内容が記録されている（あれば）
- [ ] 全テストがパスする
- [ ] 残存リスク・技術的負債が記録されている

#### ハンドオフファイル生成
```bash
python scripts/task_manager.py generate-handoff
```

自動生成される `.ftiv-task/{{TASK_ID}}/handoff_to_gemini_test.md` に以下が含まれることを確認：

- [ ] **テスト実装項目** - Phase 1のテスト観点から具体的なテストケースへ変換
- [ ] **pytestコード例** - テンプレートコード
- [ ] **重点確認項目** - パフォーマンス基準等
- [ ] **注意事項** - qappフィクスチャ使用等

---

### 📥 Gemini（受信側）の責任

#### ハンドオフ受領確認
```bash
# 必ず最初に実行
cat .ftiv-task/{{TASK_ID}}/review_report.md
cat .ftiv-task/{{TASK_ID}}/handoff_to_gemini_test.md
```

- [ ] Review Reportを全て読んだ
- [ ] テスト実装項目を理解した
- [ ] 重点確認項目を把握した

#### テスト実装
- [ ] Phase 1のテスト観点を全てカバー
- [ ] Phase 3の重点確認項目をカバー

---

## Phase 4完了 → タスクアーカイブ

### 📦 Gemini（最終担当）の責任

#### 完了確認
- [ ] 全テストが通過（XXX/XXX passed）
- [ ] ドキュメント更新済み
- [ ] タスクの受け入れ基準を全て満たしている

#### タスク完了処理
```bash
python scripts/task_manager.py complete-task
```

これにより以下が実行される：
1. `.ftiv-task/{{TASK_ID}}/` が `.ftiv-task/archive/` に移動
2. `task_completion_report.md` が生成される
3. 完了通知が表示される

---

## 🚨 緊急時の対応

### ロールバック（前フェーズに戻る）
設計不足・実装不可能等が判明した場合：
```bash
python scripts/task_manager.py rollback-phase
echo "詳細な理由" >> .ftiv-task/{{TASK_ID}}/rollback_reason.md
```

### ホットフィックス（ワークフローをスキップ）
緊急バグ修正等、フルワークフローが不要な場合：
```bash
python scripts/task_manager.py init-hotfix "バグ修正タイトル"
# → Phase 1-2-3のみ（テストは既存で確認）
```

---

## 📊 ハンドオフ品質メトリクス

各ハンドオフ後に以下を記録し、改善に活用：

| メトリクス | 目標値 | 測定方法 |
|------------|--------|----------|
| ハンドオフ完全性 | 100% | チェックリスト通過率 |
| ロールバック発生率 | < 10% | ロールバック回数 / 総タスク数 |
| 引き継ぎ情報不足による遅延 | 0回 | Phase開始後の質問回数 |
| ハンドオフ所要時間 | < 10分 | チェックリスト確認時間 |

---

## 💡 ハンドオフのベストプラクティス

### ✅ 良いハンドオフ
```markdown
## 実装範囲
ui/controllers/mindmap_controller.py の add_child_node メソッド（85-95行）に、
以下のロジックを追加してください：

1. 新規ノードの座標を calculate_position() で計算
2. layout_mode が "auto" の場合のみ、arrange_tree() を呼び出す
3. sig_node_added シグナルを発行

**制約**: 既存の parent.get_child_nodes() ロジックは変更しないこと
```

### ❌ 悪いハンドオフ
```markdown
## 実装範囲
マインドマップに子ノード追加機能を実装してください。
良い感じにお願いします。
```

**問題点**: 曖昧で、Geminiが何をすべきか不明確

---

**最終更新**: 2026-01-26

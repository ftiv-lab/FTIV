# Phase 1: Design (Claude担当)

**Task ID**: `{{TASK_ID}}`
**Task Title**: `{{TASK_TITLE}}`
**Started**: `{{START_TIME}}`
**AI**: Claude ({{MODEL_NAME}})

---

## 1️⃣ 要件整理

### 📋 ユーザー要求（原文）
```
{{USER_REQUEST}}
```

### 🎯 機能仕様（具体化）
<!-- ユーザー要求を具体的な機能仕様に変換 -->

**機能名**: [機能の簡潔な名前]

**目的**: [なぜこの機能が必要か？ユーザーにとっての価値]

**主要機能**:
- [ ] [機能1の詳細]
- [ ] [機能2の詳細]
- [ ] [機能3の詳細]

**受け入れ基準** (Acceptance Criteria):
1. [条件1が満たされている]
2. [条件2が満たされている]
3. [条件3が満たされている]

**スコープ外**（今回やらないこと）:
- [将来的には必要だが、今回は含めない項目]

---

## 2️⃣ 影響範囲分析

### 📂 変更対象ファイル
<!-- grep/glob等で調査した結果を記載 -->

| ファイルパス | 変更理由 | 変更規模 |
|-------------|---------|---------|
| `ui/controllers/mindmap_controller.py` | [理由] | 小/中/大 |
| `ui/mindmap/mindmap_node.py` | [理由] | 小/中/大 |
| ... | ... | ... |

### 🔗 依存関係
<!-- この変更が影響する他のモジュール -->
- **上流依存**: [このモジュールが依存しているもの]
- **下流影響**: [この変更で影響を受けるモジュール]

### ⚠️ リスク評価

| リスク | 深刻度 | 対策 |
|--------|--------|------|
| [リスク1: 例: 既存機能の破壊] | 高/中/低 | [対策] |
| [リスク2] | 高/中/低 | [対策] |

---

## 3️⃣ アーキテクチャ決定記録 (ADR)

### 🤔 検討した選択肢

#### Option A: [選択肢Aの名前]
**概要**: [どういうアプローチか]

**メリット**:
- [メリット1]
- [メリット2]

**デメリット**:
- [デメリット1]
- [デメリット2]

**実装コスト**: 小/中/大

---

#### Option B: [選択肢Bの名前]
**概要**: [どういうアプローチか]

**メリット**:
- [メリット1]
- [メリット2]

**デメリット**:
- [デメリット1]
- [デメリット2]

**実装コスト**: 小/中/大

---

### ✅ 最終決定: [選択したOption]

**選定理由**:
1. [理由1: 例: 業界標準に準拠]
2. [理由2: 例: 拡張性が高い]
3. [理由3: 例: .agentルールに適合]

**トレードオフの受容**:
- [受け入れるデメリット1]
- [受け入れるデメリット2]

**参考資料**:
- [業界標準ドキュメントURL]
- [類似実装の参考コード]

---

## 4️⃣ 設計仕様書 (Design Spec)

### ⚠️ 設計粒度ガイド（重要）

**Geminiに実装を任せるため、完全なコードは書かない。**

| 書くべきこと | 書かないこと |
|------------|-------------|
| クラス名・メソッドシグネチャ | 完全な実装コード |
| 責務・入出力の説明 | 具体的なアルゴリズム詳細 |
| 「何を」「なぜ」の詳細 | 「どう」の詳細（Geminiに任せる） |
| 参考にすべき既存コード | コピペ可能な完成コード |

**良い例**:
```python
def _paint_background_only(self, painter: QPainter, node: "MindMapNode") -> None:
    """編集モード中に背景のみを描画する。

    責務:
    - node.config から描画パラメータを取得
    - 角丸長方形を QPainter で描画

    参考: SimpleNodeRenderer の背景描画ロジック
    """
    pass  # 実装は Gemini に委ねる
```

**悪い例**（実装を全部書いてしまう）:
```python
def _paint_background_only(self, painter: QPainter, node: "MindMapNode") -> None:
    bg_color = QColor(node.config.background_color)
    border_color = QColor(node.config.border_color)
    corner_radius = node.config.font_size * node.config.background_corner_ratio
    rect = QRectF(0, 0, node._width, node._height)
    painter.setPen(QPen(border_color, 2))
    painter.setBrush(QBrush(bg_color))
    painter.drawRoundedRect(rect, corner_radius, corner_radius)
```

---

### 🏗️ クラス構造

#### 新規クラス: `[ClassName]`
**ファイル**: `[ファイルパス]`

**責務**: [このクラスの単一責任]

**属性**:
```python
class ClassName:
    def __init__(self):
        self.attribute1: Type = ...  # [説明]
        self.attribute2: Type = ...  # [説明]
```

**メソッド**:
```python
def method_name(self, param: Type) -> ReturnType:
    """[メソッドの目的].

    Args:
        param: [パラメータ説明]

    Returns:
        [戻り値説明]

    Raises:
        ExceptionType: [例外が発生する条件]
    """
    pass
```

---

#### 既存クラス変更: `[ClassName]`
**ファイル**: `[ファイルパス]`
**変更行**: [XX-YY行目付近]

**変更内容**:
- [ ] メソッド `method_name` を追加（シグネチャ: `...`）
- [ ] 属性 `attribute` を追加（型: `Type`）
- [ ] メソッド `old_method` を削除（理由: `...`）

**後方互換性**: 維持する / 破壊する（理由: `...`）

---

### 🔄 データフロー

```
[ユーザーアクション]
   ↓
[UI Component] (mindmap_widget.py)
   ↓ signal: sig_xxx
[Controller] (mindmap_controller.py)
   ↓ method: process_xxx()
[Model/Data] (mindmap_node.py)
   ↓ update
[View Update] (canvas.update())
```

---

### 🛡️ エラーハンドリング方針

| エラーケース | 処理方法 | ユーザーへの通知 |
|-------------|---------|------------------|
| [例: 入力値不正] | [例: ValueError raise] | [例: QMessageBox警告表示] |
| [例: ファイル読み込み失敗] | [例: デフォルト値使用] | [例: ログに記録のみ] |

---

### 🎨 UI設計（該当する場合）

**変更箇所**: [ツールバー / ダイアログ / etc]

**追加要素**:
- ボタン: [ラベル], [アイコン], [動作]
- 入力欄: [型], [バリデーション]

**レイアウト図** (ASCII or 説明):
```
+---------------------------+
| [Btn1] [Btn2] [Btn3]     |
+---------------------------+
```

---

## 5️⃣ テスト観点

### ✅ 正常系テスト
1. [テストケース1: 例: ノード追加→グループ化成功]
2. [テストケース2]
3. [テストケース3]

### ⚠️ 異常系テスト
1. [テストケース1: 例: ノード未選択でグループ化→エラー表示]
2. [テストケース2]

### 🔬 エッジケーステスト
1. [テストケース1: 例: 1000ノード選択→パフォーマンス]
2. [テストケース2: 例: 空文字列入力]

### 🔄 回帰テスト
- [ ] 既存機能Xが引き続き動作する
- [ ] 既存テストが全てパスする

---

## 6️⃣ 実装手順（Gemini向け）

### Step 1: [ステップ名]
**ファイル**: `[ファイルパス]`
**操作**: [追加 / 変更 / 削除]

**詳細**:
```python
# この位置に追加（XX行目付近）
def new_method(self, param: Type) -> ReturnType:
    # [実装のポイント]
    pass
```

---

### Step 2: [ステップ名]
**ファイル**: `[ファイルパス]`
**操作**: [追加 / 変更 / 削除]

**詳細**:
[具体的な指示]

---

### Step N: 動作確認
```bash
# 既存テスト実行
pytest tests/mindmap/ -v

# 手動確認
python main.py
# → [確認項目1]
# → [確認項目2]
```

---

## 7️⃣ .agent ルール適合性チェック

- [ ] **architect.md**: "10年後も保守可能か？" → YES / 懸念事項: [...]
- [ ] **SOLID原則**:
  - [ ] Single Responsibility: 各クラスが単一責任
  - [ ] Open/Closed: 拡張に開放、修正に閉鎖
  - [ ] Liskov Substitution: 継承関係が適切
  - [ ] Interface Segregation: 不要な依存なし
  - [ ] Dependency Inversion: 抽象に依存
- [ ] **セキュリティ**: OWASP Top 10該当なし
- [ ] **qt_signal_slot_pattern.md**: シグナル接続が規約準拠

**懸念事項**（あれば）:
- [懸念1とその対策]

---

## 🤝 Phase 1完了チェックリスト

設計完了前に、以下を全て確認してください：

- [ ] 要件が明確化されている（曖昧さ0%）
- [ ] 影響範囲が特定されている（変更ファイルリスト作成済み）
- [ ] 設計判断とトレードオフが記録されている（ADR完成）
- [ ] 実装手順が具体的（Geminiが迷わない粒度）
- [ ] テスト観点がリストアップされている
- [ ] .agent ルール適合性確認済み

**全てチェックOK？** → `python scripts/task_manager.py complete-phase` を実行してPhase 2へ

---

**設計完了日時**: `{{END_TIME}}`
**次フェーズ**: Phase 2 (Gemini Implementation)

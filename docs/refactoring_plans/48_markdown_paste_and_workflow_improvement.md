# 48: マークダウンペースト機能改善 & ワークフロー整理

**作成日**: 2025-01-27
**ステータス**: 完了

---

## 概要

本セッションでは以下の2つの作業を実施した：

1. **マークダウンペースト機能の改善** (TDD方式)
2. **Claude Code / Gemini 連携ワークフローの整理**

---

## 1. マークダウンペースト機能改善

### 背景・課題

- マークダウンをコピー＆ペーストでマインドマップに変換する機能が不十分だった
- 対応フォーマットが限定的（`#` ヘッダーと `-/*+` ブレットのみ）
- ペースト失敗時のフィードバックがなかった

### 実施内容

#### A. パース統計機能の追加

**ファイル**: `ui/mindmap/utils/markdown_importer.py`

```python
class ParseStats(TypedDict):
    total_lines: int      # 処理対象行数
    parsed_lines: int     # パース成功行数
    skipped_lines: int    # スキップ行数
    node_count: int       # 作成ノード数

class ParseResult(TypedDict):
    nodes: List[Dict]
    stats: ParseStats

def parse_markdown_with_stats(self, text: str) -> ParseResult:
    """統計情報付きでパースを実行"""
```

#### B. 寛容なパース対応

追加対応フォーマット：

| フォーマット | 例 | インデント単位 |
|-------------|-----|---------------|
| 番号付きリスト | `1.`, `2.`, `3.` | 3スペース |
| プレーンテキスト | インデントのみ | 4スペース |

**変更箇所**: `_parse_line_extended()` メソッド

#### C. プレビューダイアログの追加

**ファイル**: `ui/dialogs.py`

```python
class MarkdownPastePreviewDialog(BaseTranslatableDialog):
    """ペースト前にパース結果をツリー表示で確認"""
```

機能：
- パース統計の表示（成功: 緑背景、失敗: 赤背景）
- ツリー形式でノード構造をプレビュー
- 元テキストの折りたたみ表示
- パース失敗時はOKボタン無効化

#### D. ペースト処理の更新

**ファイル**: `ui/mindmap/mindmap_widget.py`

```python
def _handle_paste(self) -> None:
    # 1. クリップボードからテキスト取得
    # 2. プレビューダイアログ表示
    # 3. ユーザー確認後にノード作成
```

**ファイル**: `ui/controllers/mindmap_controller.py`

```python
def paste_nodes_from_parsed_data(
    self, root_dicts: list, target_parent: Optional[MindMapNode] = None
) -> int:
    """パース済みデータからノードを作成"""
```

#### E. 翻訳キーの追加

**ファイル**: `utils/locales/jp.json`, `utils/locales/en.json`

```json
"title_markdown_paste_preview": "Markdownペースト プレビュー",
"label_node_text": "ノードテキスト",
"label_node_level": "レベル",
"grp_original_text": "元のテキスト（クリックで展開）",
"msg_markdown_parse_failed": "パースに失敗しました（{total}行中、{skipped}行が認識できませんでした）",
"msg_markdown_parse_success": "{nodes}個のノードを作成します（{total}行中{parsed}行をパース）",
"msg_paste_result": "{count}個のノードを作成しました"
```

### テスト

**ファイル**: `tests/mindmap/test_markdown_integration.py`

追加テスト（5件）：
- `test_parse_markdown_with_stats_returns_statistics`
- `test_parse_markdown_with_stats_empty_input`
- `test_import_numbered_list`
- `test_import_plain_text_with_indent`
- `test_import_mixed_formats`

**結果**: 全146テスト PASS

---

## 2. ワークフロー整理

### 背景・課題

- 4フェーズのワークフロー（`.agent/templates/`）が複雑すぎた
- Claude Codeに「設計」を頼んでもコードが出てきてしまう
- 小さいタスクには過剰なプロセス

### 実施内容

#### A. グローバルルールの作成

**ファイル**: `~/.claude/rules/workflow-guide.md`

内容：
- タスクサイズ判定基準（S/M → 直接実装、L/XL → 設計モード）
- 設計モードの出力フォーマット定義
- 「コードを書かない」設計書の構成

#### B. ハンドオフフォルダの作成

**ファイル**: `.agent/handoff/README.md`

用途：Claude Codeが出力した設計書をGeminiに渡すための場所

#### C. 旧テンプレートのアーカイブ

移動先: `.agent/templates/_archive/`

アーカイブしたファイル：
- `phase_1_design.md`
- `phase_2_implementation.md`
- `phase_3_refinement.md`
- `phase_4_testing.md`
- `テンプレートの使い方.md`

### 新しい構成

```
~/.claude/rules/
├── (Everything Claude Code の8ファイル)
└── workflow-guide.md      ← NEW

.agent/
├── handoff/               ← NEW: Gemini向け出力先
│   └── README.md
└── templates/
    └── _archive/          ← 旧システム保管
```

### 使い方

| タスクサイズ | アクション |
|-------------|-----------|
| S/M（小〜中） | Claude Codeに直接「実装して」 |
| L/XL（大〜特大） | 「設計して」→ `.agent/handoff/` に出力 → Geminiに渡す |

---

## 変更ファイル一覧

### 新規作成
- `~/.claude/rules/workflow-guide.md`
- `.agent/handoff/README.md`

### 変更
- `ui/mindmap/utils/markdown_importer.py`
- `ui/dialogs.py`
- `ui/mindmap/mindmap_widget.py`
- `ui/controllers/mindmap_controller.py`
- `utils/locales/jp.json`
- `utils/locales/en.json`
- `tests/mindmap/test_markdown_integration.py`

### 移動（アーカイブ）
- `.agent/templates/phase_*.md` → `.agent/templates/_archive/`

---

## 備考

- Everything Claude Code（rules/commands）を `~/.claude/` にインストール済み
- TDDワークフローで実装（RED → GREEN → REFACTOR）
- 全テスト通過確認済み

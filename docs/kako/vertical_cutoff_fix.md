# Vertical Text Cutoff Fix Plan

## 1. 現状分析 (Current Situation)
ユーザー報告: 「縦書きで新しいテキストが途切れる」
**原因 (Root Cause):**
描画ロジック（Renderer）とサイズ計算ロジック（Sizing）の不一致です。

| Logic | Formula | Example (10 chars) |
|---|---|---|
| **Drawing (New)** | `y += fm.height()` | 120px * 10 = **1200px** |
| **Sizing (Old)** | `h = font_size * count` | 100px * 10 = **1000px** |

結果として、**200px不足** し、末尾の文字がキャンバス外にはみ出して消えます（Cutoff）。

---

## 2. 改善提案 (Improvement Proposal)

### 📐 Engineering Specialist (Refactoring)
> **"Container must fit the Content."**

サイズ計算ロジックも `QFontMetrics` を基準にするよう修正します。

**Target Files:**
*   `windows/text_renderer.py`
    *   `_render_vertical`
    *   `_paint_direct_vertical`

**Changes:**
1.  `fm = QFontMetrics(font)` を初期化。
2.  高さ計算式を変更:
    *   Before: `(window.font_size + char_spacing) * max_chars_per_line`
    *   After: `(fm.height() + char_spacing) * max_chars_per_line`

### 🎨 QA Specialist (Test Case)
この修正が完了すると、自動的に「途切れていた文字」が現れるはずです。
また、以前修正した「重なり」も解消されたまま、適切な余白を持って表示されます。

---

## 3. 実装ステップ

1.  **Rendering Sync**:
    `text_renderer.py` の `_render_vertical` と `_paint_direct_vertical` に `QFontMetrics` を導入し、高さ計算を修正します。

2.  **Verification**:
    `verify_all.bat` を実行し、既存のテスト（特に高解像度テスト `test_spacing_split.py`）がこの変更（Canvasサイズの拡大）を許容パスすることを確認します。
    *   `test_spacing_split.py` は「変化すること」を確認しているので、サイズが変わってもロジックが正しければパスするはずです。

## 4. 承認依頼
この修正により、ウィンドウサイズが以前より「縦に長く」なりますが、これは文字を正しく表示するために不可欠な変更です。
よろしいでしょうか？

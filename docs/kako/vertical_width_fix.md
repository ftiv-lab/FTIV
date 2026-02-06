# Vertical Width Cutoff Fix: The "Wide" Character Problem

## 1. High Resolution Analysis (Root Cause)
「横幅（左右）がギリギリで、一部の漢字が見切れる」原因は、**縦書き列の幅（Column Width）を `font_size` (1em) で固定しているため** です。

*   **Logic**: `width = num_lines * font_size ...`
*   **Reality**: 「薔薇」「鬱」などの画数の多い漢字や、デザインされたフォントのグリフは、`1em` ボックスよりもわずかに横にはみ出して描画されることがあります（アンチエイリアスやヒゲ部分）。
*   **Result**: 100px のフォントサイズに対して、実体が 102px あると、両端 1px ずつが見切れてしまいます。

## 2. Improvement Proposal (Specialist Solution)

### 📐 Adaptive Column Width
列幅を固定の `font_size` ではなく、**「そのフォントの最大文字幅（Max Glyph Width）」** または **「安全マージン込みのサイズ」** に拡張します。

#### Approach A: Use `fm.maxWidth()`?
`fm.maxWidth()` はフォント内の「最も幅広なグリフ」の幅を返しますが、一部の記号などで極端に大きい場合があり、列間隔がスカスカになるリスクがあります。

#### Approach B: Calculated Safe Width (Recommended)
`font_size` と `fm.horizontalAdvance(text)` の最大値、または `font_size` にわずかな「呼吸用の余裕（Breathing Room）」を持たせます。

今回は **「表示しているテキストの中で最も幅の広い文字」** に合わせて列幅を決定する「Dynamic Fitting」を採用します。

```python
# Before
col_width = window.font_size

# After
# テキストに含まれる文字の中で最大の幅を取得
max_char_width = max(fm.horizontalAdvance(c) for c in text) if text else 0
# 少なくとも font_size は確保しつつ、はみ出しがあれば拡張する
col_width = max(window.font_size, max_char_width)
```
※ 縦書きなので `horizontalAdvance` が「文字の横幅（左右の厚み）」に相当します。

### 結果 (Outcome)
「薔薇」のような幅広な文字が含まれていれば、その分だけ列幅が自動的に広がり、見切れなくなります。

---

## 3. Implementation Steps
1.  **Refactor `text_renderer.py` (_render_vertical & _paint_direct_vertical)**:
    *   計算ロジックに `col_width = max(window.font_size, max(fm.horizontalAdvance(c) for c in lines...))` を追加。
    *   `width` 計算で `window.font_size` の代わりに `col_width` を使用。
    *   描画時の `cx` (中心X) 計算にも `col_width` を考慮する（あるいは `col_width` の中心に配置する）。

2.  **Verification**:
    *   幅広文字を含むテキストで、左右が見切れていないか確認。
    *   `verify_all.bat` を通過することを確認。

この修正で、どんなに複雑な漢字が来ても、「窮屈さ」から解放されます。

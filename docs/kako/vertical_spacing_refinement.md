# Vertical Spacing Refinement: "The Goldilocks Zone"

## 1. 現状の課題 (Current Analysis)

### ユーザーの声
> "縦書きの場合、新しいテキスト...の間が横書きに比べて、広すぎる面があります"
> "行を無理やり使ってる？みたいな面があって"

### 技術的背景 (High Resolution Analysis)
現在の実装 (`y += fm.height()`) は、**「技術的には正しいが、タイポグラフィ的には行き過ぎ」** な状態です。

*   **`fm.height()` の正体**: `Ascent` + `Descent` + `Leading` (行間)
*   **横書きの場合**: 文字送りは `horizontalAdvance` (文字幅) であり、`height` (行高) は使いません。
*   **縦書きの場合**: 現在 `fm.height()` を文字送りに使っているため、**「すべての文字の間に行間（Leading）が挿入されている」** 状態です。これが「間が抜けすぎている」原因です。

しかし、以前の `font_size` (1 EM) では、アセンダ/ディセンダが長いフォント（Meiryoなど）で重なりが発生しました。

---

## 2. 改善計画 (Refinement Plan)

### Goal: "Tight but Clean"
「余白0」の定義を、**「文字本体が接するギリギリ（Solid Height）」** または **「標準的な1文字分（1 EM）」** に再定義します。

### Strategy A: Solid Height Logic (推奨)
`fm.height()` から `fm.leading()` (余分な行間) を除いた値を使用します。

```python
# Before (Too Wide)
step = fm.height()

# After (Solid)
step = fm.height() - fm.leading()
# または fm.ascent() + fm.descent()
```
これにより、文字の「ヒゲ」同士が触れる程度まで詰まり、自然な「ベタ組み」になります。

### Strategy B: Sizing Synchronization (Cutoff Fix)
前のステップで発覚した「途切れ」も同時に直します。
箱の計算（`text_window.py`）と中身の計算（`text_renderer.py`）で、**完全に同じ計算式** を使うようにリファクタリングします。

*   **DRY原則**: 計算ロジックを `TextRenderer.calculate_text_metrics(window)` のようなヘルパーメソッド、または `TextWindowConfig` のプロパティとして共通化することを検討します（今回はまずRenderer内のロジック統一を優先）。

---

## 3. Implementation Steps

1.  **Renderer Update**:
    `text_renderer.py` の `_render_vertical` と `_paint_direct_vertical` を修正。
    *   Step calculation: `step = fm.ascent() + fm.descent()` (Leading除外)

2.  **Sizing Update**:
    `text_renderer.py` 内のサイズ計算部分（`_render_vertical` 内の `total_height` 計算）も上記 `step` と同一にする。
    *   **重要**: `TextWindow` 側ではなく `TextRenderer` が `pixmap` を返す際に決定する `canvas_size` が正しければ、Windowサイズはそれに追従する仕組みになっています（`InlineEditorMixin` 参照）。ユーザーが "Sizing Logic" と呼んでいたのは Renderer 内の `total_height` 計算のことです。

3.  **Validation**:
    *   間隔が「広すぎず、かつ重ならない」ことを確認。
    *   テキストが途切れないことを確認。

## 4. スペシャリスト・コメント
以前の苦悩（枠に入らない、重なる）は、**「フォントメトリクスの成分（Ascent/Descent/Leading）を理解せず、フォントサイズ（EM）だけで全てを制御しようとした」** ことに起因します。
今回の修正で、フォントの「実体」に基づいた制御になり、どんなフォントでも破綻しない堅牢なレンダラーになります。

この方針で修正を実行します。

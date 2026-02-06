# Vertical Text Rendering Refactoring Plan

## 1. 現状の課題 (Current Issues)
ユーザー報告: 「縦書きの余白を0にしても文字が被る」
コード解析: `windows/text_renderer.py`

### Root Cause Analysis
1.  **不適切な行送り (Incorrect Vertical Step)**:
    *   `y += window.font_size + margin` (Line 1059)
    *   文字の送りを「フォントサイズ（ピクセル数）」で固定しています。
    *   しかし、一般的なフォントの描画領域（Bounding Box）はフォントサイズよりも大きいです（アセンダ/ディセンダ等のため）。
    *   結果: `font_size=100` で描画しても、実際の文字高さが `120` ある場合、次の文字が `20px` 重なります。

2.  **Magic Numbers in Transform**:
    *   `_get_vertical_char_transform` (Line 1071~)
    *   位置合わせのために `window.font_size * 0.75` や `-0.55` といったハードコードされた補正値が散乱しています。
    *   これらは「ズレを無理やり直す」ための応急処置であり、フォントが変わると狂います。

---

## 2. 修正方針 (Refactoring Strategy)

### Goal: "Zero Spacing = Standard Typography"
余白設定が `0` のとき、フォントデザイナーが意図した通りの「標準的な隙間（Standard Leading）」で表示される状態をベースラインとします。

### Step 1: フォントメトリクスの採用
`window.font_size` ではなく、`QFontMetrics` から正しい高さを取得します。

```python
# Before
line_height = window.font_size

# After
fm = QFontMetrics(font)
line_height = fm.height()  # ascent + descent
# または
line_height = fm.lineSpacing()  # height + externalLeading
```

### Step 2: 垂直スタッキングロジックの刷新 (`_draw_vertical_text_content`)
文字の中心 (`cx, cy`) を基準にする現在のロジックは、回転（縦書き）には便利ですが、積み上げ計算が複雑になります。
「枠の上端」を基準にし、そこから `ascent` 分だけ下げて描画する標準的なベースライン方式に寄せます。

*   **変更点**:
    *   `y` のインクリメントを `fm.height()` ベースにする。
    *   `margin` (隙間) は `line_height` に加算する形にする。

### Step 3: Magic Number の排除
`_get_vertical_char_transform` 内の `、。` に対する `0.75`, `-0.55` 等の補正値を削除し、`boundingRect` の中心合わせ等の動的な計算（または `QFontMetrics` の正しい値）に置き換えます。

---

## 3. 安全な移行ステップ (Safety First)

1.  **Create Verify Script**:
    *   現在の「被っている状態」を再現するテストケース（または視覚確認用のスクリプト）を作成します。
2.  **Fix Vertical Step**:
    *   まず `y += ...` の部分だけを `fm.height()` に修正し、重なりが解消されるか確認します（これが最も効果が高い）。
3.  **Clean Transforms**:
    *   次に、個別の文字（句読点など）の微調整ロジックを整理します。

## 4. 承認依頼
この「メトリクス主導」への変更は、既存の見た目（特にギリギリまで詰めていた設定）を「少し広げる」方向に変化させる可能性があります。
しかし、これこそが「正しい」状態であり、ユーザーが求めている「デフォルトで綺麗」な状態です。
この方針で実装を進めます。

# First Character Cutoff Fix: The Centering Mismatch

## 1. High Resolution Analysis (Root Cause)
「始まりの一文字目の上が切れる」原因は、**「配置セルの高さ」と「文字の実体高さ」の不一致** です。

*   **Current Logic**:
    *   文字の配置中心 (`cy`) を `y + font_size / 2.0` で計算しています。
    *   例: Font Size 100px の場合、`y + 50px` を中心とみなします。
*   **The Mismatch**:
    *   実際の文字（Glyph）の高さは `Ascent + Descent` (例: 120px) です。
    *   この 120px の文字を 100px の中心（+50px地点）に置くと、上端は `50 - (120/2) = -10px` となります。
    *   つまり、**開始位置 (`y_start`) より 10px 上にはみ出します**。これが「切れる」原因です。

## 2. Improvement Proposal (Specialist Solution)

### 📐 Cell Height Synchronization
中心座標 (`cy`) の計算にも、ステップ移動と同じ **「実体高さ (Solid Height)」** を使用します。

```python
# Before (Cutoff Risk)
cell_height = window.font_size  # Too small!
cy = y + cell_height / 2.0

# After (Perfect Fit)
cell_height = fm.ascent() + fm.descent() # Matches the glyph
cy = y + cell_height / 2.0
```

### 結果 (Outcome)
*   **Center**: `y + 60px` (例)
*   **Top**: `60px - 60px = 0px` (Relative to y)
*   **Result**: 文字の上端が `y` (margin_top) と完全に一致し、決してはみ出しません。

---

## 3. Implementation Steps
1.  **Refactor `_draw_vertical_text_content`**:
    *   `step = fm.ascent() + fm.descent()` をループの最初で定義（または `fm` から都度計算）。
    *   `cy` の計算式を `float(y) + float(step) / 2.0` に変更。

2.  **Verification**:
    *   `test_spacing_split.py` の `test_vertical_spacing_metrics` を再確認（ロジック変更の影響がないか）。
    *   `verify_all.bat` でリグレッションがないか確認。

この修正により、一文字目から完璧に表示されるようになります。

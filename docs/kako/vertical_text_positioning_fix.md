# 縦書き位置ズレ修正と完全な座標系確立 (Vertical Positioning Alignment)

## 現象 (Observation)

縦書きモードにおいて、影のオフセット（例: X=1.00）を設定すると、影はウィンドウ内に留まるが、**メインテキストが逆に移動してウィンドウ枠外にはみ出してしまう**。

## 原因 (Root Cause: Double Compensation)

前回の「影の見切れ防止（キャンバス拡張）」と、以前から存在していた「座標補正ロジック」が衝突しています。

1.  **キャンバス拡張 (Current Fix)**:
    影のオフセット分（`pad_right`など）を `margin` に加算し、キャンバスサイズと描画開始位置（マージン）を自動的に調整している。
    *   例: 影が右に100px伸びる → キャンバスが100px広がる → 右マージンも100px増える → テキストは左に寄る（これで影のスペース確保完了）。

2.  **従来の補正 (Legacy Logic)**:
    `_draw_vertical_text_content` 内で、描画開始位置 `curr_x` を計算する際に **`shadow_x` を明示的に減算** している。
    ```python
    # text_renderer.py L1077-ish
    curr_x = canvas_size.width() - ... - right_margin - shadow_x - ...
    ```

**結果**:
「マージン増加による左シフト」＋「`shadow_x` 減算による左シフト」＝ **2重の左シフト** が発生。
本来のテキスト位置よりも過剰に左に移動してしまい、画面外へ消えてしまいます（逆に影は右にズレた位置＝本来のテキスト位置に来るため、影だけが残って見えます）。

## 修正案 (Solution)

**`curr_x` の計算式から `shadow_x` を削除します。**

位置合わせは `pad_left / pad_right` によるマージン調整（`right_margin`）だけですべて解決します。
`shadow_x` は「影を描画する際のオフセット（`custom_offset`）」としてのみ使用すべきであり、メインテキストの配置基準（ベースライン）に影響させてはいけません。

```python
# Before
curr_x = canvas_size.width() - cw - margin - right_margin - shadow_x - outline_width

# After
curr_x = canvas_size.width() - cw - margin - right_margin - outline_width
```

## 検証 (Verification)

*   **Vertical (+X Offset)**: テキストは中央寄り、影が右（拡張エリア）に描画される。
*   **Vertical (-X Offset)**: テキストは中央寄り、影が左（拡張エリア）に描画される。
*   横書き（Horizontal）は影響を受けない（別のロジック）。

この修正により、縦書き・横書き共に「影オフセットによるキャンバス拡張」が正しく機能し、テキスト本体は常に正しい位置に留まります。

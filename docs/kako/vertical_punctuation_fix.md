# 縦書き句読点・約物の配置適正化プラン (Vertical Punctuation Alignment)

## 現象 (Problem)

縦書きモードにおいて、「、」「。」「ー」「！」等の約物が**文字枠のど真ん中（Dead Center）**に描画され、日本語の組版として不自然に見える。
これは、以前の修正でマジックナンバーを排除するために導入した「バウンディングボックス強制中央揃え」が、約物の本来の配置（右寄り、上寄りなど）を無効化してしまっているためです。

## 解決策: タイポグラフィに基づいた配置ロジック (Typographic Alignment Strategy)

「文字のインク（黒い部分）の中心」を揃えるのではなく、**「文字の枠（Em-box/仮想ボディ）の中心」** を揃えるロジックへ移行します。
さらに、横書き用フォントを縦書きで使用する際に不足する「位置情報」を、文字種ごとのルール（Quadrant Mapping）で補完します。

### 1. 基本ロジック: Em-box Alignment (通常文字)

漢字やひらがななどの通常文字は、インクの中心ではなく、フォントデザイナーが設定した**Em-box（仮想ボディ）**を基準に配置します。

*   **Logic**:
    *   セル（Column）の中心 `(0,0)` に対して、フォントのベースライン位置を計算して配置する。
    *   `dx = -advance / 2` （水平方向：Em-boxの中央を合わせる）
    *   `dy = ascent - (ascent + descent) / 2` （垂直方向：Em-boxの垂直中心を合わせる）
*   **Result**: 小書き文字（っ、ゃ）なども、フォントが定義した正しい位置（右寄りなど）に自然に配置されます。

### 2. 回転文字: Optical Centering (長音・括弧)

「ー」「（」「）」などは90度回転させるため、Em-box基準だとズレて見えることがあります。これらは視覚的な中心（Optical Center）を重視します。

*   **Logic**:
    *   **長音「ー」**: 90度回転 + `boundingRect` 中央揃え（既存ロジック維持）。
    *   **括弧「（」「）」**: 90度回転 + `Em-box` 基準（通常文字と同じ扱い）。これにより「（」が下（縦書きでは右）、「）」が上（縦書きでは左）に寄りすぎるのを防ぎ、行のラインに沿わせます。

### 3. 句読点: Quadrant Mapping (「、」「。」)

横書き用フォントの「、」「。」は左下に配置されていますが、縦書きでは**右上**に配置する必要があります。
これを実現するために、明示的な**象限シフト（Quadrant Shift）**を適用します。

*   **Logic**:
    *   基本的な配置は横書き（左下）のまま計算。
    *   そこから `+X`（右へ）、`-Y`（上へ）のオフセットを加算して、右上象限へ移動させる。
    *   オフセット量: `Map(char) -> (offset_x, offset_y)`
        *   `、` (Comma): 右上へ移動 (例: X+0.6em, Y-0.6em)
        *   `。` (Period): 右上へ移動

## 実装ステップ

### `_get_vertical_char_transform` の刷新

現在の「一律 `boundingRect` 中央揃え」ロジックを分岐させます。

```python
def _get_vertical_char_transform(self, window, char, font):
    em_width = fm.horizontalAdvance(char) # or font_size
    em_height = fm.ascent() + fm.descent() # or font_size
    
    # 1. 回転文字 (Rotated)
    if char in "ー～-=":
        # 90度回転 + インク中心揃え (棒線は真ん中が良い)
        return 90, -bounds_center_x, -bounds_center_y

    if char in "「」『』（）...": 
        # 90度回転 + Em-box揃え (括弧の位置関係を維持)
        # 回転後の補正が必要
        return 90, ...

    # 2. 句読点 (Punctuation)
    if char in "、。":
        # 右上へ強制移動
        # Base: 左下 (Horizontal standard)
        # Shift: Right & Up
        dx = em_width * 0.5  # 右へ
        dy = -em_height * 0.5 # 上へ
        # 微調整係数は定数定義するか、設定可能にする
        return 0, dx, dy

    # 3. 通常文字 (Standard)
    # Em-box Center Alignment
    dx = -em_width / 2
    dy = fm.ascent() - (em_height / 2)
    return 0, dx, dy
```

このアプローチにより、プロポーショナルフォント等の等幅でないフォントでも、フォントデザイナーの意図した配置（スペーシング）が最大限尊重されます。

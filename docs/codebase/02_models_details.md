# FTIV Codebase Documentation: `models` Package (詳細版)

このドキュメントは `models` パッケージ内の各ファイル、クラス、Enum、および設定モデルの詳細仕様を解説するものです。
本アプリケーションのデータ構造の中核を担う部分であり、ファイル保存形式（JSON）のスキーマとしての役割も果たします。

---

## 1. `models/enums.py`

### 概要
アプリケーション内で使用される定数セット（列挙型）を定義しています。

### 依存関係
*   標準ライブラリ: `enum.Enum`

### クラス定義

#### `AnchorPosition` (str, Enum)
接続線 (`ConnectorLine`) がウィンドウのどの辺に接続するかを指定します。
*   `AUTO`: "auto" - 自動判定（最短距離などに基づいて動的に決定）。
*   `TOP`: "top" - 上辺。
*   `BOTTOM`: "bottom" - 下辺。
*   `LEFT`: "left" - 左辺。
*   `RIGHT`: "right" - 右辺。

#### `OffsetMode` (str, Enum)
縦書きテキスト表示時の文字配置アルゴリズムを指定します。
*   `MONO`: "A" - 等幅フォント向けモード。グリッド状に配置されます。
*   `PROP`: "B" - プロポーショナルフォント向けモード。文字の高さに応じて詰めて配置されます。

#### `ArrowStyle` (str, Enum)
接続線の端点に矢印を描画するかどうかを指定します。
*   `NONE`: "none" - 矢印なし。
*   `START`: "start" - 始点のみ矢印。
*   `END`: "end" - 終点のみ矢印。
*   `BOTH`: "both" - 両端に矢印。

---

## 2. `models/window_config.py`

### 概要
各ウィンドウの状態を保存・復元するためのデータモデルを定義しています。
ライブラリ **Pydantic** (`BaseModel`) を使用しており、型安全性と自動バリデーション、JSONシリアライズ/デシリアライズを提供します。

### 依存関係
*   ライブラリ: `pydantic`
*   プロジェクト内: `.enums`

---

### クラス: `WindowConfigBase`
全種類のウィンドウ設定の基底クラスです。共通のプロパティ（座標、アニメーション設定など）を持ちます。

#### バリデーション設定 (`model_config`)
*   `validate_assignment=True`: 属性への代入時にも型チェックを行います。
*   `use_enum_values=True`: Enum型を代入した際、自動的にその値（文字列）として保存します（JSON化のため）。

#### 基本プロパティ
| プロパティ名 | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `uuid` | `str` | `""` | ウィンドウ固有の識別子 (UUID v4)。 |
| `parent_uuid` | `Optional[str]` | `None` | 親ウィンドウのUUID。グループ化時に使用。 |
| `position` | `Dict[str, int]` | `{"x":0, "y":0}` | ウィンドウの左上絶対座標。 |
| `is_frontmost` | `bool` | `True` | 現在は未使用の可能性あり（アプリ共通設定に移行？）。 |
| `is_hidden` | `bool` | `False` | 表示/非表示状態 (Hキー)。 |
| `is_click_through` | `bool` | `False` | クリック透過状態。 |
| `is_locked` | `bool` | `False` | **ロック機能**。Trueの場合、マウスドラッグによる移動やリサイズが無効化されます。 |

#### アニメーション設定
| プロパティ名 | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `move_loop_enabled` | `bool` | `False` | 移動アニメーションの有効化ループ再生。 |
| `move_position_only_enabled` | `bool` | `False` | (詳細不明: 現状UIに見当たらず。絶対移動モードに関係？) |
| `move_speed` | `int` | `1000` | 移動アニメーションの1周期の時間 (ms)。 |
| `move_pause_time` | `int` | `0` | ループ間の停止時間 (ms)。 |
| `start_position` | `Optional[Dict]` | `None` | 絶対移動アニメーションの始点座標 `{'x': int, 'y': int}`。 |
| `end_position` | `Optional[Dict]` | `None` | 絶対移動アニメーションの終点座標。 |
| `move_use_relative` | `bool` | `False` | **相対移動モード**。Trueの場合、`move_offset` を使用して現在位置を基準に動く。 |
| `move_offset` | `Dict` | `{"x":0, "y":0}` | 相対移動の移動量。 |
| `move_easing` | `str` | `"Linear"` | 移動アニメーションのイージング関数名 (例: "OutQuad")。 |
| `fade_easing` | `str` | `"Linear"` | フェードアニメーションのイージング関数名。 |
| `is_fading_enabled` | `bool` | `False` | 点滅（フェード）アニメーションの有効化。 |
| `fade_speed` | `int` | `1000` | フェード周期 (ms)。 |
| `fade_pause_time` | `int` | `0` | フェード間の停止時間 (ms)。 |

---

### クラス: `TextWindowConfig` (継承: `WindowConfigBase`)
テキストウィンドウ専用の設定モデルです。非常に多くの装飾プロパティを持ちます。

#### テキスト基本
| プロパティ名 | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `text` | `str` | `"New Text"` | 表示文字列。 |
| `font` | `str` | `"Arial"` | フォントファミリー名。 |
| `font_size` | `int` | `48` | フォントサイズ (pt)。 |
| `text_visible` | `bool` | `True` | 文字自体の表示ON/OFF。 |
| `is_vertical` | `bool` | `False` | **縦書きモード**。 |

#### 装飾（色・不透明度）
*   各要素（文字、背景、影、縁取り1〜3）ごとに `*_color` (Hex形式文字列), `*_opacity` (0-100), `*_visible` などを持ちます。
*   `text_gradient`, `background_gradient`: グラデーション設定。`[(位置float, 色コードstr), ...]` のリスト形式で定義されます。

#### 縁取り (Outline)
最大3重の縁取りに対応しています。
*   `outline_*` (1層目)
*   `second_outline_*` (2層目)
*   `third_outline_*` (3層目)
*   `background_outline_*` (背景矩形の枠線)

#### レイアウト・マージン
| プロパティ名 | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `horizontal_margin_ratio` | `float` | `0.0` | (要確認) 旧マージン仕様の名残？現在は `margin_left` 等を使用。 |
| `vertical_margin_ratio` | `float` | `0.2` | 縦方向のデフォルト余白率。 |
| `margin_top/bottom/left/right` | `float` | - | 各方向のマージン（フォントサイズに対する比率）。 |
| `background_corner_ratio` | `float` | `0.2` | 背景角丸の半径比率。 |

---

### クラス: `ImageWindowConfig` (継承: `WindowConfigBase`)
画像ウィンドウ専用の設定モデルです。

#### プロパティ詳細
| プロパティ名 | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `image_path` | `str` | `""` | 画像ファイルの絶対パス。 |
| `geometry` | `Dict` | `x,y,w,h` | ウィンドウの位置とサイズ。 |
| `scale_factor` | `float` | `1.0` | 拡大縮小率。 |
| `opacity` | `float` | `1.0` | 不透明度 (0.0 - 1.0)。`TextWindow` と異なり 0-100 ではなく 0.0-1.0 である点に注意。 |
| `rotation_angle` | `float` | `0.0` | 回転角度 (度)。 |
| `flip_horizontal` | `bool` | `False` | 左右反転。 |
| `flip_vertical` | `bool` | `False` | 上下反転。 |
| `animation_speed_factor` | `float` | `1.0` | GIF/APNGアニメーションの再生速度倍率。 |

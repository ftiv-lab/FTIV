# FTIV Codebase Documentation: `windows` Package (詳細版)

このドキュメントは、アプリケーションの可視コンポーネント（オーバーレイウィンドウ）の実装を詳述します。
すべてのオーバーレイは `BaseOverlayWindow` を継承し、共通の移動、アニメーション、Undo/Redo機能を提供します。

---

## 1. `windows/base_window.py`

### クラス: `BaseOverlayWindow(QLabel)`
すべてのオーバーレイウィンドウ（テキスト、画像、コネクタラベル）の基底クラスです。
`QLabel` を継承していますが、テキスト表示だけでなく、透明ウィンドウとしての振る舞いやイベントハンドリングの基盤を提供します。

#### コア機能
*   **Undo/Redo 統合**: `set_undoable_property` メソッドを通じて、プロパティ変更を `MoveWindowCommand` や `PropertyChangeCommand` として UndoStack に積みます。
*   **ドラッグ移動**: `mousePressEvent`, `mouseMoveEvent` でウィンドウ移動を処理。
    *   `move_tree_by_delta()`: 親子関係 (親子付け機能) に基づき、子ウィンドウも連動して移動させます。
*   **アニメーション**:
    *   **移動**: `move_loop` (往復), `move_position_only` (片道), 相対移動/絶対移動に対応。
    *   **フェード**: `is_fading` (点滅), フェードイン/アウト。
    *   **イージング**: `QEasingCurve` を使用し、設定ファイルへの保存/復元 (`_apply_easing_from_config`) に対応。
*   **親子関係**: `child_windows` リストと `parent_window_uuid` で管理。
    *   `propagate_scale_to_children()`, `propagate_rotation_to_children()` などで変形を伝播。

#### 重要なメソッド
*   **`set_undoable_property(name, value, update_method)`**: プロパティ変更をUndo可能にするラッパー。
*   **`clear_all_relations()`**: 削除時に親子関係やコネクタを切断する安全策。
*   **`closeEvent()`**: 終了処理。`WindowManager` に `sig_window_closed` を通知して管理リストから削除させます。**`deleteLater()` は呼ばず、WindowManagerに委譲する設計** になっています。

---

## 2. `windows/text_window.py`

### クラス: `TextWindow(BaseOverlayWindow)`
テキストを表示するメインウィンドウです。描画処理は `TextRenderer` に委譲しています。

#### 主な役割
*   **テキスト管理**: 内容、フォント、色、不透明度。
*   **装飾プロパティ**:
    *   **縁取り**: 3重縁取り (`outline`, `second_outline`, `third_outline`)。
    *   **影**: `ShadowOffsetDialog` で調整可能なドロップシャドウ。
    *   **背景**: 角丸、枠線 (`background_outline`)、グラデーション。
*   **TextRenderer 連携**:
    *   頻繁な更新（ホイール操作など）による負荷を防ぐため、`update_text()` ではなく `update_text_debounced()` を用いて描画リクエストを間引き（デバウンス）します。
*   **インライン編集**: ダブルクリックで `TextInputDialog` を開き、リアルタイムプレビューしながら編集可能。

---

## 3. `windows/text_renderer.py`

### クラス: `TextRenderer`
`TextWindow` および `ConnectorLabel` の描画ロジックを一手に引き受けるヘルパークラス。
ステートレスに近い設計ですが、パフォーマンス向上のためにキャッシュを持ちます。

#### 特徴と最適化
*   **Glyph Cache (`_glyph_cache`)**: `QPainterPath` の生成コストが高いため、`(font_family, size, char)` をキーにパスをキャッシュ（LRU）します。
*   **Blur Cache (`_blur_cache`)**: ぼかし処理（影、縁取り）の結果をキャッシュ。
*   **Render Cache**: 最終的な `QPixmap` をキャッシュ（条件により）。
*   **Profiling**: `set_profiling(True)` で描画工程ごとの所要時間を計測可能。

#### 描画フロー
1.  **プロファイル開始**: (有効時)
2.  **サイズ計算**: フォントメトリクスからキャンバスサイズを決定。
3.  **背景描画**: `_draw_background`
4.  **テキスト要素描画**:
    *   **影**: ぼかし処理付きで描画。
    *   **縁取り**: 3層分を奥から順に描画 (`QPainterPath.translated` を使用)。
    *   **メインテキスト**: グラデーション (`fillPath`) または単色 (`drawText`)。
    *   **縦書き対応**: `_render_vertical` メソッドで文字ごとに回転・配置補正を行う。

---

## 4. `windows/image_window.py`

### クラス: `ImageWindow(BaseOverlayWindow)`
画像を表示するためのウィンドウ。静止画だけでなくアニメーションGIF/APNGにも対応。

#### 機能
*   **高度な変形**: 拡大縮小 (`scale_factor`)、回転 (`rotation_angle`)、反転 (`flip_h/v`)。`QTransform` を用いて描画時に適用されます。
*   **アニメーション再生**: `QTimer` を使い、`PIL` で読み込んだフレーム (`self.frames`) を順次切り替え。速度調整 (`animation_speed_factor`) も可能。
*   **ディスプレイ適合**: `fit_to_display`, `center_on_display` 等で画面に合わせて自動リサイズ・配置。

---

## 5. `windows/connector.py`

ウィンドウ間を結ぶ線 (`ConnectorLine`) と、その上に乗るラベル (`ConnectorLabel`) を定義します。

### クラス: `ConnectorLine(QWidget)`
*   **役割**: 2つのウィンドウ (`start_window`, `end_window`) の中心を結ぶ線を描画。
*   **ベジェ曲線**: 単純な直線ではなく、アンカー位置 (`AnchorPosition`) を考慮した `path.cubicTo` による滑らかな曲線を描画。
*   **装飾**:
    *   線種（実線、破線、点線）。
    *   矢印（始点、終点、両方）。
    *   ラベル表示制御 (`ConnectorLabel` の表示/非表示)。
*   **イベント**:
    *   自分自身は `QWidget` だが、クリック判定は `QPainterPathStroker` で太らせた領域 (`setMask`) で行うことで、細い線でも選択しやすくしている。

### クラス: `ConnectorLabel(BaseOverlayWindow)`
*   **役割**: 接続線の中央に追従するテキストラベル。
*   **実装**: `TextWindow` とほぼ同等の機能を持ちつつ、移動は自分で行わず `ConnectorLine.update_position()` によって制御される。
*   **UI**: 右クリックメニューから、親である線のスタイル変更や削除も行えるように連携している。

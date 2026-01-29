# FTIV マインドマップモード実装履歴 (MindMap Implementation Log)

デスクトップ付箋アプリ (FTIV) にマインドマップ機能を追加するプロジェクトの実装履歴です。
**期間**: 2026-01-19 〜 2026-01-23

---

## Phase 1: MindMap Mode Foundation (基盤構築)
- **AppMode**: アプリケーションモード (`Desktop`, `MindMap`) を管理する列挙型と `AppModeManager` を実装。
- **WindowLayer**: ウィンドウの重なり順を管理する `WindowLayer` 列挙型を導入。
- **パッケージ構造**: `ui/mindmap` パッケージを作成し、今後の拡張の基盤を整備。

## Phase 2: Canvas Implementation (キャンバス)
- **MindMapCanvas**: 無限キャンバス (`QGraphicsView` + `QGraphicsScene`) を実装。
  - **動的拡張**: ノードが端に近づくとキャンバスサイズを自動拡張 (3000px 〜 10000px)。
  - **操作**: マウスホイールでのズーム、ドラッグでのパン、中央表示機能。
  - **全画面**: `F11` またはツールバーから全画面モードへの切り替えに対応。
- **GridBackground**: グリッド表示機能を実装 (Phase 18 でトグル機能追加)。

## Phase 3: Node Implementation (ノード)
- **MindMapNode**: マインドマップの要素となるノード (`QGraphicsItem`) を実装。
  - **インタラクション**: ドラッグ移動、選択状態、ダブルクリックによるテキスト編集。
  - **スタイル**: フォント、色、影、角丸などのスタイリングに対応。

## Phase 4: Edge Implementation (エッジ)
- **MindMapEdge**: ノード間を結ぶエッジ (`QGraphicsPathItem`) を実装。
  - **ベジェ曲線**: ノード位置に追従して滑らかな曲線を描画。
  - **自動追従**: ノード移動時にリアルタイムで再描画。

## Phase 5: UI Integration (統合)
- **MindMapWidget**: キャンバスとツールバーを統合するコンテナウィジェットを作成。
- **MindMapTab**: メインウィンドウにタブとしてマインドマップ機能を追加。
- **ContextMenu**: キャンバスおよびノードの右クリックメニューを実装。

## Phase 6: Persistence (保存・読み込み)
- **FileManager拡張**: `mindmaps.json` を用いたマインドマップデータの保存・読み込みに対応。
- **データ構造**: カテゴリごとに複数のマップを管理可能な構造を採用。

---

## Phase 7-8: TextRenderer Integration (テキスト描画強化)
- **TextRenderer統合**: 既存の高機能テキスト描画エンジン (`TextRenderer`) をマインドマップノードに統合。
- **Direct Paint**: `paint_direct()` メソッドを追加し、ビットマップ化せずにベクター品質で直接テキストを描画可能に。
- **縦書き対応**: 日本語の縦書き表示をサポート。

## Phase 9: UX Clean-up (高機能モード統一)
- **モード統一**: シンプルモードを廃止し、高機能モード (TextRenderer) をデフォルトとして統一。
- **コード削減**: 不要な切り替えメニューやレガシーコードを削除。

## Phase 10-12: Property Panel Integration (プロパティパネル統合)
- **UI連携**: 既存の `PropertyPanel` を拡張し、マインドマップノードのプロパティ（フォント、色、透明度など）を編集可能に。
- **双方向同期**: ノード選択時のUI更新と、UI操作時のノード更新をリアルタイムに同期。
- **Gradient Editor**: グラデーション編集ダイアログを統合し、テキストおよびノード背景のグラデーションに対応。

## Phase 13-14: Polish & Stability (品質向上)
- **Zoom Fix**: ズームスライダーとマウスホイールの競合を解消し、同期ロジックを修正。
- **Gradient Sync**: グラデーション設定のUI同期ロジックを完成。

## Phase 15: Decoration Improvement (装飾改善)
- **Stroke & Shadow**: 縁取りと影の描画ロジックを改善し、ぼかしなし (`blur=0`) の場合の描画品質を向上。

## Phase 16: Default Style Settings (デフォルトスタイル)
- **DefaultNodeStyle**: 新規ノード作成時のデフォルトスタイルを管理するモデルとダイアログを実装。
- **Context Menu**: 既存ノードのスタイルを「デフォルトに設定」する機能を追加。

## Phase 17: Environment & Rules (開発環境)
- **Verificaton Scripts**: `verify_all.bat` (Python 3.14開発用) と `verify_build_ready.bat` (Python 3.13ビルド用) を整備。
- **Safety First**: リファクタリング時の安全第一原則（既存コードを壊さない、フォールバック維持）をルール化 (`Antigravity Rules v2.2`)。

## Phase 18: UX Improvement (UX改善)
- **Grid Toggle**: ツールバーにグリッド表示切り替えボタンを追加。
- **Zoom Range**: マウスホイールによるズームが上限 (300%) までスムーズに到達するようロジックを修正。
- **Refactoring**: `MindMapNode` の完全疎結合化（親ウィジェットへの直接参照排除）を完了。

# リファクタリング計画: MainWindowの分割 (God Object 解体)

## 目標
`ui/main_window.py` (現在約4200行) の複雑さとサイズを削減し、UI構築、イベント処理、ロジックを独立した凝集度の高いコンポーネントに分割する。"God Object" アンチパターンを解消する。

## 現状の課題
1.  **密結合**: `ui/tabs/*.py` の関数が `MainWindow` インスタンスの属性 (例: `mw.btn_lang_en`) を直接書き換えている。
2.  **名前空間の汚染**: `MainWindow` が各タブに属する数百のウィジェットの参照をフラットに保持している。
3.  **関心の混在**: UI構築、ビジネスロジック、イベント処理、ウィンドウ管理がすべて混在している。

## Phase 1: タブのカプセル化 (UI分離)
**目的**: `ui/tabs/*.py` の関数ベースのビルダーを、独立した `QWidget` サブクラスに変換する。
**戦略**:
1.  各タブごとにクラスを作成する (例: `GeneralTab(QWidget)`, `TextTab(QWidget)`).
2.  UI構築ロジックを `build_xxx_tab` から `__init__` または `setup_ui` メソッドに移動する。
3.  **依存性の注入**: 機能維持のため、初期段階では `MainWindow` (または特定のコントローラー) を `__init__` に渡すが、可能な限り属性操作ではなくシグナル/スロットの使用を目指す。
4.  **名前空間の整理**: `mw.some_button` への代入をクラス内の `self.some_button` に変更する。

### 対象ファイルと詳細戦略

#### 1. `ui/tabs/general_tab.py` -> `class GeneralTab(QWidget)` [完了]
- 言語切り替え、最前面トグルなどの基本設定を担当。

#### 2. `ui/tabs/text_tab.py` -> `class TextTab(QWidget)`
- **主な機能**: テキストウィンドウ生成、フォント設定、整列。
- **依存関係**: `mw.font_manager`, `mw.text_windows`, `mw.add_text_window`。
- **実装詳細**:
    - `_txt_on_selection_changed(self, window)` を `TextTab` クラスのメソッド `on_selection_changed(self, window)` に移行する。
    - `MainWindow` 側には互換性維持のため `self._txt_on_selection_changed = self.text_tab.on_selection_changed` のようにエイリアスを貼るか、委譲メソッドを残す。
    - `txt_btn_` などの属性も `GeneralTab` と同様に `mw` に注入して既存コードを壊さないようにする。
- **戦略**: 
    - `mw` 経由で `WindowManager` や `FontManager` にアクセスする。

#### 3. `ui/tabs/image_tab.py` -> `class ImageTab(QWidget)`
- **主な機能**: 画像ウィンドウ生成、監視フォルダ設定、変形（サイズ/透明度/回転/反転）、整列。
- **依存関係**: `mw.file_manager`, `mw.image_windows`, `mw.add_image_window`。
- **実装詳細**:
    - `_img_on_selection_changed(self, window)` -> `ImageTab.on_selection_changed(self, window)` へ移動。
    - `_img_transform_sel_tab_index` (タブ選択状態の保持) も `ImageTab` 内で管理する。
    - `img_btn_` プレフィックスが付く大量のボタン属性を `mw` に注入して互換性を維持する。
    - ドラッグ＆ドロップ受け入れ（`setAcceptDrops(True)`）が `MainWindow` 自体でも行われているか確認し、必要なら `ImageTab` 内でも処理できるようにする（現状は `mw` 全体で受けている可能性が高いので、そのままで良いか確認）。
- **戦略**: `TextTab` と同様の手順で移行。
    - 生成関連: `mw.add_image`
    - 変形関連: `mw._img_run_selected_transform_action`, `mw.set_all_image_size_percentage` 等のロジックは今回 `MainWindow` に残る (Logic分離は別フェーズ)。まずはUIと状態更新の責務を移動する。

#### 4. `ui/tabs/scene_tab.py` -> `class SceneTab(QWidget)`
- **主な機能**: シーン管理（カテゴリ・シーン一覧、追加/保存/読込）。
- **依存関係**: `mw.scene_category_tabs`, `mw.add_new_category` 等。
- **実装詳細**:
    - `build_scene_tab` の内容を `SceneTab` クラスに移行。
    - 同ファイルに含まれる `build_connections_subtab` は、ファイル名は `connections_tab.py` ではなく `scene_tab.py` にあるが、タブ名としては "Scene" ではなく "Connections" タブとして個別に登録されている可能性がある（`MainWindow.create_connections_tab` がこれを呼んでいる）。
    - 調査の結果、`build_connections_subtab` は `create_connections_tab` から呼ばれているため、これは **SceneTab とは別の `ConnectionsTab` クラス** として分割すべき。
    - よって、`ui/tabs/scene_tab.py` から `ConnectionsTab` クラスも同時に抽出・定義する。
    - `mw.scene_group` や `btn_add_category` などの属性注入を行い、互換性を維持。
- **戦略**: `SceneTab` と `ConnectionsTab` の2クラスを定義し、それぞれ `MainWindow` に統合する。
#### 5. `ui/tabs/animation_tab.py` -> `class AnimationTab(QWidget)`
- **主な機能**: アニメーションプリセットの適用。
- **依存関係**: `mw.last_selected_window` (選択中のウィンドウに対して操作)。
- **実装詳細**:
    - `build_animation_tab` をクラス化し、UI構築を `__init__` に移動。
    - `mw.anim_target_combo` などの属性注入を行い互換性を維持。
    - `mw._anim_on_selection_changed` を `AnimationTab.on_selection_changed` に移行。
    - `mw._anim_refresh_enabled_state` もクラス内に移動。
- **戦略**: 既存のアニメーション適用メソッド（`mw._anim_apply_offset` 等）は、Logic分離フェーズまでは `MainWindow` に残し、ボタンの `connect` で `self.mw._anim_apply_offset` を呼ぶ形にする。UIの状態管理責務を重点的に移行する。
#### 6. `ui/tabs/about_tab.py` -> `class AboutTab(QWidget)`
- **主な機能**: バージョン情報表示、リンク、設定（パフォーマンスなど）。
- **依存関係**: ほぼなし。静的な情報表示が主だが、パフォーマンス設定など一部設定値へのアクセスあり。
- **実装詳細**:
    - `build_about_tab` をクラス化 (`__init__` へ)。
    - `mw.edition_group`, `mw.label_current_edition` などの属性注入を行い互換性を維持。
    - `mw._refresh_about_tab_text` を `AboutTab.refresh_ui` に移行。
    - パフォーマンス設定ボタンのコールバック (`_apply_perf`) もクラス内メソッドとしてカプセル化し、`mw.apply_performance_settings` を呼ぶ形にする。
- **戦略**: UI構築と表示更新のロジックを `AboutTab` に集約する。設定適用などのビジネスロジックは、当面 `MainWindow` のメソッドを呼び出す形で維持し、Logic分離フェーズで改めて検討する。

## Phase 2: メニュー構築の分離 (MenuManager)
**目的**: `MainWindow` 内のコンテキストメニュー構築ロジック (`show_context_menu`) を分離する。メインメニューバーは存在しないため、コンテキストメニューが対象。

#### 1. `managers/menu_manager.py` の作成
- `class MenuManager`:
    - `__init__(self, main_window: Any)`: MainWindowへの参照を保持。
    - `show_context_menu(self, pos: QPoint)`: `MainWindow.show_context_menu` のロジックを移動。
    - 各種 `QAction` のシグナル接続は `self.mw.some_method` への委譲となる。

#### 2. `MainWindow` の修正
- `MenuManager` のインスタンス化。
- `show_context_menu` を `self.menu_manager.show_context_menu(pos)` に置き換え。
- ※ `create_all_rotation_action_handler` などのヘルパー関数も移動を検討するが、クロージャとして実装されている場合は `MenuManager` 内で定義しなおす。委譲する。

## Phase 3: イベント処理の分離 (Mixins)
**目的**: 複雑なイベント処理（ドラッグ＆ドロップ、ショートカット、マウス操作）を分離する。
**戦略**: 多重継承を用いた Mixin パターンを採用し、`MainWindow` 本体を軽量化する。

#### 1. `mixins/dnd_mixin.py` (Drag & Drop)
- `class DnDMixin`:
    - `dragEnterEvent`, `dropEvent` をここに移動。
    - `mw.add_image_from_path` などの呼び出しは `self` (MainWindowと仮定) 経由で行う。

#### 2. `mixins/shortcut_mixin.py` (Shortcuts)
- `class ShortcutMixin`:
    - `_register_emergency_shortcuts`, `emergency_disable_all_click_through` などの緊急ショートカット関連メソッドを移動。
    - `create_undo_redo_actions` もここに含めるか検討。

#### 3. `MainWindow` の修正
- `class MainWindow(QWidget, DnDMixin, ShortcutMixin):` のように継承順序を変更。
- `__init__` で各Mixinの初期化（必要であれば）を行う。
- ※ `mousePressEvent` などのウィンドウ移動ロジックは、短いので `MainWindow` に残すか、`WindowMovabilityMixin` として更に分けるか検討（今回は保留またはDnDに統合）。

## 検証計画
1.  **目視確認 (Manual Testing)**:
    - アプリ起動後、全タブが正しく表示されること。
    - 各ボタン（言語切り替え、前面固定など）が従来通り機能すること。
2.  **Lintチェック**:
    - `mainwindow.some_attribute` へのアクセス違反（AttributeError）がないこと。
3.  **ロジック不変**:
    - これは構造的な変更であり、ビジネスロジックの変更は行わない。

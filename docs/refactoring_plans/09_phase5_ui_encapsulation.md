# Phase 5: UI Logic Encapsulation (UIロジックの隠蔽・カプセル化)

## 概要
現在、`GeneralTab`, `TextTab` 等のタブクラスは物理的にファイル分割されていますが、`_inject_compatibility_attributes` メソッドを通じて内部のウィジェット（ボタン等）を `MainWindow` に注入しています。
これにより、`MainWindow` が依然として他クラスのUIを直接操作する（`refresh_ui_text` 等で）「密結合」な状態が続いています。
Phase 5 では、これらの「互換性注入」を廃止し、各タブが自身のUI更新や状態管理を完結させる「真のカプセル化」を実現します。

## 現状の課題
- **密結合**: `MainWindow` が `self.btn_add_text_main` など、本来 `TextTab` の内部にあるべきボタンを直接触っている。
- **神クラスの残滓**: UIの構築コードは移動したが、UIの**制御コード**（翻訳更新など）が `MainWindow` に残っている。

## 実施計画

### 1. `MainWindow.refresh_ui_text` のリファクタリング
現在 `MainWindow` で行っている各ウィジェットの `setText` 処理を、各タブクラスの `refresh_ui()` メソッド呼び出しに完全に委譲します。

- [ ] **GeneralTab**: `MainWindow._refresh_general_tab_text` を削除し、`self.general_tab.refresh_ui()` のみに一本化。
- [ ] **TextTab**: `MainWindow._refresh_text_tab_text` を削除し、`self.text_tab.refresh_ui()` のみに一本化。
- [ ] **ImageTab**: `MainWindow._refresh_image_tab_text` を削除。
- [ ] **AnimationTab**: `_refresh_subtab_titles` などのロジックをタブ内に移動。

### 2. 互換性注入 (`_inject_compatibility_attributes`) の廃止
`MainWindow` がウィジェットを直接参照している箇所（主に状態同期）を洗い出し、タブ側のメソッド経由に変更した後、注入メソッドを削除します。

#### 例
**現在**:
```python
# MainWindow
self.btn_toggle_prop.setChecked(True)  # GeneralTabのボタンを直接操作
```

**修正後**:
```python
# MainWindow
self.general_tab.update_prop_button_state(True) # メソッド経由
```

### 3. 対象ファイル
- `ui/main_window.py`
- `ui/tabs/general_tab.py`
- `ui/tabs/text_tab.py`
- `ui/tabs/image_tab.py`
- `ui/tabs/animation_tab.py`
- `ui/tabs/scene_tab.py`

## ゴール
- `MainWindow` から `self.btn_*` のようなウィジェット参照を全排除する。
- `MainWindow.refresh_ui_text` を、各マネージャー/タブへの委譲メソッド呼び出しだけの 20行程度 のメソッドにする。

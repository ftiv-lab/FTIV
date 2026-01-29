# Phase 4: 残存ロジックのクリーンアップ計画

## 目的
`MainWindow` に残存している高密度のUIロジック（特にコネクタ関連）や、不要なプロキシメソッドを整理し、「God Object」からの完全脱却を目指す。

## 現状の課題
1.  **コネクタロジックの逆流**: `ConnectionsTab` はUI作成のみを行い、シグナル接続先として `MainWindow` の非公開メソッド (`_conn_*`) を指定している。これにより、`MainWindow` 側に100行以上のコネクタ制御ロジックが残留している。
2.  **プロキシメソッドの散在**: `change_all_fonts` など、単にManagerを呼ぶだけのメソッドが大量にあり、`MainWindow` の行数を押し上げている。

## 変更案

### 1. `ConnectionsTab` へのロジック移動 (`ui/tabs/scene_tab.py`)
`MainWindow` にある以下のメソッド群を `ConnectionsTab` クラス内に移動する。

- `_conn_on_selection_changed` -> `on_selection_changed`
- `_conn_delete_selected` -> `delete_selected`
- `_conn_change_color_selected` -> `change_color_selected`
- `_conn_open_width_dialog_selected` -> `open_width_dialog_selected`
- `_conn_open_opacity_dialog_selected` -> `open_opacity_dialog_selected`
- `_conn_label_action_selected` -> `label_action_selected`
- `_conn_set_arrow_style_selected` -> `set_arrow_style_selected`

**修正方針**:
- `ConnectionsTab` 内での `self.mw._conn_...` への参照を `self.method` に書き換える。
- `MainWindow` からは `self.connections_tab.on_selection_changed(window)` を呼ぶように変更する。

### 2. プロキシメソッドの削除 (Option)
`MainWindow` のメニューやショートカット定義で、`self.change_all_fonts` ではなく `self.bulk_manager.change_all_fonts` を直接呼ぶように変更し、`MainWindow` 側のメソッドを削除する。

## 手順
1.  `ui/tabs/scene_tab.py` (`ConnectionsTab`) にロジックを移植する。
2.  `ui/main_window.py` から対応するコードブロックを削除する。
3.  `_inject_compatibility_attributes` は維持（後方互換性のため）するが、実体は `ConnectionsTab` が持つようにする。

## 検証
1.  コネクタ（線/ラベル）を選択した際、プロパティ変更パネル（Connectionsタブ内）が正しく更新されるか。
2.  コネクタの色変更、矢印変更、削除が正しく動作するか。

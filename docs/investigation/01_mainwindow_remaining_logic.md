# 調査報告書: MainWindow 残存ロジック

## 概要
Phase 1-3 のリファクタリングにより、`MainWindow` は多くの責務を Manager や Tab クラスに移譲しました。
しかし、依然として `ui/main_window.py` は 2200行以上の規模を持ち、いくつかの「接着剤」以上のロジックが残留しています。

## 特定された残存ロジック

### 1. `_conn_on_selection_changed` (約120行)
**場所**: `ui/main_window.py` L1638付近
**内容**: コネクタ選択時のステータスラベル更新、矢印ボタンスタイルの同期ロジック。
**問題**:
- `ConnectorLine`, `ConnectorLabel` などのクラスを直接 import し、型チェックを行っている。
- UI更新の詳細（テキスト整形、ボタン状態変更）を直接記述している。
**対策**:
- `ConnectionsTab` クラス、または `ConnectorActions` コントローラーに移動すべき。
- `MainWindow` は `self.connections_tab.on_selection_changed(obj)` を呼ぶだけにする。

### 2. UI更新プロキシメソッド群
**場所**: L450 - L750 付近
**内容**: `_refresh_general_tab_text`, `change_all_fonts`, `show_all_everything` など。
**現状**:
- 多くは `Manager` や `Tab` への単純な委譲（プロキシ）になっている。
- 一部、`update_overlay_button_style` のようなフォールバックロジックが含まれている。
**対策**:
- プロキシメソッドを削除し、シグナル接続やボタンアクションから直接 `Manager` メソッドを呼ぶ形に変更することで、`MainWindow` の行数を数百行削減できる可能性がある。
- ただし、外部インターフェース（`MainWindow.change_all_fonts` を外部から呼ぶケース）がある場合は注意が必要。

### 3. イベントハンドラ
- `on_manager_selection_changed` が各タブへの分配を行っている。これは「メディエーター」としての役割なので許容範囲だが、分配ロジック自体も記述が長くなりがち。

## 結論
次のステップ（Phase 4）として、最も肥大化している `_conn_on_selection_changed` の移動と、不要なプロキシメソッドの削減を推奨します。
これにより `MainWindow` のさらなる軽量化が可能になります。

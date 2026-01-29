# Phase 11: User Interaction & Command Flow Decoupling

## 1. 概要
Phase 11 では、`MainWindow` に残存している大量の「委譲用ラッパーメソッド（Pass-Through Methods）」を削除し、UIコンポーネント（Tabs）がビジネスロジック（Controllers/Actions）に直接アクセスする形にリファクタリングします。
これにより、`MainWindow` は「ただのコンテナ」としての責務に集中し、機能追加時に `MainWindow` を経由する必要がなくなります。

## 2. 背景・課題 (Technical Debt)
現在、`ui/tabs/text_tab.py` 等のタブクラスは、ボタンが押された際に `self.mw.set_all_text_horizontal()` のようなメソッドを呼び出しています。
しかし、`MainWindow` 側の実装は以下のようになっており、単に `LayoutActions` 等へ横流ししているだけです。

```python
# ui/main_window.py (Bad Pattern)
def set_all_text_horizontal(self) -> None:
    self.txt_actions.set_all_text_horizontal()
```

このようなメソッドが数十個存在し、`MainWindow` を肥大化させています。

## 3. 実施内容

### 3.1 `MainController` へのアクセサ追加
Tabs が `LayoutActions` や `ImageActions` にアクセスするための経路を整備します。
`MainWindow` は `MainController` を持っているため、そこを経由してアクションにアクセスするか、Tabs 初期化時にアクションインスタンスを渡す形にします。

*   **方針**: `MainController` が `Actions` へのゲートウェイとなる。
    *   `main_controller.layout_actions`
    *   `main_controller.image_actions`
    *   `main_controller.connector_actions`

### 3.2 `ui/tabs/*.py` の修正
`self.mw.wrapper_method()` を呼んでいる箇所を、`self.mw.main_controller.layout_actions.real_method()` （または適切なアクション呼び出し）に書き換えます。

*   **Target Files**:
    *   `ui/tabs/text_tab.py`
    *   `ui/tabs/image_tab.py`
    *   `ui/tabs/scene_tab.py` (もしあれば)

### 3.3 `ui/main_window.py` の掃除
不要になったラッパーメソッドを一括削除します。推定で100行〜200行の削減が見込まれます。

*   **削除対象 (例)**:
    *   `set_all_text_vertical`
    *   `set_all_text_horizontal`
    *   `_txt_hide_other_text_windows`
    *   etc...

## 4. 検証計画

### 4.1 静的解析 & ユニットテスト
*   **pytest**: `tests/` 以下のテストが引き続きパスすることを確認（ロジック自体は変わらないため）。
*   **Syntax Check**: メソッド削除による `AttributeError` が発生しないか、`findstr` 等で呼び出し元を完全網羅して確認。

### 4.2 手動確認
*   **Text Tab**: 配置変更（水平/垂直）、表示切り替え（Show/Hide）が機能するか。
*   **Image Tab**: 一括操作（透明度、サイズ）が機能するか。
*   **Refactoring Safety**: 「機能は何も変わっていない」ことが合格条件。

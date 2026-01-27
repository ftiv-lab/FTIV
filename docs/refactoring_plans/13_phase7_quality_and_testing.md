# Phase 7 Implementation Plan: Quality & Testing

これまでのリファクタリングでビジネスロジックの分離が進みました。
Phase 7 では、これらの成果物の品質を「型安全性」と「自動テスト」の両面から保証し、将来の変更に強いコードベースを構築します。

## 1. Strict Type Safety (型安全性の強化)

現状 `Any` が多用されている箇所を、具体的な型ヒントに置き換えます。

### 対象ファイル
- `ui/controllers/layout_actions.py`
- `ui/controllers/connector_actions.py`
- `ui/controllers/image_actions.py`
- `ui/tabs/*.py` (可能な範囲で)

### 実施方針
1. **循環参照の回避**:
   `from typing import TYPE_CHECKING` ブロックを使用し、実行時の循環インポートを回避しつつ、型チェッカーには正しい情報を伝えます。

   ```python
   if TYPE_CHECKING:
       from ui.main_window import MainWindow
       from ui.windows.image_window import ImageWindow
   ```

2. **`Any` の排除**:
   `window: Any` -> `window: ImageWindow | TextWindow` のように、可能な限り具体的な型を指定します。

## 2. Unit Testing (単体テストの導入)

分離されたロジック (`LayoutActions`, `ImageActions` 等) に対して、`pytest` を用いた単体テストを作成します。

### 環境構築
- `tests/` ディレクトリの作成
- `conftest.py` の作成 (必要に応じてQtテスト用のフィクスチャなど)

### テスト対象
1. **`LayoutActions`**:
   - `pack_all_left_top`: 座標計算が正しいか。
   - `align_images_grid`: 指定した列数・間隔で座標が計算されるか。
   - *Note*: 実際のウィンドウ移動 (`move()`) は Mock を用いて検証します。

2. **`ImageActions`**:
   - `set_all_image_opacity`: 全ウィンドウに対して `set_opacity` が呼ばれるか (Mock検証)。

## 3. タスク分割

1. **環境整備**: `tests/` 作成、`mypy` / `pytest` 設定確認。
2. **型定義の強化**: コントローラークラスの型ヒント修正。
3. **テスト実装**: `test_layout_actions.py`, `test_image_actions.py` の作成。
4. **検証**: テスト実行とPass確認。

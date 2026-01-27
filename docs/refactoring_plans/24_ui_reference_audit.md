# UI参照に関する包括的監査報告書

**日付**: 2026-01-18
**監査対象**: `managers/*.py`, `ui/controllers/*.py`
**目的**: `AnimationManager` で発生した「UIコンポーネントが MainWindow 直下にあると誤認して参照エラーになる」不具合と同様のパターンが、他クラスに残存していないか検証する。

## 1. 監査手法
すべての Manager および Controller クラスにおいて、以下のパターンを検索・目視確認しました。
- `self.mw.widget_name` (MainWindow直下のウィジェット直接参照)
- `self.view.widget_name` (同上)

## 2. 監査結果

### 🚨 修正済み (Fixed)
*   **`managers/animation_manager.py`**
    *   **状況**: `self.mw.anim_move_speed` 等、UI部品を直接参照していた。
    *   **対応**: `_get_ui_widget` ヘルパーメソッドを導入し、`AnimationTab` 内を探索するように修正済み。正常動作を確認。

*   **`ui/controllers/connector_actions.py`**
    *   **状況**: `self.mw._conn_refresh_enabled_state` という存在しないメソッド（デッドコード）を呼び出していた。
    *   **対応**: 該当のデッドコードを削除し、`self.mw.connections_tab.on_selection_changed` への依存に一本化。

### ✅ 安全 (Safe)
以下のクラスは、適切なアクセサ（`Tab`オブジェクト経由）を使用しているか、UI部品への直接アクセスを行っていないため、**問題ありません**。

*   **`ui/controllers/text_actions.py`**
    *   UI操作は `self.mw.text_tab` を経由しており適切。
*   **`ui/controllers/image_actions.py`**
    *   UI操作は `self.mw.image_tab` を経由しており適切。
*   **`ui/controllers/scene_actions.py`**
    *   コンボボックス等の操作は `self.mw.scene_tab` を経由しており適切。
*   **`ui/controllers/layout_actions.py`**
    *   Undoスタックやウィンドウリストのみを使用しており、UI部品には触れていない。
*   **`managers/bulk_manager.py`**
    *   `WindowManager` への委譲のみで、UI部品直触りはなし。
*   **`managers/window_manager.py`**
    *   シグナル (`sig_...`) を介した通信が主であり、UI部品への直接依存はない。

## 3. 総評と推奨事項
*   **現状**: `AnimationManager` 以外の主要コンポーネントは、「タブによるUIのカプセル化」ルールにおおむね準拠しています。
*   **推奨**: 今後新しい Manager/Controller を追加する際は、`MainWindow` に直接ウィジェットをぶら下げるのではなく、必ず「Tabクラス」または「Panelクラス」にカプセル化し、そのインスタンス経由でアクセスすることを徹底してください。

以上

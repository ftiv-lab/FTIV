# Phase 8: Comprehensive Quality Assurance (Structure & Tests)

Phase 7 では主要な Controller に対して型安全化とテスト導入を行いましたが、**UI層 (`ui/tabs/*`)** や **Manager層 (`managers/*`)**、および **Connector ロジック** にはまだ「曖昧な型定義 (`Any`)」や「テスト未作成」の領域が残っています。
Phase 8 ではこれらを網羅的にカバーし、プロジェクト全体の品質と保守性を飛躍的に向上させます。

## Goal
プロジェクト全体の「型安全性 (Type Safety)」を確立し、主要なロジックに対する「テストカバレッジ (Test Coverage)」を拡大する。

## User Review Required
> [!NOTE]
> このフェーズは機能追加ではなく、内部品質の向上（リファクタリング）がメインです。見た目の変化はありませんが、バグの未然防止や開発効率向上に直結します。

## Proposed Changes

### 1. Global Strict Type Safety (型定義の完全化)
`Any` の使用を原則禁止とし、全てのクラス・メソッドに厳密な型ヒントを適用します。

#### Target Files
-   **Managers**:
    -   `managers/settings_manager.py`: `load_settings` 等のデータ型を明確化。
    -   `managers/window_manager.py`: 管理するウィンドウリスト (`image_windows` 等) のジェネリクス型定義 (`List[ImageWindow]`)。
-   **UI Tabs**:
    -   `ui/tabs/*.py` (`image_tab.py`, `text_tab.py` 等): `MainWindow` への依存を `TYPE_CHECKING` で解決し、UIイベントハンドラの引数を明確化。

### 2. Expanded Unit Testing (テスト範囲の拡大)
テスト未作成の重要ロジックに対して、単体テストを追加します。

#### Target Components
-   **`ConnectorActions`**:
    -   `delete_selected`, `change_color` 等のロジックテスト（Mock使用）。
-   **`SettingsManager`**:
    -   設定ファイル (`json`) の読み書き、値のバリデーションロジックのテスト。
    -   `init_window_settings` 等の初期化ロジック検証。
-   **`WindowManager`**:
    -   ウィンドウの登録・削除、リスト管理ロジック (`register_window`, `close_all_*`) のテスト。

## Verification Plan

### Automated Tests
-   `pytest tests/` を実行し、既存の5テストに加え、新規作成するテストケース（約10〜15件想定）が全て PASS することを確認する。

### Manual Verification
-   アプリを起動し、リファクタリング（型定義変更）によって実行時エラー（ImportError, AttributeError）が発生していないか、主要機能を一通り触って確認する。

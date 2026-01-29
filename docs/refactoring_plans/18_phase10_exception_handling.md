# Phase 10: Exception Handling & Logging Standardization

Phase 9 では Controller パターン導入により構造が整理されました。次の Phase 10 では、`99_senior_engineer_critique.md` での最重要指摘事項の一つである **「例外の握りつぶし (Pokemon Exception Handling)」の撲滅** と、**ロギングの標準化** を行います。

## Goal
アプリ全体の信頼性を高めるため、`try: ... except: pass` を排除し、適切なエラーログ出力 (`logging`) とユーザー通知 (`QMessageBox`) を実装する。

## User Review Required
> [!NOTE]
> このフェーズにより、ユーザーはエラー発生時に「何が起きたか」を知ることができるようになり、開発者はログファイルを通じてデバッグが容易になります。

## Proposed Changes

### 1. Standardization Rule (標準化ルール)
*   **Catch Specific Exceptions**: `Exception` ではなく `ValueError`, `IOError` 等を捕捉する。
*   **Must Log**: 例外をキャッチしたら必ず `logger.error` または `logger.exception` を呼ぶ。
*   **User Feedback**: ユーザー操作（保存、読み込み等）に直結するエラーは `QMessageBox` で通知する。

### 2. Target Components
*   **`ui/main_window.py`**:
    *   (In Progress) `closeEvent`, UI refresh logic, and `copy_shop_url` logging.
*   **`managers/window_manager.py`** (Critical):
    *   Found ~30 occurrences of `pass`.
    *   Key areas: `remove_window`, `add_connector`, `set_selected_window`.
    *   Action: Replace with `logger.error(..., exc_info=True)` or `logger.debug` for harmless compatibility checks.
*   **`ui/tabs/text_tab.py`**:
    *   Found 3 occurrences (lines 368, 544, 562).
    *   Action: Add logging.
*   **`managers/settings_manager.py`**:
    *   Found 2 occurrences.
    *   Action: Add logging.

### 3. Implementation Steps
1.  **Global Logger Check**: `utils/logger.py` の設定再確認（ログファイル出力先など）。
2.  **Sweep & Fix**: `try` ブロックを検索し、`pass` のみを記述している箇所を特定・修正。
3.  **Refactor**: 共通のエラーハンドリングロジックがあれば `utils/error_handler.py` (仮) に切り出し。

## Verification Plan

### Automated Tests
*   既存の `pytest` が、ログ出力追加後も修正なくパスすることを確認。
*   （可能であれば）`caplog` (pytest fixture) を用いて、エラー時に正しくログが出るかを検証するテストを追加。

### Manual Verification
*   意図的にエラーを起こす（例：読み込み不可ファイルを指定）手順を実施し、ログファイル (`logs/app.log`) にスタックトレースが記録されるか確認。
*   重要なエラーでメッセージボックスが出るか確認。

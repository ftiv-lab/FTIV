---
description: Strict Test-Driven Development (Red-Green-Refactor) workflow.
---

# Workflow: Test-Driven Development (TDD)

> [!CRITICAL]
> **NO CODE WITHOUT TESTS.**
> テストを書く前に実装コードを書くことは、Antigravity Rules 違反である。

## Step 1: Design & Red (Failing Test)

1.  **仕様の決定**: 何を作るか明確にする（入力と期待される出力）。
2.  **テストファイルの作成**: `tests/test_feature_name.py` を作成または追記。
3.  **テストケースの記述**:
    ```python
    def test_calculator_add():
        calc = Calculator()
        assert calc.add(2, 3) == 5
    ```
4.  **実行して失敗を確認**:
    ```bash
    pytest tests/test_feature_name.py
    # => FAILED (ModuleNotFoundError or AttributeError)
    ```

## Step 2: Green (Minimal Implementation)

1.  **最小限の実装**: テストを通すためだけのコードを書く。
    ```python
    class Calculator:
        def add(self, a, b):
            return a + b
    ```
2.  **テスト実行**:
    ```bash
    pytest tests/test_feature_name.py
    # => PASSED
    ```

## Step 3: Refactor (Clean Code)

1.  **リファクタリング**: 重複の排除、命名の改善、構造化。
2.  **再検証**:
    ```bash
    pytest tests/test_feature_name.py
    # => PASSED
    ```

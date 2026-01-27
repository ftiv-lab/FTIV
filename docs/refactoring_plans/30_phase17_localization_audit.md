# Phase 17: Localization Audit & Completion (日英翻訳網羅化)

## 1. 目的 (Objective)
アプリケーション全体の日英翻訳 (`en.json` / `jp.json`) が完全に同期し、かつコード内にハードコードされた文字列が残っていないかを網羅的にチェックし、修正します。

## 2. 現状の課題 (Current Issues)
*   **キーの不一致**: 機能追加に伴い、`en.json` にあって `jp.json` にない（またはその逆）キーが存在する可能性がある。
*   **ハードコード**: 開発中に `setText("Error")` や `QAction("Open")` のように直接英語/日本語を書いてしまい、翻訳システム (`tr()`) を通していない箇所が潜在している。
*   **未使用キー**: 削除された機能のゴミキーが残っている。

## 3. 実装計画 (Implementation Plan)

### 3.1. Audit Tool Creation (`tools/audit_translation.py`)
以下の機能を備えた監査スクリプトを作成します。

1.  **JSON Parity Check (対称性チェック)**
    *   `en.json` と `jp.json` のキーセットを比較。
    *   片方にしか存在しないキーをエラーとして報告。
2.  **Reference Check (参照チェック)**
    *   Python コード全域 (`.py`) から `tr("KEY_NAME")` パターンを抽出。
    *   JSON に定義されていないキーを使用している箇所を検出。
3.  **Hardcoded String Detection (ハードコード検出 - Heuristic)**
    *   UI関連メソッド（`setText`, `setWindowTitle`, `QAction`, `QPushButton` 等）の引数に、`tr()` でラップされていない文字列リテラルが渡されている箇所を警告としてリストアップ。
    *   ※ログ (`logging.info` 等) や辞書キーなどは除外するロジックを入れる。

### 3.2. Execution & Reporting
*   スクリプトを実行し、レポート `translation_issues.md` を生成。
*   ユーザー（およびAI）がこれを確認し、修正方針を決定。

### 3.3. Fix Implementation
*   **Missing Keys**: 不足している翻訳を追加。
*   **Hardcoded Check**: 検出されたハードコード箇所を `tr("new_key")` に置き換え、JSONに追加。

## 4. 成果物 (Deliverables)
1.  `tools/audit_translation.py` (監査ツール)
2.  `translation_issues.md` (監査レポート)
3.  修正された `Locales` (`en.json`, `jp.json`)
4.  修正された `Source Codes`

## 5. スケジュール
*   **Step 1**: 監査ツール作成と実行
*   **Step 2**: 欠落キーの修正 (`en.json` <-> `jp.json`)
*   **Step 3**: ハードコード箇所の修正
*   **Step 4**: 最終確認 (UI上で言語切り替えテスト)

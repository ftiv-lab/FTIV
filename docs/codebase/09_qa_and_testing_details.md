# 09. QA & Testing Documentation (品質保証とテスト)

## 1. 品質保証 (QA) 戦略の概要
FTIVプロジェクトでは、「壊れにくいコード」と「安全なリファクタリング」を支えるために、多層的な品質保証システムを構築しています。
これらは単なるバグ発見ツールではなく、開発者が安心してコードを変更できるための**セーフティネット**として設計されています。

---

## 2. 自動化スクリプト

### `verify_all.bat` (標準検証)
**パス**: `o:/Tkinter/FTIV/verify_all.bat`

プロジェクトの健全性をワンクリックで確認するための統合スクリプトです。コミット前やプルリクエスト前に必ず実行することが推奨されます。
以下の3つのステップを順次実行し、1つでも失敗すると即座に停止します。

1.  **Static Analysis (静的解析)**: `ruff check` を実行し、構文エラー、未定義変数、インポートミスなどを検出します。
2.  **Architecture Audit (構造監査)**: `check_ui_refs.py` を実行し、アーキテクチャ違反（UIへの直接アクセス）を検出します。
3.  **Test Suite (テスト実行)**: `pytest` を標準モードで実行し、機能テストを行います。

### `verify_stress.bat` (高負荷・カオス検証)
**パス**: `o:/Tkinter/FTIV/verify_stress.bat`

**[Phase 15 追加]** システムの限界や復旧能力を検証するための「意地悪なテスト」専用スクリプトです。
時間がかかるため、リリース前や重要なコアロジック変更後に実行します。

---

## 3. テストスイート構成 (`tests/`)

テストコードは `pytest` フレームワークを使用しており、目的別に分類されています。

### 3.1. ユニットテスト (`tests/*.py`)
各クラスやメソッドが単体で正しく動作するかを検証します。UIを起動せず（またはヘッドレスで）、ロジックそのものをテストします。

*   **`test_window_manager.py`**: ウィンドウの生成、削除、制限チェックなどのライフサイクル管理をテストします。
*   **`test_settings_manager.py`**: 設定の保存・読み込み、Atomic Saveの動作を検証します。
*   **`test_image_actions.py` / `test_layout_actions.py`**: 画像の整列計算や一括操作ロジックをテストします。
*   **`test_ui_structure.py`**: `MainWindow` 内に必須の UI 部品（ボタン、タブ）が正しく配置され、命名されているかをチェックする「構造テスト」です。

### 3.2. インタラクティブ・実体テスト (`tests/test_interactive/`)
`PySide6.QtTest` (QTest) を使用し、実際にアプリを起動してボタンをクリックしたりキー入力を送ったりするシミュレーションテストです。
Mockを極力排除し、**Real Object (実体)** の振る舞いを検証します。

*   **App Flow**:
    *   `test_app_flow.py`: アプリ起動 → タブ切り替え → 終了 という基本的なユーザーフロー。
    *   `test_image_flow.py`: 画像追加ボタンを押した際のダイアログ動作やウィンドウ生成。
    *   `test_persistence.py`: データを保存し、アプリを再起動してデータが復元されるか。
    *   `test_undo_redo.py`: `MoveWindowCommand` の Undo/Redo による座標復元。

*   **Comprehensive Properties (Phase 16)**:
    *   `test_image_properties_comprehensive.py`: `ImageWindow` の全プロパティ（透明度、回転、反転など）の変更と Undo/Redo。
    *   `test_text_properties_comprehensive.py`: `TextWindow` の40以上のプロパティ（フォント、色、アウトラインなど）の網羅的検証。
    *   `test_actions_integration.py`: `pack_all` や `normalize` が実体リストに対して正しく作用するか。

### 3.3. ストレス・カオステスト (`tests/test_stress/`, `tests/test_chaos/`)
**[Phase 15 追加]** システムの堅牢性を検証するためのテスト群です。

*   **`test_heavy_load.py`**: 数百〜数千のウィンドウを生成し、パフォーマンス劣化を確認。
*   **`test_large_image.py`**: 巨大解像度、巨大ファイルサイズの画像読み込み。
*   **`test_config_corruption.py`**: 起動時に設定ファイル (`app_settings.json`) を破壊し、`ConfigGuardian` が自動復旧するか検証。
*   **`test_save_interrupt.py`**: 保存処理中のクラッシュを模倣し、データ消失（0バイトファイル化）を防げるか検証。

### 3.4. Property-Based Testing (`tests/test_hypothesis.py`)
**[Phase 2 追加]** Hypothesisライブラリを使用したプロパティベーステスト。

*   **目的**: 人間が思いつかないエッジケース（境界値、ゼロ、NaN等）を自動発見。
*   **対象モデル**: `WindowConfigBase`, `ImageWindowConfig`, `TextWindowConfig`
*   **テスト数**: 8件

### 3.5. Manager/Theme Tests (`tests/test_spacing_manager.py`, `tests/test_style_theme.py`)
**[Phase 2 追加]** Managerレイヤーの純粋関数テスト。

| ファイル | 対象 | テスト数 |
|---------|------|----------|
| `test_spacing_manager.py` | `SpacingManager` | 10 |
| `test_style_theme.py` | `ThemeManager`, `_TextRenderDummy` | 12 |

---

## 4. テスト統計 (Phase 2 Updated)

| カテゴリ | テスト数 |
|---------|----------|
| Core (ユニット/モデル) | 111 |
| Interactive (UI操作) | 75 |
| Chaos/Stress (堅牢性) | 6 |
| **合計** | **192** |

**Coverage要件**:
*   最低閾値: **27%** (verify_all.batで強制)
*   目標: **30%+**
*   HTMLレポート: `htmlcov/index.html`

---

## 4. 監査・解析ツール (`tools/`)

### 4.1. `tools/check_ui_refs.py`
**アーキテクチャ監査ツール**。
`MainWindow` の肥大化を防ぐため、コントローラーやマネージャーから `self.mw.ui_button` のように UI 部品へ直接アクセスすることを禁止しています。
このスクリプトはソースコードを解析し、そのような違反パターンを検出して警告します。

### 4.2. `tools/audit_translation.py`
**[Phase 17 追加] 翻訳監査ツール**。
日英翻訳の網羅性をチェックします。
1.  **Parity Check**: `en.json` と `jp.json` のキー不一致を検出。
2.  **Usage Check**: コード内で `tr("KEY")` されているキーが JSON に定義されているか確認。
3.  **Hardcode Detection**: UIメソッドに直接文字列リテラル（ハードコード）が渡されていないかヒューリスティックに検出。

---

## 5. 静的解析 (Static Analysis)

### Ruff Configuration
**設定ファイル**: `pyproject.toml`
Pythonの高速リンター "Ruff" を採用しています。
*   **厳格なルール**: 未使用のインポート、未定義の変数、複雑すぎるコードなどをエラーとして報告します。
*   **除外設定**: ビルド生成物 (`.venv313`, `dist_test`) は解析対象外としています。

---

## 6. ランタイム保護 (`managers/config_guardian.py`)

### `ConfigGuardian`
テストだけでなく、本番環境での安定性を高めるための自己修復モジュールです。
アプリ起動時に `main.py` から呼び出され、以下のチェックを行います。

*   **JSON整合性**: 設定ファイルが破損していないかチェックします。
*   **自動バックアップ**: 破損を検知した場合、壊れたファイルを `xx.json.bak` に退避し、デフォルト設定でアプリを起動させます（「起動しない」という最悪の事態を防ぎます）。

---

## 7. テスト実行方法

開発者は以下のコマンドを使用できます。

```powershell
# 一括検証 (推奨)
.\verify_all.bat

# 高負荷・カオス検証 (リリース前)
.\verify_stress.bat

# 単体テストのみ実行
pytest

# 特定のテストのみ実行
pytest tests/test_interactive/test_image_properties_comprehensive.py
```

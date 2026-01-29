# Phase 7: Quality & Testing (Strict Types & Unit Tests)

Phase 6 でビジネスロジックの分離が完了しました。Phase 7 では、これらの分離されたコンポーネントの品質を担保するため、静的解析（型安全性）と自動テスト（Unit Test）を導入します。

- [x] 計画: テスト環境の構築と対象範囲の選定 <!-- id: 1 -->
- [x] 実行: 型安全性の強化 (Strict Type Safety) <!-- id: 2 -->
    - [x] `ui/controllers/*.py` の `Any` を具体的な型 (`QWidget`, `ImageWindow` 等) に置換
    - [x] 循環参照を `TYPE_CHECKING` ブロックで回避
- [x] 実行: 単体テストの作成 (Unit Testing) <!-- id: 3 -->
    - [x] `tests/` ディレクトリ作成と `pytest` 導入
    - [x] `tests/test_layout_actions.py`: 整列ロジックのテスト
    - [x] `tests/test_image_actions.py`: 一括操作ロジックのテスト (Mock使用)
- [x] 検証: テスト実行とカバレッジ確認 (5 passed) <!-- id: 4 -->

# Phase 8: Comprehensive Quality Assurance (Structure & Tests)

- [x] 計画: 対象コンポーネントの洗い出しとテスト設計 <!-- id: 5 -->
- [x] 実行: Manager層・Tab層の型安全化 (Global Strict Typing) <!-- id: 6 -->
    - [x] `managers/*.py` (SettingsManager, WindowManager)
    - [x] `ui/tabs/*.py` (ImageTab, TextTab, etc.)
- [x] 実行: テストカバレッジの拡大 (Expanded Testing) <!-- id: 7 -->
    - [x] `tests/test_connector_actions.py`: コネクタ操作のテスト
    - [x] `tests/test_settings_manager.py`: 設定管理ロジックのテスト
    - [x] `tests/test_window_manager.py`: ウィンドウ管理ロジックのテスト
- [x] 検証: 全テストの実行とリグレッション確認 (17 passed) <!-- id: 8 -->

# Phase 9: Event Handling Separation (Controller Pattern)

- [x] 計画: `MainController` の設計と責務定義 <!-- id: 9 -->
- [x] 実行: `MainController` の実装 <!-- id: 10 -->
    - [x] `ui/controllers/main_controller.py` 作成
    - [x] `MainWindow` のシグナル接続ロジックを移動
    - [x] アプリ状態管理ロジック (`handle_app_state_change`) を移動
- [x] 実行: `MainWindow` のリファクタリング <!-- id: 11 -->
    - [x] `MainController` の DI 導入
    - [x] 不要になった旧イベントハンドラ削除
- [x] 検証: 動作確認とテスト (22 passed) <!-- id: 12 -->
    - [x] `tests/test_main_controller.py` 作成と実行
    - [x] アプリ起動・操作の手動確認

# Phase 10: Exception Handling & Logging Standardization

- [x] 計画: エラーハンドリング指針の策定 <!-- id: 13 -->
- [x] 実行: 例外処理の標準化 <!-- id: 14 -->
    - [x] `managers/window_manager.py`: ~30カ所のサイレントエラー修正
    - [x] `text_tab.py`, `settings_manager.py`: ログ詳細化
    - [x] `ui/main_window.py`: レガシーロジックの保護
- [x] 検証: 全テスト実行 (22 passed) と構文チェック <!-- id: 17 -->

# Phase 11: Interaction & Command Flow Decoupling (Retry)

- [/] 実行: Interaction Decoupling リファクタリング
    - [x] `AnimationManager` の UI 参照エラー修正
    - [ ] `MainWindow` ラッパーメソッドの整理（継続中）

# Phase 12: Reliability & Prevention Standards (Quality Assurance)

- [x] 計画: 品質保証プロセスの策定 (Pre-flight Check導入) <!-- id: 18 -->
- [x] 実行: UI構造整合性テストの作成 (`tests/test_ui_structure.py`) <!-- id: 19 -->
- [x] 実行: 参照監査スクリプトの作成 (`tools/check_ui_refs.py`) <!-- id: 20 -->
- [x] 実行: エージェント行動指針(Memory/Doc)のアップデート <!-- id: 21 -->
- [x] 検証: テスト環境の動作確認と新フローの試行 (Passed) <!-- id: 22 -->

# Phase 13: Advanced Quality Assurance (Interactive Tests & Safety Nets)

- [x] 実行: Ruff Linter の導入とプロジェクト全体のコードクリーンアップ <!-- id: 23 -->
- [x] 実行: 自己診断機能 `ConfigGuardian` の実装と `main.py` への統合 <!-- id: 24 -->
- [x] 実行: ワンクリック検証スクリプト `verify_all.bat` の作成 <!-- id: 25 -->
- [x] 実行: `QTest` による GUI操作自動テスト (`test_app_flow.py`) の実装 <!-- id: 26 -->
- [x] 検証: 全自動チェックの完走 (Passed) <!-- id: 27 -->

# 環境刷新 / Environment Upgrade (2026-01-18)
- [x] Runtime: Python 3.14.2 (.venv314)
- [x] Dependencies: `requirements.txt` Created (PySide6 6.10, Pillow 12.1)
- [x] QA Status: All 27 tests PASSED (including E2E)

# Phase 11 (Resumed): 最終的な疎結合化 (Final Decoupling)
- [x] 画像整列ロジック (`img_pack_*`) を `ImageActions` へ移動
- [x] シーン管理ロジック (`scene_*`) を `SceneActions` へ移動
- [x] `MainWindow` のラッパーメソッド削除と委譲実装
- [x] テストカバレッジの拡大 (Image Flow, Persistence, Undo/Redo) -> **30 Passed**

# Phase 14: リリース準備とNuitka統合
- [x] パッケージング: Nuitka + Python 3.13 環境の構築
- [x] ドキュメント: `README.md`, `CONTRIBUTING.md` の整備
- [x] 成果: `build_release.py` による安全なビルドパイプラインの確立

# Phase 15: 意地悪なテスト実験 (Stress & Chaos)
- [x] 負荷テスト: 200個のウィンドウ生成と8K画像(64MP)読み込みをクリア
- [x] カオス実験: 設定ファイルの破損自動復旧(ConfigGuardian)と、保存中断時のデータ保護(Atomic Save)を検証
- [x] 検証: `verify_stress.bat` による高負荷検証スイートの確立

# Phase 16: 実体による網羅的テスト強化 (Comprehensive Testing)
- [x] ImageWindow: 全プロパティ(透明度・回転等)のUndo/Redo検証 (`test_image_properties_comprehensive.py`)
- [x] TextWindow: 40項目以上のスタイル設定網羅検証 (`test_text_properties_comprehensive.py`)
- [x] Controller統合: `pack_all`, `normalize` 等の実体動作検証 (`test_actions_integration.py`)
- [x] 成果: `AttributeError` 等の単純ミスを完全に防ぐセーフティネットの完成

# Phase 17: Localization Audit (日英翻訳網羅化)
- [x] 監査: `tools/audit_translation.py` によるキー欠落とハードコードの検出
- [x] 修正: `en.json` / `jp.json` の完全同期 (Parity Fix)
- [x] 成果: 言語リソースの完全性確保 (Zero Issues)

# Phase 18-21: MindMap Development (Experiemntal)
- *Note: These phases involved the development of MindMap features, which were ultimately removed in Phase 22 to prioritize core stability.*

# Phase 22: V1.0 Release (Pivot & Cleanup)
- [x] 決断: マインドマップ機能の完全削除による「選択と集中」
- [x] 実行: `feature/mindmap_v1` への退避と `master` のクリーンアップ
- [x] 検証: V1.0 テストスイートの通過 (Stabilized)
- [x] 成果: [ポストモーテム文書](22_v1_release_postmortem.md) の作成

# Phase 23: Udemy Online Course Planning
- [x] 計画: 3つの視点（Senior Engineer, Udemy Expert, AI Specialist）による構想策定
- [x] 成果: `docs/online_course_plan/` に企画書群を作成

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
- [x] 実行: `ui/main_window.py` の例外処理修正 <!-- id: 14 -->
- [x] 実行: `managers/` の例外処理修正 <!-- id: 15 -->
- [x] 実行: `ui/tabs/` の例外処理修正 <!-- id: 16 -->
- [x] 検証: ログ出力テストと動作確認 (22 passed) <!-- id: 17 -->

# Phase 11: User Interaction & Command Flow Decoupling
 
- [x] 計画: ラッパーメソッドの特定とアクセサ設計 <!-- id: 18 -->
- [x] 実行: `MainController` への Action 公開 <!-- id: 19 -->
- [x] 実行: `ui/tabs/` の呼び出し元修正 (Direct Access化) <!-- id: 20 -->
- [x] 実行: `MainWindow` の不要ラッパーメソッド削除 <!-- id: 21 -->
- [x] 検証: リグレッションテストと動作確認 <!-- id: 22 -->

- [x] **[Phase 11] ユーザー操作とコマンドフローの分離**
  - [x] ラッパーメソッドの削除 (`ui/main_window.py`)
  - [x] 呼び出し元の修正 (`ui/controllers/*` または Manager への直接アクセス)
  - [x] Lintエラー解消 (F841, E402等) と `verify_all.bat` の通過
- [x] **緊急修正 (Linting & Stability)**
  - [x] `layout_actions.py` の F841 修正
  - [x] `base_window.py`, `connector.py` の E402/I001 修正
  - [x] `verify_all.bat` の正常動作確認

- [x] **Phase 11 (Resumed): 最終的な疎結合化 (Final Decoupling)**
  - [x] 画像整列ロジック (`img_pack_*`) を `ImageActions` へ移動
  - [x] シーン管理ロジック (`scene_*`) を `SceneActions` へ移動
  - [x] `MainWindow` のラッパーメソッド削除と委譲実装
  - [x] 機能検証 (Verification)

# Phase 12: 信頼性と防止基準の策定 (Quality Assurance)

- [x] 計画: 品質保証プロセスの策定 (Pre-flight Check導入)
- [x] 実行: UI構造整合性テストの作成 (`tests/test_ui_structure.py`)
- [x] 実行: 参照監査スクリプトの作成 (`tools/check_ui_refs.py`)
- [x] 実行: エージェント行動指針(Memory/Doc)のアップデート
- [x] 検証: テスト環境の動作確認と新フローの試行 (Passed)

# Phase 13: 高度な品質保証 (Interactive Tests & Safety Nets)

- [x] 実行: Ruff Linter の導入とプロジェクト全体のコードクリーンアップ
- [x] 実行: 自己診断機能 `ConfigGuardian` の実装と `main.py` への統合
- [x] 実行: ワンクリック検証スクリプト `verify_all.bat` の作成
- [x] 実行: `QTest` による GUI操作自動テスト (`test_app_flow.py`) の実装
- [x] 実行: 全ドキュメントの同期 (docs/codebase, docs/refactoring_plans)
- [x] 検証: 全自動チェックの完走 (Passed)

# 環境刷新 (2026-01-18)
- [x] ランタイム: Python 3.14.2 (.venv314)
- [x] 依存関係: `requirements.txt` 作成 (PySide6 6.10, Pillow 12.1)
- [x] QAステータス: 全27テスト合格 (E2E含む)

# 緊急修正 (Regressions & Audits)
- [x] アニメーションタブ設定反映の修正（AnimationManager UI参照先ミス修正）
- [x] ダブルクリックアニメーション機能の修正（Ctrl+DblClick導入）
- [x] **監査と修正詳細**
  - [x] `AnimationManager` 参照エラー修正
  - [x] ダブルクリックアニメーション修正
  - [x] UI参照監査 (合格)

# Phase 12-Extended: テストカバレッジの拡大
- [x] **画像機能テスト**
  - [x] `tests/test_interactive/test_image_flow.py` 実装 (Mock QFileDialog)
- [x] **全体信頼性テスト**
  - [x] `tests/test_interactive/test_persistence.py` 実装 (Save/Load/Restore)
    - GUIダイアログをバイパスし、Atomic Saveロジックをテスト
  - [x] `tests/test_interactive/test_undo_redo.py` 実装 (Command Stack)
    - `MoveWindowCommand` の push/undo/redo ロジック検証
- [x] **結果**: 全30テスト合格 (Passed)

# Phase 14: リリース準備とNuitka統合
- [x] **パッケージング (Nuitka)**
  - [x] Nuitka互換性チェック (Python 3.13必須)
  - [x] `.venv313` への Nuitka & Zstandard インストール/アップグレード
  - [x] ビルドテスト (Core + Launcher) -> `FTIV_Test.exe` 動作確認
  - [x] `build_release.py` へのバージョン安全チェック追加
- [x] **ドキュメント**
  - [x] README.md 作成 (アーキテクチャ & ビルドガイド)
  - [x] CONTRIBUTING.md 作成
- [/] **仕上げ (Polish)**
  - [x] ビジュアル監査 (アイコン確認、ダークモード適用確認)
- [x] **結果**: リリースパイプライン確立完了

# Phase 15: Stress & Chaos Testing (意地悪なテスト)
- [ ] **計画策定**
  - [x] テスト計画書の作成 (`phase15_chaos_testing_plan.md`)
- [ ] **負荷テスト (Stress Testing)**
  - [x] `tests/test_stress/test_heavy_load.py` 実装 (Massive Windows)
  - [x] `tests/test_stress/test_large_image.py` 実装 (Huge Image)
- [x] **カオス実験 (Chaos Engineering)**
  - [x] `tests/test_chaos/test_config_corruption.py` 実装 (ConfigGuardian検証)
  - [x] `tests/test_chaos/test_save_interrupt.py` 実装 (Atomic Save検証)
- [x] **検証**
  - [x] `verify_stress.bat` の作成と実行
- [x] **結果**: ストレス耐性と復旧能力の証明完了

# Phase 14 (Final): リリースビルド生成
- [x] **環境復旧**
  - [x] フォルダリネーム (`Tkinter用` -> `Tkinter`) 対応
  - [x] `.venv313` / `.venv314` 再構築
- [x] **リリースビルド**
  - [x] `build_release.py` 実行 (LNK1104エラー解消)
  - [x] `dist/FTIV_Free` および `dist/FTIV_Pro` の生成確認
- [x] **完了**: 配布可能パッケージの完成

# Phase 16: Comprehensive Real-Object Testing & Hardening
- [x] **計画策定 (Planning)**
    - [x] テスト計画書の作成 (`phase16_testing_plan.md`)
    - [x] `set_undoable_property` 使用状況の監査
- [x] **ImageWindow Coverage**
    - [x] `tests/test_interactive/test_image_properties_comprehensive.py` 作成
    - [x] 全プロパティ(opacity, rotation, etc.)のUndo/Redo検証
- [x] **TextWindow Coverage**
    - [x] `tests/test_interactive/test_text_properties_comprehensive.py` 作成
    - [x] 40+項目(font, color, gradient)の網羅的パラメータライズドテスト
- [x] **Integration Tests (Controllers)**
    - [x] `tests/test_interactive/test_actions_integration.py` 作成
    - [x] `pack_all_*`, `normalize_*` 系の実体検証
- [x] **検証 (Verification)**
    - [x] `verify_all.bat` 更新と実行
    - [x] 最終品質確認

# Phase 17: Localization Audit & Completion (日英翻訳網羅化)
- [x] **計画策定 (Planning)**
    - [x] 監査計画書の作成 (`phase17_translation_audit_plan.md`)
- [x] **監査実行 (Auditing)**
    - [x] 監査ツール作成 (`tools/audit_translation.py`)
    - [x] `translation_issues.md` (レポート) 生成
    - [x] キー不一致 (Parity) チェック
    - [x] ハードコード (Heuristic) チェック
- [x] **修正 (Fixing)**
    - [x] 欠落キーの追加
    - [x] ハードコード箇所の `tr()` 化
- [x] **確認 (Verification)**
    - [x] 再監査 (Zero Issues check)
    - [x] UI言語切り替え動作確認

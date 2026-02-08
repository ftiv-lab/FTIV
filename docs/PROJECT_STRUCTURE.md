# FTIV プロジェクト構造 (Project Structure)

> **更新ルール**: 新規ディレクトリ・重要ファイル追加時は本ドキュメントを更新すること

## ディレクトリ構成

### 📦 Core Production Code

| Directory | Files | Purpose |
|-----------|-------|---------|
| `ui/` | 7 files + 6 subdirs | UI層全体。MainWindow, Tabs, Dialogs, Controllers |
| `ui/controllers/` | - | MainController等のビジネスロジック仲介 |
| `ui/tabs/` | - | 各タブ (General, Text, Image, Animation等) |
| `ui/dialogs/` | - | ダイアログウィンドウ |
| `managers/` | 11 files | バックエンドロジック (WindowManager, FileManager等) |
| `models/` | 8 files | データモデル (Pydantic Config, Enums) |
| `windows/` | 6 files | オーバーレイウィンドウ (TextWindow, ImageWindow, Connector) |
| `utils/` | 12 files | ユーティリティ (Logger, Translator, Commands) |

### 🧪 Testing & Quality

| Directory | Files | Purpose |
|-----------|-------|---------|
| `tests/` | 14+ files | メインテストスイート |
| `tests/test_interactive/` | 11 files | GUI操作を含む統合テスト |
| `tests/test_chaos/` | 2 files | 破損・異常系シナリオテスト |
| `tests/test_stress/` | 3 files | 負荷・パフォーマンステスト |
| `scripts/` | 7 files | 開発用スクリプト (pre-commit hook等) |
| `tools/` | 2 files | 静的解析ツール (UI参照チェック, 翻訳監査) |

### 📁 Configuration & Assets

| Directory/File | Purpose |
|----------------|---------|
| `pyproject.toml` | 依存関係・Ruff・Mypy設定 |
| `assets/` | スタイルシート・アイコン・フォント |
| `json/` | デフォルト設定・プリセット |
| `utils/locales/` | 国際化ファイル (en.json, jp.json) |

---

## 主要ファイル役割

### Entry Point
- `main.py` - アプリケーションエントリーポイント

### Core Architecture (MVC風)
- `ui/main_window.py` - View (62KB)
- `ui/controllers/main_controller.py` - Controller Hub
- `managers/window_manager.py` - Model/State Manager (47KB)

### Data Layer
- `models/window_config.py` - Pydantic永続化モデル (ここに無いプロパティは保存されない)
- `managers/file_manager.py` - JSON/シーン保存・読込

### Rendering
- `windows/base_window.py` - オーバーレイ基底クラス (56KB)
- `windows/text_renderer.py` - テキスト描画エンジン (56KB)

---

## 品質ゲート

| Script | Purpose |
|--------|---------|
| `verify_all.bat` | 完全検証 (Ruff→Mypy→UIAudit→Pytest) |
| `verify_debug.bat` | デバッグモード検証 (ログファイル出力) |
| `verify_stress.bat` | ストレステスト専用 |
| `scripts/hook_pre_commit.py` | コミット前チェック |

---

*Last Updated: 2026-02-08*
*Maintained by Antigravity*

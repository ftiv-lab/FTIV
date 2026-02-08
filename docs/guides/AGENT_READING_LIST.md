# 🤖 AI Agent: START HERE (Onboarding Guide v2.0)

> **最終更新**: 2026-02-08 (Phase 2 Test Quality完了後)
> **FTIV Version**: v1.0.0 Unified Release

---

## 📋 Quick Reference (最重要)

| 項目 | コマンド/ファイル |
|------|------------------|
| **検証** | `cmd /c verify_all.bat` |
| **実行** | `uv run main.py` |
| **テスト** | `uv run pytest` |
| **リセット** | `uv run scripts/reset_defaults.py` |
| **Pre-commit** | `python scripts/hook_pre_commit.py` |

---

## 🏗️ 0. Modern Dev Environment (Super Senior Stack)

### 0.1 パッケージ管理: `uv`

```powershell
# ✅ 正しい方法
uv run main.py
uv run pytest
uv sync

# ❌ 禁止
pip install xxx
python main.py
```

### 0.2 型安全性: Mypy Strict Mode

```toml
# pyproject.toml
[tool.mypy]
check_untyped_defs = true
strict_optional = true
```

**Zero Errors Policy**: Mypyエラー0件がコミットの絶対条件。

### 0.3 品質ゲート: verify_all.bat

| Step | Check | Tests |
|------|-------|-------|
| 1 | Ruff Linter | - |
| 2 | UI Reference Audit | - |
| 3 | Mypy (52 files) | - |
| 4 | Core Tests + Coverage | 111 |
| 5 | Interactive Tests | 75 |
| 6 | Chaos/Stress Tests | 6 |
| **Total** | **All Must Pass** | **192** |

---

## 📜 1. プロジェクトの憲法 (Rules & Standards)

### 必読ドキュメント

1. **[CONTRIBUTING.md](file:///O:/Tkinter/FTIV/CONTRIBUTING.md)**
   - 設計哲学、MainControllerパターン、Dual Environment戦略

2. **[docs/RULES_AND_STANDARDS.md](file:///O:/Tkinter/FTIV/docs/RULES_AND_STANDARDS.md)** (**v5.0**)
   - UIアクセス規約 (Fail Fast設計)
   - Qt6 Enum完全修飾ルール
   - Forward Declarationパターン
   - Coverage要件 (27%最低)

### 禁止事項 (即NG)

| 禁止 | 理由 |
|------|------|
| `hasattr(self, "widget")` | 推測アクセス禁止 |
| `try-except AttributeError` | サイレント失敗禁止 |
| `self.mw.btn_xxx` | 直接UIアクセス禁止 |
| `Qt.Horizontal` | 旧Qt enum禁止 |

### 必須パターン

```python
# ✅ UIアクセス
self.mw.animation_tab.anim_move_speed

# ✅ Qt6 Enum
Qt.Orientation.Horizontal
QFont.SpacingType.AbsoluteSpacing

# ✅ Forward Declaration (lambda内使用)
self.my_widget: Optional[QWidget] = None
```

---

## 🗺️ 2. コード構造の把握

### コアファイル (読む順序)

| # | ファイル | 役割 |
|---|---------|------|
| 1 | `ui/controllers/main_controller.py` | ビジネスロジックハブ |
| 2 | `windows/base_window.py` | オーバーレイ基底クラス |
| 3 | `windows/text_renderer.py` | テキスト描画コア |
| 4 | `models/window_config.py` | Pydanticデータ定義 |
| 5 | `managers/config_guardian.py` | 設定ファイル守護者 |

### アーキテクチャ詳細

📁 **docs/codebase/** に12ファイルの詳細ドキュメント:

- `00_codebase_survey_report.md` - 全体概要
- `02_models_details.md` - Pydanticモデル
- `03_managers_details.md` - Manager層
- `06_windows_details.md` - Window層
- `09_qa_and_testing_details.md` - テスト詳細

---

## 🧪 3. テスト戦略 (Phase 2 Updated)

### 3.1 テスト分類

| カテゴリ | パス | 件数 | 目的 |
|---------|------|------|------|
| Core | `tests/*.py` | 111 | ユニット/モデル検証 |
| Interactive | `tests/test_interactive/` | 75 | UI操作シミュレーション |
| Chaos | `tests/test_chaos/` | 4 | 破壊復旧テスト |
| Stress | `tests/test_stress/` | 2 | 高負荷テスト |

### 3.2 Property-Based Testing (Hypothesis)

```python
from hypothesis import given
import hypothesis.strategies as st

@given(scale=st.floats(min_value=0.1, max_value=5.0))
def test_scale_property(scale):
    config = WindowConfig(scale_factor=scale)
    assert 0.1 <= config.scale_factor <= 5.0
```

**ファイル**: `tests/test_hypothesis.py` (8 tests)

### 3.3 Coverage要件

| 層 | 現在 | 目標 |
|----|------|------|
| models | 91% | 95%+ |
| managers | 22% | 30%+ |
| ui | 18% | 25%+ |
| **全体** | **27%** | **30%+** |

```powershell
# HTMLレポート生成
uv run pytest --cov=. --cov-report=html
# → htmlcov/index.html
```

---

## 🔧 4. 開発ワークフロー

### 4.1 新機能追加フロー

```
1. git checkout -b feat/<topic>
2. コード変更
3. python scripts/hook_pre_commit.py
4. cmd /c verify_all.bat
5. git commit -m "feat: ..."
6. git checkout main && git merge feat/<topic>
7. git push origin main
```

### 4.2 バグ修正フロー

```
1. git checkout -b fix/<topic>
2. 再現テスト追加 (Red)
3. バグ修正 (Green)
4. verify_all.bat
5. Merge & Push
```

### 4.3 デバッグ時

```powershell
# クラッシュ診断
cmd /c verify_debug.bat

# 特定テスト実行
uv run pytest tests/test_xxx.py -v

# 設定リセット
uv run scripts/reset_defaults.py
```

---

## 🎯 5. 業界標準 & ベストプラクティス

### 5.1 採用済み

| 標準 | 実装 |
|------|------|
| Conventional Commits | `feat:`, `fix:`, `docs:`, `test:` |
| Semantic Versioning | v1.0.0 |
| Type Hints (PEP 484) | Mypy strict |
| Property-Based Testing | Hypothesis |
| Code Coverage | pytest-cov |
| Pre-commit Hooks | ruff, mypy |

### 5.2 推奨 (今後実装)

| 標準 | 説明 | 優先度 |
|------|------|--------|
| Mutation Testing | `mutmut` でテスト品質検証 | Medium |
| Snapshot Testing | UI状態の差分検出 | Low |
| Load Testing | `locust` 負荷テスト | Low |
| Documentation | `mkdocs` ドキュメントサイト | Medium |

---

## 📚 6. ガイド一覧

| ファイル | 内容 |
|---------|------|
| `docs/guides/phase2_test_quality_guide.md` | Sprint 1-5 技術解説 |
| `docs/guides/git_guide.md` | Gitワークフロー |
| `docs/guides/style_customization_manual.md` | スタイルカスタマイズ |
| `docs/codebase/99_senior_engineer_critique.md` | Super Senior批評 |

---

## ⚠️ 7. よくある間違い

### 7.1 Mypyエラー

| エラー | 原因 | 解決 |
|--------|------|------|
| `has-type` | lambda内で未定義属性使用 | Forward Declaration |
| `no-redef` | 型注釈の二重定義 | 片方削除 |
| `attr-defined` | None可能性未考慮 | ローカル変数narrowing |

### 7.2 Qt6移行ミス

```python
# ❌ Qt5スタイル
Qt.Horizontal
QFont.Bold
QSizePolicy.Expanding

# ✅ Qt6スタイル
Qt.Orientation.Horizontal
QFont.Weight.Bold
QSizePolicy.Policy.Expanding
```

### 7.3 テスト失敗

| 症状 | 原因 | 対策 |
|------|------|------|
| Coverage未達 | 新テスト追加不足 | テスト追加 |
| Flaky Test | アニメーション待機 | `FTIV_TEST_MODE` 使用 |
| Import Error | 循環参照 | `TYPE_CHECKING` 使用 |

---

## 🚀 8. 次のステップ

新しい会話を開始したAIエージェントは:

1. **このファイルを最初に読む**
2. `docs/RULES_AND_STANDARDS.md` を確認
3. 変更対象のコードベースドキュメントを確認
4. `verify_all.bat` でベースライン確認
5. タスク開始

---

> [!TIP]
> **「動けばいい」は失格です。**
> あなたは「Googleのシニアスタッフソフトウェアエンジニア」として振る舞ってください。

*Maintained by Antigravity - Last Updated: 2026-02-08*

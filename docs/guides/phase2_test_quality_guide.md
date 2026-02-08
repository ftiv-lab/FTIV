# Test Quality Phase 2 技術解説書

> **対象読者**: 初〜中級Pythonプログラマー
> **作成日**: 2026-02-08
> **著者**: Antigravity (Super Senior観点)

---

## 概要

Phase 2では、FTIVプロジェクトのテスト品質を大幅に向上させました。

| 指標 | Before | After | 改善 |
|------|--------|-------|------|
| テスト数 | 〜80 | **117** | +46% |
| カバレッジ | 〜20% | **27%** | +35% |
| Mypyエラー | 複数 | **0** | 完全解消 |

---

## Sprint 1: 低リスク・高インパクト

### 1.1 レガシーファイル削除

**削除したファイル:**
```
tests/repro_json_legacy.py
tests/reproduce_issue/verify_property_panel_flags.py
```

**理由:**
- 一時的なデバッグ用スクリプト
- pre-commitで警告が出続けていた
- 本番コードには無関係

> [!TIP]
> デバッグ用スクリプトは `scripts/debug/` に配置し、`.gitignore` に追加するのがベストプラクティス。

---

### 1.2 Qt Enum修正 (property_panel.py)

**問題**: PySide6 + Mypy組み合わせで、古いQt enum記法がエラーに。

```python
# ❌ Before (Mypy Error)
slider.setOrientation(Qt.Horizontal)

# ✅ After (Mypy Clean)
slider.setOrientation(Qt.Orientation.Horizontal)
```

**修正箇所**: 11箇所

**なぜこれが重要?**
- Qt6では「完全修飾名」が推奨
- 将来のQt7で旧記法は非推奨に
- Mypy strict modeで検出可能

---

### 1.3 ConfigGuardian 100%カバレッジ

`managers/config_guardian.py` のテストカバレッジを100%に。

**追加したテストケース:**
| テスト名 | カバー内容 |
|---------|-----------|
| `test_nonexistent_base_directory` | 存在しないディレクトリ |
| `test_corrupted_json_recovery` | 破損JSON自動復旧 |
| `test_missing_required_keys_recovery` | 必須キー欠損時の復旧 |
| `test_backup_created_on_corruption` | バックアップ作成確認 |
| `test_unexpected_read_exception` | 予期せぬ例外ハンドリング |

> [!IMPORTANT]
> ConfigGuardianは設定ファイルの「守護者」。ここが壊れると全アプリが起動不能に。100%カバレッジは必須。

---

## Sprint 2: Hypothesis導入

### 2.1 Property-Based Testing とは？

**従来のテスト (Example-Based):**
```python
def test_scale_factor():
    config = WindowConfig(scale_factor=1.5)
    assert config.scale_factor == 1.5
```

**Hypothesisテスト (Property-Based):**
```python
@given(scale=st.floats(min_value=0.1, max_value=5.0))
def test_scale_factor_property(scale):
    config = WindowConfig(scale_factor=scale)
    assert 0.1 <= config.scale_factor <= 5.0
```

**違い:**
- Example-Based: 特定の値でテスト
- Property-Based: 「任意の有効入力で成り立つべき性質」をテスト

> [!NOTE]
> Hypothesisは自動的に境界値、ゼロ、極大値、NaN などを試す。人間では思いつかないエッジケースを発見。

---

### 2.2 追加したHypothesisテスト

`tests/test_hypothesis.py`:

| テストクラス | テスト内容 |
|-------------|-----------|
| `TestWindowConfigHypothesis` | scale_factor, flags, anchor の任意値テスト |
| `TestImageWindowConfigHypothesis` | opacity, rotation_angle の境界テスト |
| `TestTextWindowConfigHypothesis` | font_size, text_opacity の境界テスト |

**発見したバグ:**
- `WindowConfigBase` に `scale_factor` が存在しないことが判明 → テスト修正
- `move_speed` が `int` 期待なのに `float` を渡していた → テスト修正

---

## Sprint 3: inline_editor_mixin Qt Enum

### 3.1 修正箇所

`windows/mixins/inline_editor_mixin.py` で11箇所のQt enum修正:

```python
# ❌ Before
font.setLetterSpacing(QFont.AbsoluteSpacing, value)
font.setLetterSpacing(QFont.PercentageSpacing, 100)

# ✅ After
font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, value)
font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 100)
```

**影響範囲:**
- テキストウィンドウのインライン編集機能
- フォントスペーシング設定

---

## Sprint 4: SpacingManager Tests

### 4.1 SpacingManagerとは?

テキストウィンドウの余白・行間を管理するクラス。

**主要メソッド:**
| メソッド | 役割 |
|---------|------|
| `validate_spacing_value()` | 値を有効範囲にクランプ |
| `validate_settings()` | SpacingSettings全体を検証 |
| `dialog_tuple_to_legacy_dict()` | ダイアログ値→設定辞書変換 |
| `get_defaults_for_mode()` | 横書き/縦書きのデフォルト取得 |

---

### 4.2 発見した制約

テスト作成中に発見:

```python
# SpacingManagerの実際の制約
MIN_SPACING = -0.5   # 最小スペーシング
MAX_SPACING = 5.0    # 最大スペーシング
MIN_MARGIN = 0.0     # 最小マージン（非負）
MAX_MARGIN = 5.0     # 最大マージン
```

> [!WARNING]
> これらの定数はドキュメント化されていなかった。テストで初めて明確に。

---

### 4.3 追加したテスト (10件)

```python
class TestSpacingManagerValidation:
    test_validate_spacing_value_clamped_to_max    # 上限クランプ
    test_validate_spacing_value_clamped_to_min    # 下限クランプ
    test_validate_spacing_value_margin_non_negative  # マージン非負
    test_validate_spacing_value_passthrough_valid    # 有効値パススルー
    test_validate_settings_returns_spacing_settings  # 戻り値型確認

class TestSpacingManagerDialogConversion:
    test_dialog_tuple_to_legacy_dict_structure  # 出力キー確認
    test_dialog_tuple_preserves_values          # 値保持確認

class TestSpacingManagerDefaults:
    test_get_defaults_for_mode_horizontal  # 横書きデフォルト
    test_get_defaults_for_mode_vertical    # 縦書きデフォルト
    test_defaults_match_expected_order     # 順序一致確認
```

---

## Sprint 5: ThemeManager/StyleManager Tests

### 5.1 DARK_THEME トークン検証

`managers/theme_manager.py` の `DARK_THEME` 辞書を検証:

```python
DARK_THEME = {
    "@bg_primary": "#2b2b2b",
    "@bg_secondary": "#323232",
    "@surface": "#333333",
    "@border": "#404040",
    "@accent_primary": "#007acc",
    "@text_primary": "#e0e0e0",
    ...
}
```

**テスト内容:**
1. 必須トークンが存在するか
2. 値が有効なHex色か
3. 背景色が実際に「暗い」か（輝度100未満）

---

### 5.2 _TextRenderDummy テスト

`StyleManager` 内部の `_TextRenderDummy` クラスをテスト:

**目的:** `TextRenderer` に渡すための軽量ダミー。実際の `TextWindow` を生成せずにサムネイル作成。

**テスト内容:**
| テスト | 確認事項 |
|--------|---------|
| `test_dummy_creates_from_config` | ConfigからDummy生成 |
| `test_dummy_exposes_font_family` | font_family公開 |
| `test_dummy_exposes_font_size` | font_size公開 |
| `test_dummy_exposes_colors` | font_color, background_color公開 |
| `test_dummy_pos_returns_qpoint` | pos()がQPoint(0,0)返却 |
| `test_dummy_shadow_properties` | 影プロパティ群 |
| `test_dummy_outline_properties` | 縁取りプロパティ群 |
| `test_dummy_text_gradient_properties` | グラデーション設定 |
| `test_dummy_vertical_mode` | 縦書きモード |

---

## Mypy Type Errors 修正

### 修正内容

| ファイル | 問題 | 解決策 |
|---------|------|--------|
| `image_tab.py` | `img_sel_display_combo` 使用前参照 | Forward declaration追加 |
| `image_actions.py` | `current_row` 型注釈不足 | `list` 明示 |
| `main_window.py` | `manual_dialog` None可能性 | ローカル変数でnarrowing |

### Forward Declaration パターン

```python
class ImageTab(QWidget):
    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        
        # Forward declaration for Mypy type inference
        self.img_sel_display_combo: Optional[QComboBox] = None
        
        self._setup_ui()  # ここで実際に代入
```

**なぜ必要?**
- Mypyは静的解析ツール
- lambda内での `self.xxx` 参照を解析時点でチェック
- 定義前の使用はエラーになる

---

## verify_all.bat 更新

### Coverage設定

```batch
REM Coverage threshold set to 27% (stable baseline). Full project coverage at 31%.
uv run pytest tests/ -k "not interactive and not chaos and not stress and not inline" \
    --cov=ui --cov=managers --cov=windows --cov=models \
    --cov-report=term-missing --cov-report=html \
    --cov-fail-under=27 --maxfail=1 --showlocals -v
```

**ポイント:**
- `--cov-fail-under=27`: 27%未満でCI失敗
- `--cov-report=html`: `htmlcov/` にレポート生成
- 対象: `ui`, `managers`, `windows`, `models` の4層

---

## 学習ポイントまとめ

### 1. テストは仕様のドキュメント

SpacingManagerの制約 (MIN_SPACING=-0.5) はコード内コメントにしかなかった。
テストを書くことで「公式な仕様」として明文化。

### 2. Property-Based Testingの威力

Hypothesisを導入することで:
- 境界値テストの網羅性向上
- 型の不整合を自動発見
- ドキュメント化されていない制約の発見

### 3. Qt6のEnum完全修飾

PySide6 + Mypy環境では、すべてのQt enumを完全修飾する:
```python
Qt.Orientation.Horizontal  # ✅
Qt.Horizontal              # ❌ (動くがMypy警告)
```

### 4. Forward Declarationパターン

クラス属性をlambda/コールバック内で使用する場合、`__init__`冒頭で`Optional`宣言:
```python
self.my_widget: Optional[QWidget] = None
```

---

## 関連ファイル一覧

| カテゴリ | ファイル |
|---------|---------|
| 新規テスト | `tests/test_hypothesis.py`, `tests/test_spacing_manager.py`, `tests/test_style_theme.py` |
| 修正済み | `ui/property_panel.py`, `windows/mixins/inline_editor_mixin.py` |
| 型修正 | `ui/tabs/image_tab.py`, `ui/controllers/image_actions.py`, `ui/main_window.py` |
| 設定更新 | `verify_all.bat`, `pyproject.toml` |

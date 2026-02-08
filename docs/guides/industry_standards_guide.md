# 業界標準ツール解説書

> **対象読者**: 初〜中級Pythonプログラマー
> **作成日**: 2026-02-08
> **観点**: Super Seniorスペシャリスト

---

## 📋 ツール一覧 (導入優先度順)

| ツール | カテゴリ | FTIV導入 | 優先度 |
|--------|---------|----------|--------|
| GitHub Actions | CI/CD | 🟡 可能 | ⭐⭐⭐⭐⭐ |
| mkdocs | ドキュメント | 🟡 可能 | ⭐⭐⭐⭐ |
| Playwright | E2Eテスト | 🔴 困難 | ⭐⭐ |
| mutmut | Mutation Testing | 🟢 容易 | ⭐⭐⭐ |
| Sphinx | ドキュメント | 🟡 可能 | ⭐⭐⭐ |

---

## 1. GitHub Actions (CI/CD)

### 1.1 これは何？

**継続的インテグレーション (CI)** と **継続的デリバリー (CD)** を自動化するGitHubの機能。

```
あなた: git push
  ↓
GitHub Actions: 自動でテスト実行
  ↓
結果: ✅ Pass → マージ可能 / ❌ Fail → マージ禁止
```

### 1.2 なぜ必要？

| 現状 | GitHub Actions導入後 |
|------|---------------------|
| ローカルで`verify_all.bat`を手動実行 | Push時に自動実行 |
| 「テスト忘れ」でバグ混入リスク | 強制チェックでリスクゼロ |
| Windows限定 | 複数OS (Linux/Mac/Windows) で検証 |

### 1.3 FTIVへの導入可能性

**🟢 可能 (推奨)**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup uv
        uses: astral-sh/setup-uv@v5
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest --maxfail=1
      - name: Type check
        run: uv run mypy .
```

### 1.4 導入コスト

| 項目 | 見積もり |
|------|---------|
| 作業時間 | 1-2時間 |
| 費用 | 無料 (公開リポジトリ) |
| 難易度 | ★★☆ 中程度 |

---

## 2. mkdocs (ドキュメントサイト)

### 2.1 これは何？

Markdownファイルから**美しいドキュメントサイト**を自動生成するツール。

```
docs/guides/*.md
  ↓ mkdocs build
https://ftiv-lab.github.io/FTIV/ (静的サイト)
```

### 2.2 なぜ必要？

| 現状 | mkdocs導入後 |
|------|-------------|
| MarkdownをGitHubで閲覧 | ブラウザで検索・ナビゲーション可能 |
| ファイル構造が複雑 | サイドバーで階層表示 |
| 見た目が地味 | テーマでプロフェッショナルな見た目 |

### 2.3 実例

- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Material for MkDocs**: https://squidfunk.github.io/mkdocs-material/

### 2.4 FTIVへの導入可能性

**🟢 可能**

```yaml
# mkdocs.yml
site_name: FTIV Documentation
theme:
  name: material
  palette:
    scheme: slate  # ダークテーマ
nav:
  - Home: index.md
  - Guides:
    - Agent Onboarding: guides/AGENT_READING_LIST.md
    - Phase 2 Guide: guides/phase2_test_quality_guide.md
  - Codebase:
    - Overview: codebase/00_codebase_survey_report.md
    - QA & Testing: codebase/09_qa_and_testing_details.md
```

### 2.5 導入コスト

| 項目 | 見積もり |
|------|---------|
| 作業時間 | 2-3時間 |
| 費用 | 無料 (GitHub Pages) |
| 難易度 | ★★☆ 中程度 |

---

## 3. Playwright (E2Eテスト)

### 3.1 これは何？

**ブラウザ自動操作**ツール。Webアプリのエンドツーエンド (E2E) テストに使用。

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    page.click("button#submit")
    assert page.title() == "Success"
```

### 3.2 なぜ必要？

| 用途 | 説明 |
|------|------|
| Webアプリテスト | ブラウザ操作を自動化 |
| スクリーンショット | 画面キャプチャで視覚的確認 |
| クロスブラウザ | Chrome, Firefox, Safari対応 |

### 3.3 FTIVへの導入可能性

**🔴 困難 (非推奨)**

| 理由 | 詳細 |
|------|------|
| FTIVはWebアプリではない | デスクトップアプリ (PySide6) |
| 代替手段あり | `PySide6.QtTest (QTest)` で十分 |
| 学習コスト高 | Webの知識が必要 |

**代わりに使うべき**: 現在使用中の `QTest` + `pytest-qt`

---

## 4. mutmut (Mutation Testing)

### 4.1 これは何？

**テストの品質**を検証するツール。コードに意図的なバグ(ミュータント)を埋め込み、テストが検出できるか確認。

```
元のコード: x = a + b
  ↓ mutmut がミュータント生成
ミュータント: x = a - b  ← わざとバグ
  ↓ テスト実行
結果: ❌ テスト失敗 → ミュータント「殺害」(良い)
     ✅ テスト成功 → ミュータント「生存」(悪い = テスト不足)
```

### 4.2 なぜ必要？

| 問題 | mutmutで解決 |
|------|-------------|
| カバレッジ100%でもバグ検出できない | ミュータント生存率で品質測定 |
| 「通るだけのテスト」が増える | 本当に意味のあるテストか検証 |

### 4.3 実例

```bash
# 実行
mutmut run --paths-to-mutate=managers/

# 結果
Legend:
🎉 = Killed (テストがバグを検出)
🐙 = Survived (テストがバグを見逃し ← 問題!)
```

### 4.4 FTIVへの導入可能性

**🟢 容易**

```bash
# インストール
uv add mutmut --dev

# 実行 (特定ディレクトリ)
mutmut run --paths-to-mutate=managers/spacing_manager.py

# HTML結果表示
mutmut html
```

### 4.5 導入コスト

| 項目 | 見積もり |
|------|---------|
| 作業時間 | 30分 |
| 費用 | 無料 |
| 難易度 | ★☆☆ 簡単 |

### 4.6 注意点

- **実行時間が長い** (テスト数 × ミュータント数)
- 日常的には使わず、リリース前チェックに使用

---

## 5. Sphinx (ドキュメント)

### 5.1 これは何？

Pythonコードの**docstringから自動でAPIドキュメント生成**。

```python
def calculate_spacing(value: float, mode: str) -> float:
    """Calculate spacing value.

    Args:
        value: The input value.
        mode: Either 'horizontal' or 'vertical'.

    Returns:
        Calculated spacing value.

    Raises:
        ValueError: If mode is invalid.
    """
```

↓ Sphinx

```
API Reference
└── calculate_spacing(value, mode)
    Calculate spacing value.
    
    Parameters:
        value (float) – The input value.
        mode (str) – Either 'horizontal' or 'vertical'.
    
    Returns:
        float – Calculated spacing value.
```

### 5.2 mkdocs vs Sphinx

| 項目 | mkdocs | Sphinx |
|------|--------|--------|
| 主用途 | 一般ドキュメント | APIリファレンス |
| 入力 | Markdown | reStructuredText (または Markdown) |
| 学習コスト | 低 | 中〜高 |
| FTIV向け | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 5.3 FTIVへの導入可能性

**🟡 可能 (ただしmkdocs推奨)**

FTIVは「教材」目的なので、コードのdocstringよりも概念説明が重要。
→ **mkdocsの方が適切**

---

## 📊 導入ロードマップ (推奨)

### Phase 3A: 基盤整備 (1-2時間)

```
[ ] GitHub Actions CI 導入
    └── Push時自動テスト
```

### Phase 3B: ドキュメント強化 (2-3時間)

```
[ ] mkdocs 導入
    └── GitHub Pagesでホスティング
```

### Phase 3C: テスト品質 (任意)

```
[ ] mutmut 導入
    └── リリース前のみ実行
```

---

## 📚 参考リンク

| ツール | 公式ドキュメント |
|--------|------------------|
| GitHub Actions | https://docs.github.com/en/actions |
| mkdocs | https://www.mkdocs.org/ |
| Material for MkDocs | https://squidfunk.github.io/mkdocs-material/ |
| mutmut | https://mutmut.readthedocs.io/ |
| Playwright | https://playwright.dev/python/ |
| Sphinx | https://www.sphinx-doc.org/ |

---

> [!TIP]
> **優先度**: GitHub Actions > mkdocs > mutmut
> 
> Playwrightは**Webアプリ用**なのでFTIVには不要です。

# Walkthrough: Spacing System Split (Vertical/Horizontal De-coupling)

縦書き・横書きの文字間隔・行間隔設定を完全に分離し、それぞれのモードで最適なレイアウト設定を独立して保存・適用できるようになりました。

## 概要

| 機能 | 以前の挙動 | 新しい挙動 |
| :--- | :--- | :--- |
| **文字間隔 (Char Spacing)** | 縦書きでも `horizontal_margin` が使われたり、混同があった | **縦 (`char_spacing_v`)** と **横 (`char_spacing_h`)** で完全に独立。 |
| **行間隔 (Line Spacing)** | 縦書きの列間隔と横書きの行間隔が `vertical_margin` で共有されていた | **縦 (`line_spacing_v`)** と **横 (`line_spacing_h`)** で完全に独立。 |
| **設定ダイアログ** | 共通の値が表示されていた | 現在のモード（縦/横）に応じた設定値が表示・編集される。 |

## 実装詳細

### 1. データモデルの拡張
`TextWindowConfig` に以下のプロパティを追加しました：
- `char_spacing_h`, `line_spacing_h` (横書き用)
- `char_spacing_v`, `line_spacing_v` (縦書き用)

既存の `horizontal_margin_ratio` 等は後方互換性のために維持されますが、内部ロジックは新プロパティを優先します。

### 2. レンダラ (`TextRenderer`) の刷新
描画ロジックを更新し、モードに応じて正しい間隔パラメータを使用するようにしました。
- **縦書き**: 文字送りは `char_spacing_v`、行送り（列間隔）は `line_spacing_v` を使用。
- **横書き**: 文字送りは `char_spacing_h`、行送りは `line_spacing_h` を使用。

### 3. UI (`TextSpacingDialog`)
ダイアログを更新し、縦書きモード時は「文字間隔 (縦)」「行間隔 (縦)」として縦書き専用の値を編集するように変更しました。

## バグ修正：横書き時の文字重ね問題 (Regression Check)

ユーザー報告により判明した「横書きモードで全ての文字が同じ位置に重なってしまう問題」を修正しました。
また、再発防止のために **High Resolution Testing**（描画位置の分散検証）を `test_spacing_split.py` に追加しました。

**検証ロジック:**
- Mock Painter を使用し、`drawText` (横書き) および `translate` (縦書き) の座標呼び出し順序を追跡。
- 文字ごとに行方向への座標移動が確実に発生していることを1文字単位で検証。

## 自動検証結果 (準拠: CONTRIBUTING.md)

`verify_all.bat`（プロジェクト標準検証スイート）による全テストをパスしました。
これには、新設した **`tests/test_interactive/test_spacing_split.py`** の以下の検証も含まれます：

1.  **Horizontal Logic**: 横書き設定を変更した際、Canvas の幅が適切に変化すること。
2.  **Vertical Logic**: 縦書き設定を変更した際、Canvas の高さ（文字間隔）または幅（行間隔）が変化すること。
3.  **Independence**: 横書き設定を極端に変更しても、縦書きモードのレイアウト計算結果が 1px も変化しないこと（完全分離）。

```batch
[1/6] Running Ruff Linter... (Passed)
[2/6] Running UI Reference Audit... (Passed)
[3/6] Running Tests: Group 1 (Core Logic)... (Passed)
[5/6] Running Tests: Group 3 (Interactive)... (Passed)
  tests/test_interactive/test_spacing_split.py ...
ALL CHECKS PASSED! READY FOR DEPLOY.

## リファクタリング：縦書きメトリクス適正化 (Vertical Metrics)

「文字間隔0でも縦書き文字が被る」問題を解決するため、描画ロジックを根本から修正しました。

*   **Before**: `y += font_size` (固定ピクセル送り)
    *   実際のフォント高さ(Ascent+Descent)より狭いため、必ず重なっていた。magic number での補正も散乱。
*   **After**: `y += fm.height()` (正しいフォントメトリクス送り)
    *   フォント自身が持つ「正しい高さ」を採用。
    *   句読点などのマジックナンバー (`0.75`等) を全廃し、`boundingRect` ベースの安全な実装へ移行。
*   **Verification**:
    *   `verify_all.bat` (All Green).
    *   `test_spacing_split.py` に `test_vertical_spacing_metrics` を追加。
    *   計算上のステップ幅が「フォントサイズ」ではなく「メトリクス高さ」以上であることを保証。

### リファインメント：行間削減とカットオフ修正 (Solid Height & Cutoff Fix)

さらに「縦書きの間隔が広すぎる」というフィードバックに基づき、ロジックを以下のように洗練させました。

*   **Spacing Logic**: `fm.height()` (Ascent + Descent + Leading) から `fm.ascent() + fm.descent()` へ変更。行間成分 (Leading) を除外し、引き締まったレイアウトを実現。
*   **Sizing Logic**: コンテナサイズ計算式をレンダリングロジックと完全に同期。これにより、文字数が増えても計算上の高さが不足せず、末尾が途切れる問題 (Cutoff) が解消されました。

### バグ修正：一文字目の上部切れ (First Char Cutoff)

一文字目の上部が枠からはみ出して切れていた問題を修正しました。
*   **Cause**: 配置計算において、グリフの実体サイズ（120px等）ではなく、小さなフォントサイズ（100px）の中心に合わせていたため、頭がはみ出していた。
*   **Fix**: `cy` (垂直中心) の計算にも `Ascent + Descent` (Solid Height) を使用し、正しい中心座標を算出するように修正。

### バグ修正：縦書きの左右窮屈・見切れ (Vertical Width Cutoff / Adaptive Column Width)

「薔薇」「鬱」などの幅広な漢字が左右で見切れる問題を修正しました。
*   **Cause**: 縦書きの列幅を `font_size` (1em) に固定していたため、1em を超える幅を持つ文字（Wide Glyphs）の両端が見切れていた。
*   **Fix**: テキスト内の最大文字幅 (`max_char_width`) を計測し、`max(font_size, max_char_width)` を列幅として採用する「Adaptive Column Width」ロジックを実装。

### リファインメント：影の描画改善 (Shadow Geometry Refinement)

影が「オフセット0でもズレる」「見切れる」という問題を修正しました。

1.  **オフセット0でのズレ解消 (Coordinate Lock)**
    *   **Cause**: ぼかしエフェクトが画像を拡張する際、座標系がズレてしまっていた。
    *   **Fix**: `source` と `target` の矩形を強制的に一致させることで、影が文字の真後ろに正確に描画されるように修正。

2.  **影の見切れ防止 (Bounding Box Expansion)**
    *   **Cause**: キャンバスサイズ計算に影の広がり（オフセットとぼかし半径）が含まれていなかった。
    *   **Fix**: `_calculate_shadow_padding` を実装し、影がどれだけ広がってもキャンバスが自動拡張されるように修正。

### バグ修正：縦書き影のズレ (Vertical Shadow Alignment / Layout Locking)

縦書き時に影のオフセットを(0,0)にしても、わずかにズレて表示される（ドリフト現象）問題を修正しました。

*   **Cause**: 影の描画時、サイズが同じでも「影用フォント」でレイアウト（文字配置・回転）を再計算していたため。フォントレンダリングの微細な誤差（ヒンティング等）が蓄積してズレが生じていました。
*   **Fix**: **Layout Locking** を実装。影や縁取りを描画する際、座標計算には強制的に「メインテキストのフォント」を使用し、塗り（描画）のみに「影フォント」を使用するように変更。これにより、数学的に完全に一致する座標に描画されることを保証しました。

### バグ修正：縦書きテキストの位置ズレ (Vertical Text Positioning / Double Compensation)

影のオフセットを設定すると、メインテキストがウィンドウ枠外に見切れてしまう問題を修正しました。

*   **Fix**:
    - [x] Implementation: Use `layout_font` for metrics calculation
    - [x] Implementation: Pass main font as anchor from `_draw_vertical_text_elements`

- [x] **Fix: Vertical Text Positioning (Double Compensation)** <!-- id: 82 -->
    - [x] Fix: Remove `shadow_x` from `curr_x` calculation*   **Fix**: `_draw_vertical_text_content` の描画開始位置計算から `shadow_x` の減算処理を削除しました。

### 改善：縦書き句読点の配置 (Vertical Punctuation Alignment)

縦書き時に「、」や「。」が文字枠のど真ん中に表示され、日本語として不自然な問題を修正しました。

*   **Cause**: 以前の修正でマジックナンバーを排除するため、すべての文字を一律「バウンディングボックス中心」で揃えていたため、約物の位置情報が失われていました。
*   **Fix**:
    *   **通常文字**: フォントの「Em-box（仮想ボディ）」を基準に配置するロジックに変更。
    *   **句読点（、。）**: フォント標準位置（左下）から、縦書き用（右上）への「象限マッピング（Quadrant Shift）」を実装。

### クリーンアップ：レガシー設定 (Type A/B) の削除

新しいTypographic Alignmentロジックの導入により不要となった旧式の「Type A (Monospace) / Type B (Proportional)」設定を完全に削除しました。

*   **Deleted**: `OffsetMode` enum, `offset_mode` property.
*   **UI**: テキストタブとコンテキストメニューから旧設定項目を削除。
*   **Codebase**: 関連する制御ロジックを削除し、コードベースをスリム化。

### Localization Cleanup
**Objective**: 不要となった翻訳キーの削除と、言語ファイルの整理。

*   **Cleanup**: `en.json` および `jp.json` から、Type A/B 関連の未使用キー（5項目）を削除しました。
    *   `menu_vertical_font_type`, `menu_mono_font`, `btn_vert_type_a`, etc.
*   **Fix**: テキストタブ (`text_tab.py`) に残っていた、削除済みキーを参照するコードを除去しました。

### Developer Experience (DX)
**Objective**: 「エラー原因の特定に時間がかかる」という課題の解決。

*   **Improvement**: `verify_all.bat` を改良。
    *   `--maxfail=1`: 最初のエラーで即停止（スクロールバック不要化）。
    *   `--showlocals`: エラー時の変数の中身を表示（デバッグ情報量アップ）。
*   **Docs**: `CONTRIBUTING.md` にトラブルシューティングガイドを追加。

### Modern Development Environment (Super Senior Stack)
**Objective**: 開発環境を業界標準の最新構成 ("Super Senior Stack") へアップグレード。

*   **UV Integration**: `pip` + `venv` を Rust製超高速ツール `uv` に移行。
    *   `pyproject.toml` ですべての依存関係を管理。
    *   `verify_all.bat` は `uv run` を使用し、環境設定の煩わしさを排除。
*   **Type Safety (Mypy)**: 静的型解析 `mypy` を導入。
    *   型定義のないコードを許容する設定からスタート（Baseline Green）。
    *   CI/Verification に組み込み済み。
*   **Automation (Pre-commit)**: `pre-commit` を導入。
    *   `git commit` 時に自動で `ruff` (Lint/Format) と `mypy` が実行されるようになりました。

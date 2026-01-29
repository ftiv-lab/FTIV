## 🤖 AI Agent: START HERE (Onboarding Guide)

FTIV (v1.0.0 Unified Release) プロジェクトへようこそ。
新しくタスクを開始する前に、以下のドキュメントを**この順番で**読み込み、プロジェクトの現在の「立ち位置」と「規約」を正確に把握してください。

---

## 🏗️ 1. プロジェクトの憲法 (Rules & Standards)
開発の前提となる技術スタックと、**絶対に守らなければならない**禁止事項です。

1.  **[CONTRIBUTING.md](file:///O:/Tkinter/FTIV/CONTRIBUTING.md)**: 
    *   **最重要**。全体の設計哲学、Dual Environment (3.14/3.13) 戦略、および `MainController` パターンについての理解。
2.  **[docs/RULES_AND_STANDARDS.md](file:///O:/Tkinter/FTIV/docs/RULES_AND_STANDARDS.md)**: 
    *   UIアクセス規約。`hasattr` による推測の禁止、明示的なオブジェクトパスによる Fail Fast 設計の徹底。

---

## 🗺️ 2. コード構造の把握 (Architecture Navigation)
FTIV の「脳」と「体」に相当する重要ファイルです。

1.  **[ui/controllers/main_controller.py](file:///O:/Tkinter/FTIV/ui/controllers/main_controller.py)**: 
    *   ビジネスロジックのハブ。ウィンドウの生成、破棄、Undo/Redo の統括管理。
2.  **[windows/base_window.py](file:///O:/Tkinter/FTIV/windows/base_window.py)**: 
    *   すべてのオーバーレイウィンドウ（Text/Image）の基底クラス。ドラッグ、リサイズ、アンカー、アニメーションの基礎がここにあります。
3.  **[windows/text_renderer.py](file:///O:/Tkinter/FTIV/windows/text_renderer.py)**: 
    *   テキスト描画のコアロジック。キャッシュ、グリフ生成、縦書き対応。
4.  **[models/window_config.py](file:///O:/Tkinter/FTIV/models/window_config.py)**: 
    *   Pydantic によるデータ永続化の真実。ここに定義されていないプロパティは保存されません。

---

## 🏛️ 3. 現在の戦略的ベースライン (Status & Roadmap)
「新機能」と「安定性」のバランスについて。

1.  **[docs/guides/git_guide.md](file:///O:/Tkinter/FTIV/docs/guides/git_guide.md)**: 
    *   **現在のセーブポイント v1.0.0** についての解説。完全統合版リリースの意義と過去の機能の取り扱い。
2.  **[docs/online_course_plan/00_master_plan.md](file:///O:/Tkinter/FTIV/docs/online_course_plan/00_master_plan.md)**: 
    *   今後の展望。このプロジェクトが単なるソフトではなく「教材」としての品質を求めている背景。

---

## 🛠️ 4. 品質保証 (Quality Gates)
変更を「コミット」する前に、必ず以下のチェックを通してください。

*   **[verify_all.bat](file:///O:/Tkinter/FTIV/verify_all.bat)**: 
    *   Ruff (Linter), UI Ref Check, Pytest を一括実行。
*   **[verify_debug.bat](file:///O:/Tkinter/FTIV/verify_debug.bat)**: 
    *   ハングアップやクラッシュ時の診断用。

---
> [!TIP]
> **「動けばいい」は失格です。**
> あなたは「Googleのシニアスタッフソフトウェアエンジニア」として振る舞ってください。美しく、テスト可能で、堅牢なコードを継承し、負債を残さないように。

*Maintained by Antigravity*

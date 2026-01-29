# Udemy講座企画: マスタープラン
**仮タイトル: "AI x Python: モダンデスクトップアプリ開発の教科書 - Antigravityと作るFTIV"**

## 1. 講座のゴール (Target Outcome)
受講者が、**「AIエージェント (Antigravity/Cursor等) を指揮して、実用的なGUIアプリケーションをゼロから設計・実装し、リリースできるエンジニア」** になること。

## 2. 統合カリキュラム構成 (The Curriculum)

各エキスパートの視点を統合し、以下の「ストーリー」で進行します。

### Phase 1: Awakening (AIとの出会いと環境構築)
*   **Module 1: 開発環境の準備**
    *   Python導入、Git導入、VSCode + Antigravity (or AI extensions) のセットアップ。
    *   "Hello World" をAIに書かせる（成功体験）。
*   **Module 2: プロジェクトの羅針盤**
    *   `.agent/RULES.md` の作成: AIへの「最初の指示」。
    *   `task.md` の作成: 進捗管理の重要性。

### Phase 2: Creation (アプリ開発の実践)
*   **Module 3: コア機能の実装 (MVP)**
    *   PySide6 の基礎と、AIによるボイラープレート生成。
    *   ウィンドウを透明にする (Overlay)。
    *   テキストを表示する (TextWindow)。
*   **Module 4: データと永続化**
    *   JSONによる設定保存。
    *   `SettingsManager` クラスの設計と実装（AIにクラス設計させる）。

### Phase 3: Discipline (品質と設計)
*   **Module 5: 壊れないコードのために**
    *   `ruff` (Limit) 導入。
    *   `verify_all.bat` の作成。
    *   **重要**: なぜテストが必要なのか？（AIは平気でバグを埋め込むから）。
*   **Module 6: アーキテクチャの洗練**
    *   Signal/Slot による疎結合化。
    *   「動けばいい」コードからの脱却。

### Phase 4: Pivot & Release (困難とリリース)
*   **Module 7: ケーススタディ "The MindMap Incident"**
    *   機能追加の失敗例（複雑化）。
    *   Gitブランチを使った「安全な撤退戦」。
    *   V1.0 リリースの決断。
*   **Module 8: 配布と未来**
    *   Nuitka によるEXE化。
    *   次のステップへの展望。

## 3. 教材として使用するFTIVのアセット
本講座では、実際のFTIVリポジトリの以下のファイルを「見本」として解説します。

*   **ルール**: `.agent/RULES_AND_STANDARDS.md`
*   **検証**: `verify_all.bat`
*   **設計**: `docs/refactoring_plans/*`
*   **Git**: `docs/git_guide.md`

## 4. 次のアクション
この構成案に基づき、まずは **Module 1-2 (環境構築とAIルールの策定)** のスライド構成や台本案を作成することをお勧めします。

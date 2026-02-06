# レガシー設定「Type A/B」の完全撤廃計画 (Legacy Settings Cleanup Plan)

## 診断結果 (Diagnosis)

現在の `TextRenderer`（特に `_render_vertical` と `_get_vertical_char_transform`）を分析した結果、**「Type A（等幅向け）」や「Type B（プロポーショナル向け）」といったモードによる分岐処理は完全に削除されている**ことが確認できました。

新しく実装された**「Typographic Alignment（Em-box基準配置＋自動列幅調整）」**は、フォントの種類（等幅かプロポーショナルか）に関わらず、フォント内部のメトリクス情報を使って常に最適な配置を行うユニバーサルなロジックです。

したがって、ユーザー様のご推察通り、これらの設定項目は**実質的に不要（Dead Code/UI）**となっており、削除することでアプリケーションをシンプル化できます。

## 撤廃手順 (Removal Steps)

以下の順序で削除・クリーンアップを行います。

### 1. データモデル (Models)
*   `O:/Tkinter/FTIV/models/enums.py`:
    *   `class OffsetMode` 定義を削除。
*   `O:/Tkinter/FTIV/models/window_config.py`:
    *   `TextWindowConfig` から `offset_mode` フィールドを削除。
    *   `from_dict` / `to_dict` での読み書き処理を削除（後方互換性のため `from_dict` で読み飛ばす処理は残しても良いが、完全に消してもデフォルト値で動くなら可）。

### 2. UIコンポーネント (User Interface)
*   **メインコントロールパネル (`MainWindow`)**:
    *   「縦書き設定」エリアにあるコンボボックスやラジオボタン（Type A / Type B 選択用）を削除。
*   **右クリックメニュー (`TextWindow`)**:
    *   コンテキストメニューから「縦書きモード切替」項目を削除。

### 3. コントローラー (Controllers)
*   `ui/controllers/text_actions.py`:
    *   `set_offset_mode` 等のアクションハンドラを削除。

### 4. テスト (Tests)
*   `tests/test_interactive/test_text_properties_comprehensive.py` 等:
    *   `offset_mode` の変更をテストしている箇所を削除。

## 期待される効果
*   **UIの整理**: 不要な項目が消え、ユーザーが迷う要素が減ります。
*   **コードの健全化**: 使われていないパラメータの運搬がなくなります。
*   **設定ファイルの軽量化**: 保存されるJSONから不要なキーが消えます。

この計画に基づき、一括削除を実行します。

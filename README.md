# FTIV (Free Text & Image Viewer)

**FTIV** は、コンテンツクリエイター、ストリーマー、パワーユーザー向けに設計された、高性能なオーバーレイ型テキスト＆画像ビューワーです。Python 3.14 と PySide6 で構築されています。

## 🚀 主な機能

*   **オーバーレイモード**: 背景透過ウィンドウとして、画面のあらゆる場所にテキストや画像を配置できます。
*   **ビジュアルコネクション**: テキストや画像同士をカスタマイズ可能な接続線でリンクできます (Shift+Drag)。
*   **高度なカスタマイズ**: ウィンドウごとにフォント、色、不透明度、アニメーションを調整可能。
*   **モダンUI**: 流れるようなアニメーションを備えた、洗練されたダークテーマインターフェース。
*   **ハイパフォーマンス**: リソース使用量を抑えた最適化設計。

## 🛠️ システム要件

*   **OS**: Windows 10/11 (64-bit)
*   **ランタイム**: Python 3.14.2 (開発推奨) / Python 3.13 (リリースビルドに必須)

## 📦 インストール (開発者向け)

1.  **リポジトリのクローン**
    ```powershell
    git clone https://github.com/Start-to-Finish/FTIV.git
    cd FTIV
    ```

2.  **仮想環境の作成 (Python 3.14)**
    ```powershell
    py -3.14 -m venv .venv314
    .venv314\Scripts\activate
    ```

3.  **依存関係のインストール**
    ```powershell
    pip install -r requirements.txt
    ```

4.  **アプリケーションの実行**
    ```powershell
    python main.py
    ```

## 🏗️ リリースビルドの作成 (EXE化)

**Nuitka** を使用してスタンドアロンの実行可能ファイルを作成します。
**注意:** Nuitka との互換性のため、ビルドには現在 **Python 3.13** が必要です。

1.  **ビルド環境のセットアップ (Python 3.13)**
    ```powershell
    py -3.13 -m venv .venv313
    .venv313\Scripts\pip install -r requirements.txt
    ```

2.  **ビルドスクリプトの実行**
    ```powershell
    & '.venv313\Scripts\python.exe' build_release.py
    ```

3.  **出力**
    実行ファイルは `dist/FTIV/` に生成されます。

## 🤝 コントリビューション

開発ガイドラインやコーディング規約については [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 📄 ライセンス

(Proprietary / Contact Author)

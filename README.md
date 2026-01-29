# FTIV (Floating Text Image Viewer)

**Floating Text & Image Viewer for Creators, Streamers, and Power Users.**
**クリエイター、ストリーマー、パワーユーザーのための、高性能オーバーレイビューワー。**

![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

---

## 📥 Download / ダウンロード

**[Get the latest version (v1.0.0) from Releases](https://github.com/Start-to-Finish/FTIV/releases)**

1.  Download `FTIV.zip`.
2.  Extract the zip file.
3.  Run `FTIV.exe`.

最新の `FTIV.zip` をダウンロード・解凍し、中の `FTIV.exe` を起動してください。

---

## ✨ Features / 主な機能

*   **Overlay Mode / オーバーレイモード**
    *   Place text and images anywhere on your screen with transparent backgrounds.
    *   画面のあらゆる場所に、背景透過でテキストや画像を配置できます。

*   **Visual Connections / ビジュアルコネクション**
    *   Link windows with customizable lines (Shift+Drag).
    *   Shift+ドラッグで、ウィンドウ同士を線で繋ぐことができます。

*   **High Customization / 高度なカスタマイズ**
    *   Adjust fonts, colors, opacity, and animations per window.
    *   ウィンドウごとにフォント、色、不透明度、アニメーションを細かく調整可能。

*   **Modern UI / モダンUI**
    *   Sleek dark theme with smooth animations.
    *   流れるようなアニメーションを備えた、洗練されたダークテーマ。

---

## 🛠️ System Requirements / 動作環境

*   **OS**: Windows 10 / 11 (64-bit)
*   **Runtime**: No installation required (Portable EXE) / インストール不要

---

## 👨‍� For Developers / 開発者向け情報

> **Note**: This project uses a Dual-Environment Strategy (Python 3.14 for Dev, Python 3.13 for Build).
> **注意**: このプロジェクトは開発用に Python 3.14、ビルド用に Python 3.13 を使用します。

### Setup

```bash
# 1. Clone
git clone https://github.com/Start-to-Finish/FTIV.git
cd FTIV

# 2. Setup Dev Env (Python 3.14)
py -3.14 -m venv .venv314
.venv314\Scripts\activate
pip install -r requirements.txt

# 3. Run
python main.py
```

### Build (Release)

```bash
# Requires Python 3.13 environment
& '.venv313\Scripts\python.exe' build_release.py
```

For detailed rules and contributing guide, please see [CONTRIBUTING.md](CONTRIBUTING.md).

---

(c) 2026 Antigravity (Start-to-Finish). All rights reserved.

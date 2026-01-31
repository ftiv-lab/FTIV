# FTIV (Floating Text Image Viewer)

**Floating Text & Image Viewer for Creators, Streamers, and Power Users.**
**クリエイター、ストリーマー、パワーユーザーのための、高性能オーバーレイビューワー。**

![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

---

## 📥 Download / ダウンロード

**[Get the latest version (v1.0.0) from Releases](https://github.com/ftiv-lab/FTIV/releases/latest)**

1.  Download `FTIV.zip`.
2.  Extract the zip file.
3.  Run `FTIV.exe`.

最新の `FTIV.zip` をダウンロード・解凍し、中の `FTIV.exe` を起動してください。

---

## 🚀 Why FTIV? / どんなソフト？

FTIV is not just a viewer; it's a **"High-End Desktop Workspace Tool"**.
Think of it as **"Sticky Notes on Steroids"** or an **"Infinite Canvas over your Desktop"**.

FTIVは、単なるビューワーではありません。**「デスクトップ付箋ソフトの究極進化形」** です。
画面全体を「透明なキャンバス」として使い、テキストや画像を自由自在に配置・接続・整理できます。

---

## ✨ Key Features / 強力な機能

### 1. 🎨 Ultimate Overlay Engine / 究極のオーバーレイ
*   **Total Freedom**: Place text, images, and GIFs anywhere on your screen.
    *   テキストも画像も、デスクトップの好きな場所に配置。
*   **Transparency Control**: Adjust opacity from 0% (invisible) to 100% (solid).
    *   ウィンドウの透明度を0%～100%まで自由に調整可能。作業の邪魔になりません。
*   **Always on Top**: Keep references visible while you work in other apps.
    *   常に最前面に表示し、資料を見ながらの作業や配信に最適です。

### 2. 📝 Rich Text & Vertical Writing / リッチテキスト＆縦書き
*   **Typography**: Customize fonts, sizes, colors, outlines, and shadows.
    *   フォント、色、縁取り（アウトライン）、影（シャドウ）など、Photoshopのようなリッチな文字装飾が可能。
*   **Vertical Support**: Full support for Tategaki (Vertical writing), perfect for Japanese content.
    *   **「縦書き」** に完全対応。小説の執筆や、和風な配信素材にも最適です。

### 3. 🎬 Dynamic Media Support / 動画・アニメーション
*   **Motion Graphics**: Supports **APNG** and **GIF** animations.
    *   静止画だけでなく、**APNG** や **GIF** アニメーションも再生可能。
*   **Custom Animations**: Create simple floating/fading animations for any text or image without video editing software.
    *   ソフト内で「ふわふわ浮く」「フェードイン・アウト」などの簡易アニメーションをテキストや画像に付与できます。

### 4. 🧠 Visual Thinking / 思考の可視化
*   **Connect the Dots**: Link items with customizable lines (Shift+Drag) to create mind maps or relationship charts directly on your desktop.
    *   Shift+ドラッグでウィンドウ同士を **「線」** で接続。デスクトップ上でそのままマインドマップや相関図を作れます。

### 5. ⚙️ Pro-Level Customization / プロ級のカスタマイズ
*   **Deep Control**: Every aspect (Window style, Border, Background) is tweakable via Property Panel or Right-click menu.
    *   右クリックメニューやプロパティパネルから、すべての要素（枠線、背景色、角丸など）を細かく設定可能。
*   **Preset System**: Save your favorite layouts and styles.
    *   お気に入りのスタイルや配置を保存・復元できます。

---

## 👥 Use Cases / こんな人にオススメ

*   **📺 For Streamers / 配信者の方へ**
    *   Show current song playing, comments, or discord images as overlays.
    *   Create dynamic "Now Loading" screens using GIFs and text.
    *   配信画面に「現在の曲名」や「コメント」、「立ち絵」を透過で配置。

*   **🎨 For Creators / クリエイターの方へ**
    *   Keep reference images floating while modeling in Blender or drawing in Photoshop.
    *   Build mood boards directly on your screen.
    *   BlenderやPhotoshopで作業中、参考資料（リファレンス）を常に横に置いておくのに最適。

*   **✒️ For Writers / 物書きの方へ**
    *   Keep plot notes or character names visible.
    *   Use "Vertical Text" for hauling traditional Japanese aesthetics.
    *   プロットやキャラ設定をデスクトップに貼り付け。縦書きで美しいメモを常駐。

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
git clone https://github.com/ftiv-lab/FTIV.git
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

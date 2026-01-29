# utils/docs.py

# ==========================================
# ユーザーマニュアル (日本語)
# ==========================================
MANUAL_TEXT_JP = """
<h1 align="center" style="color:#88ccff;">FTIV</h1>
<div align="center" style="font-size: 16px; font-weight: bold; color: #ccc;">
    Floating Text Image Viewer
</div>
<br>
<div align="center">Desktop Overlay Tool for Creators</div>
<hr>

<div style="background-color:#2a2a2a; padding:15px; border-radius:8px; border:1px solid #444;">
    <h3 style="margin-top:0;">目次</h3>
    <ul>
        <li><a href="#basic" style="color:#aaaaff; text-decoration:none;"><b>▼ 第1部：基本編 (Basic)</b></a>
            <ul>
                <li><a href="#basic_add" style="color:#ddd; text-decoration:none;">ウィンドウの追加・削除</a></li>
                <li><a href="#basic_ops" style="color:#ddd; text-decoration:none;">基本操作・見た目の変更</a></li>
                <li><a href="#basic_save" style="color:#ddd; text-decoration:none;">保存と読み込み</a></li>
            </ul>
        </li>
        <li><a href="#advanced" style="color:#aaaaff; text-decoration:none;"><b>▼ 第2部：応用・詳細編 (Advanced)</b></a>
            <ul>
                <li><a href="#anim" style="color:#ffcc88; text-decoration:none;"><b>アニメーション完全ガイド</b></a> (★重要)</li>
                <li><a href="#text_style" style="color:#ddd; text-decoration:none;">テキスト装飾の極意 (縁取り/グラデ)</a></li>
                <li><a href="#image_ops" style="color:#ddd; text-decoration:none;">画像の整列・一括操作</a></li>
                <li><a href="#connect" style="color:#ddd; text-decoration:none;">接続とグループ化</a></li>
                <li><a href="#perf" style="color:#ddd; text-decoration:none;">パフォーマンスチューニング</a></li>
                <li><a href="#shortcuts" style="color:#ff8888; text-decoration:none;">緊急ショートカット一覧</a></li>
            </ul>
        </li>
    </ul>
</div>

<br><br>

<!-- ========================================================= -->
<h2 id="basic" style="background-color:#004488; color:white; padding:5px;">第1部：基本編 (Basic)</h2>

<h3 id="basic_add">1. ウィンドウの追加・削除</h3>
<ul>
    <li><b>テキストの追加:</b> [テキスト] タブの <b>「+ テキストを追加」</b> ボタンを押します。</li>
    <li><b>画像の追加:</b> [画像] タブから追加するか、画像ファイルをウィンドウへ直接 <b>ドラッグ＆ドロップ</b> してください。</li>
    <li><b>削除:</b> ウィンドウを選択して <b>Deleteキー</b>、または右クリックメニューから削除できます。</li>
</ul>

<h3 id="basic_ops">2. 基本操作・見た目の変更</h3>
<ul>
    <li><b>移動:</b> 左クリックでドラッグ。</li>
    <li><b>サイズ変更:</b> <b>Ctrl + マウスホイール</b> で拡大縮小できます（フォントサイズ/画像スケール）。</li>
    <li><b>右クリックメニュー:</b> 色、フォント、反転などの詳細設定はここから行います。</li>
    <li><b>隠す/表示:</b> <b>Hキー</b> で一時的に隠し、<b>Fキー</b> で最前面表示を切り替えます。</li>
</ul>

<h3 id="basic_save">3. 保存と読み込み</h3>
<p>FTIVには2種類の保存形式があります。</p>
<table border="1" cellpadding="5" cellspacing="0" width="100%">
    <tr>
        <th bgcolor="#444">形式</th>
        <th bgcolor="#444">特徴・用途</th>
    </tr>
    <tr>
        <td><b>シーン (Scene)</b></td>
        <td>現在の画面状態（ウィンドウ配置・設定）を保存します。「雑談用」「ゲーム用」などの場面転換に使います。</td>
    </tr>
    <tr>
        <td><b>プロジェクト (Project)</b></td>
        <td>全てのシーン情報を含めて保存します。バックアップや環境移行用です。</td>
    </tr>
</table>
<p><i>※ [シーン] タブでカテゴリを作成し、その中にシーンを追加していくのが基本スタイルです。</i></p>

<br><br>

<!-- ========================================================= -->
<h2 id="advanced" style="background-color:#004488; color:white; padding:5px;">第2部：応用・詳細編 (Advanced)</h2>

<h3 id="anim" style="color:#ffcc88;">1. アニメーション完全ガイド</h3>
<p>[アニメーション] タブで、ウィンドウに動きをつけることができます。</p>

<h4>A. 相対移動 (Relative Move)</h4>
<p>「現在の位置」を基準に、ゆらゆら動かしたい時に使います。</p>
<ul>
    <li><b>設定方法:</b>
        <ol>
            <li>動かしたいウィンドウを選択し、「開始位置を記録」を押す（今の場所が基準になります）。</li>
            <li>ウィンドウを動かして、「終了位置を記録」を押す（移動量が計算されます）。</li>
            <li>「往復ループ」または「片道ループ」を押して再生。</li>
        </ol>
    </li>
    <li><b>往復 (Ping-pong):</b> 行って戻る動き。浮遊感の演出に。<br><code>(基準) &lt;--&gt; (基準+オフセット)</code></li>
    <li><b>片道 (One-way):</b> 端まで行ったら瞬時に戻る動き。背景の雲などに。<br><code>(基準) --&gt; (基準+オフセット) [瞬間移動] (基準) --&gt; ...</code></li>
</ul>

<h4>B. 絶対移動 (Absolute Move)</h4>
<p>「画面の決まった位置」を行き来させたい時に使います。</p>
<ul>
    <li><b>特徴:</b> 再生すると、ウィンドウがどこにあっても強制的に「開始位置」へワープしてから動き出します。</li>
    <li><b>用途:</b> ボタン一つで画面外からキャラをスライドインさせる、定位置を巡回させるなど。</li>
</ul>

<h4>C. イージング (Easing) の種類</h4>
<p>動きの「加速・減速」の味付けです。</p>
<ul>
    <li><b>Linear:</b> 等速。ロボットや機械的な動き、背景スクロールに。</li>
    <li><b>OutQuad / OutCubic:</b> 徐々に減速して止まる。自然で使いやすい標準的な動き。</li>
    <li><b>OutBack:</b> 行き過ぎてから戻る。「登場感」を出したい時に最適。</li>
    <li><b>OutBounce:</b> ボールが弾むように止まる。コミカルな演出に。</li>
    <li><b>Elastic:</b> ゴムで引っ張られたようにビヨンビヨンする。</li>
</ul>

<hr>

<h3 id="text_style">2. テキスト装飾の極意</h3>
<ul>
    <li><b>3重縁取り:</b> 内側から [白] [黒] [白] のように色を変え、太さを [5] [10] [15] と広げていくと、くっきりした「袋文字」が作れます。</li>
    <li><b>グラデーション:</b> 右クリックメニューから編集可能。ストップ（分岐点）を追加するにはバーをダブルクリックします。</li>
    <li><b>縦書きのフォント:</b>
        <ul>
            <li><b>Type A (等幅):</b> 記号や数字もきれいに縦に並びます。</li>
            <li><b>Type B (プロポーショナル):</b> 文字間が詰まります。英数字が横倒しになる場合があります。</li>
        </ul>
    </li>
</ul>

<h3 id="image_ops">3. 画像の整列・一括操作</h3>
<ul>
    <li><b>整列 (Arrange):</b> 複数の画像をグリッド状に並べます。配信のスタンプ一覧表示などに便利です。</li>
    <li><b>一括操作 (Bulk):</b> [画像] タブの「一括操作」グループを使うと、開いている全ての画像のサイズや透明度を一度に変更できます。</li>
</ul>

<h3 id="connect">4. 接続とグループ化</h3>
<ul>
    <li><b>接続 (Connector):</b> <b>Shift + クリック</b> でウィンドウ同士を線で繋ぎます。マインドマップや相関図に使えます。</li>
    <li><b>グループ化 (Group):</b> 右クリックメニューから「選択元を親として追従」を選ぶと、親ウィンドウを動かした時に子ウィンドウも一緒についてくるようになります。</li>
    <li><b>ラベル:</b> 接続線を右クリックすると、線の上に文字（ラベル）を追加できます。</li>
</ul>

<h3 id="perf">5. パフォーマンスチューニング</h3>
<p>[情報 (About)] タブで設定できます。動作が重い場合に調整してください。</p>
<ul>
    <li><b>描画デバウンス (Render Debounce):</b> 数値を上げると、サイズ変更時などの描画回数が減り、PC負荷が下がります（見た目の追従は少し遅れます）。</li>
    <li><b>グリフキャッシュ (Glyph Cache):</b> 文字の形状をメモリに保存する数です。テキストを大量に表示する場合は 1024 程度に上げるとスムーズになります。</li>
</ul>

<hr>

<h3 id="shortcuts" style="color:#ff8888;">6. 緊急ショートカット一覧</h3>
<p>操作不能になった場合（クリック透過したまま戻せない等）に使います。</p>
<ul>
    <li><b>Ctrl + Alt + Shift + R :</b> 全ウィンドウのクリック透過を強制解除 (Rescue)</li>
    <li><b>Ctrl + Alt + Shift + M :</b> 操作パネルを最前面に持ってくる (Main Window)</li>
    <li><b>Ctrl + Alt + Shift + H :</b> 全ウィンドウを表示状態にする (Show All)</li>
</ul>

<br><br><br>
"""

# ==========================================
# User Manual (English)
# ==========================================
MANUAL_TEXT_EN = """
<h1 align="center" style="color:#88ccff;">FTIV</h1>
<div align="center" style="font-size: 16px; font-weight: bold; color: #ccc;">
    Floating Text Image Viewer
</div>
<br>
<div align="center">Desktop Overlay Tool for Creators</div>
<hr>

<div style="background-color:#2a2a2a; padding:15px; border-radius:8px; border:1px solid #444;">
    <h3 style="margin-top:0;">Table of Contents</h3>
    <ul>
        <li><a href="#basic" style="color:#aaaaff; text-decoration:none;"><b>▼ Part 1: Basic (Getting Started)</b></a>
            <ul>
                <li><a href="#basic_add" style="color:#ddd; text-decoration:none;">Add & Remove Windows</a></li>
                <li><a href="#basic_ops" style="color:#ddd; text-decoration:none;">Basic Operations & Styles</a></li>
                <li><a href="#basic_save" style="color:#ddd; text-decoration:none;">Save & Load</a></li>
            </ul>
        </li>
        <li><a href="#advanced" style="color:#aaaaff; text-decoration:none;"><b>▼ Part 2: Advanced (Tips & Tricks)</b></a>
            <ul>
                <li><a href="#anim" style="color:#ffcc88; text-decoration:none;"><b>Animation Guide</b></a> (Important)</li>
                <li><a href="#text_style" style="color:#ddd; text-decoration:none;">Text Styles (Outline/Gradient)</a></li>
                <li><a href="#image_ops" style="color:#ddd; text-decoration:none;">Image Arrangement & Bulk Ops</a></li>
                <li><a href="#connect" style="color:#ddd; text-decoration:none;">Connectors & Grouping</a></li>
                <li><a href="#perf" style="color:#ddd; text-decoration:none;">Performance Tuning</a></li>
                <li><a href="#shortcuts" style="color:#ff8888; text-decoration:none;">Emergency Shortcuts</a></li>
            </ul>
        </li>
    </ul>
</div>

<br><br>

<!-- ========================================================= -->
<h2 id="basic" style="background-color:#004488; color:white; padding:5px;">Part 1: Basic (Getting Started)</h2>

<h3 id="basic_add">1. Add & Remove Windows</h3>
<ul>
    <li><b>Add Text:</b> Click the <b>"+"</b> button in the [Text] tab.</li>
    <li><b>Add Image:</b> Select a file from the [Image] tab or <b>Drag & Drop</b> an image directly onto a window.</li>
    <li><b>Remove:</b> Select a window and press <b>Delete</b>, or use the right-click menu.</li>
</ul>

<h3 id="basic_ops">2. Basic Operations & Styles</h3>
<ul>
    <li><b>Move:</b> Left-click and drag.</li>
    <li><b>Resize:</b> <b>Ctrl + Mouse Wheel</b> to resize font or image scale.</li>
    <li><b>Context Menu:</b> Right-click to access detailed settings like color, font, flip, etc.</li>
    <li><b>Hide/Front:</b> Press <b>H</b> to Hide temporarily. Press <b>F</b> to toggle Frontmost.</li>
</ul>

<h3 id="basic_save">3. Save & Load</h3>
<p>FTIV supports two save formats:</p>
<table border="1" cellpadding="5" cellspacing="0" width="100%">
    <tr>
        <th bgcolor="#444">Format</th>
        <th bgcolor="#444">Description</th>
    </tr>
    <tr>
        <td><b>Scene</b></td>
        <td>Saves the current screen state (windows, positions). Useful for scene transitions (e.g., "Chatting", "Gaming").</td>
    </tr>
    <tr>
        <td><b>Project</b></td>
        <td>Saves ALL scene data. Use this for backup or migration.</td>
    </tr>
</table>
<p><i>* Recommended workflow: Create categories in the [Scenes] tab and add scenes inside them.</i></p>

<br><br>

<!-- ========================================================= -->
<h2 id="advanced" style="background-color:#004488; color:white; padding:5px;">Part 2: Advanced (Tips & Tricks)</h2>

<h3 id="anim" style="color:#ffcc88;">1. Animation Guide</h3>
<p>You can animate windows via the [Animation] tab.</p>

<h4>A. Relative Move</h4>
<p>Moves relative to the "current position". Good for floating effects.</p>
<ul>
    <li><b>How to set:</b>
        <ol>
            <li>Select a window and click "Record Start Pos" (Current pos becomes base).</li>
            <li>Move the window and click "Record End Pos" (Calculates the offset).</li>
            <li>Click "Ping-pong" or "One-way" loop to play.</li>
        </ol>
    </li>
    <li><b>Ping-pong:</b> Back and forth. Floating effect.<br><code>(Base) &lt;--&gt; (Base + Offset)</code></li>
    <li><b>One-way:</b> Moves to end, then instantly snaps back. Flowing cloud effect.<br><code>(Base) --&gt; (Base + Offset) [Snap] (Base) --&gt; ...</code></li>
</ul>

<h4>B. Absolute Move</h4>
<p>Moves between fixed screen coordinates.</p>
<ul>
    <li><b>Feature:</b> When played, the window forces itself to the "Start" position regardless of where it is.</li>
    <li><b>Usage:</b> Slide-in character entry, patrol paths.</li>
</ul>

<h4>C. Easing Types</h4>
<p>Controls the acceleration/deceleration of motion.</p>
<ul>
    <li><b>Linear:</b> Constant speed. Robotic movement.</li>
    <li><b>OutQuad / OutCubic:</b> Slows down at the end. Natural and standard UI motion.</li>
    <li><b>OutBack:</b> Overshoots and comes back. Good for "Pop-in" effects.</li>
    <li><b>OutBounce:</b> Bounces like a ball. Comical effect.</li>
    <li><b>Elastic:</b> Rubber band effect.</li>
</ul>

<hr>

<h3 id="text_style">2. Text Styles (Outline/Gradient)</h3>
<ul>
    <li><b>Triple Outline:</b> Change outline colors (e.g., White -> Black -> White) and increase widths (e.g., 5 -> 10 -> 15) to create distinct text borders.</li>
    <li><b>Gradient:</b> Editable via right-click menu. Double-click the gradient bar to add stops.</li>
    <li><b>Vertical Text Fonts:</b>
        <ul>
            <li><b>Type A (Monospace):</b> Aligns symbols and numbers vertically.</li>
            <li><b>Type B (Proportional):</b> Tighter spacing. Some chars may rotate sideways.</li>
        </ul>
    </li>
</ul>

<h3 id="image_ops">3. Image Arrangement & Bulk Ops</h3>
<ul>
    <li><b>Arrange:</b> Align images in a grid. Useful for stamp collections.</li>
    <li><b>Bulk Ops:</b> Use the "Bulk Actions" group in [Image] tab to resize or change opacity for ALL images at once.</li>
</ul>

<h3 id="connect">4. Connectors & Grouping</h3>
<ul>
    <li><b>Connector:</b> <b>Shift + Click</b> another window to connect them with a line.</li>
    <li><b>Grouping:</b> Right-click -> "Set Selected as Parent" to group. Moving the parent moves the child.</li>
    <li><b>Label:</b> Right-click a connector line to add text (label) on it.</li>
</ul>

<h3 id="perf">5. Performance Tuning</h3>
<p>Configurable in the [About] tab. Adjust if the app feels heavy.</p>
<ul>
    <li><b>Render Debounce:</b> Increasing this reduces CPU load during resizing (visual updates will be slightly delayed).</li>
    <li><b>Glyph Cache:</b> Number of char shapes kept in memory. Increase to ~1024 for heavy text usage.</li>
</ul>

<hr>

<h3 id="shortcuts" style="color:#ff8888;">6. Emergency Shortcuts</h3>
<p>Use these if you lose control (e.g., Click-through enabled and can't click).</p>
<ul>
    <li><b>Ctrl + Alt + Shift + R :</b> Disable Click-Through for ALL windows (Rescue)</li>
    <li><b>Ctrl + Alt + Shift + M :</b> Bring Control Panel to Front</li>
    <li><b>Ctrl + Alt + Shift + H :</b> Show All Windows</li>
</ul>

<br><br><br>
"""

# ==========================================
# ライセンス条項 (License & Credits)
# ==========================================
# (ここは前回のままでOKですが、念のため再掲します)
LICENSE_TEXT = """
<h2>ソフトウェア利用規約 / Terms of Use</h2>

<p>本ソフトウェア（以下「本ソフト」）を使用する前に、以下の規約をお読みください。<br>
Please read the following terms before using this software.</p>

<h3>1. 権利の帰属 (Copyright)</h3>
<p>本ソフトの著作権は製作者に帰属します。<br>
The copyright of this software belongs to the author.</p>

<h3>2. 免責事項 (Disclaimer)</h3>
<p>本ソフトの使用によって生じた損害について、製作者は一切の責任を負いません。<br>
The author is not responsible for any damages caused by the use of this software.</p>

<h3>3. 禁止事項 (Prohibitions)</h3>
<ul>
    <li>本ソフトの無断での再配布・販売<br>Unauthorized redistribution or sale.</li>
    <li>リバースエンジニアリング、逆コンパイル、逆アセンブル<br>Reverse engineering, decompiling, or disassembling.</li>
    <li>公序良俗に反する目的での使用<br>Use for purposes contrary to public order and morals.</li>
</ul>

<p>Copyright (c) 2026 FTIV Project. All rights reserved.</p>

<hr>

<h2>第三者ソフトウェアのライセンス / Third Party Licenses</h2>
<p>本ソフトは、以下のオープンソースソフトウェアを含んでいるか、使用しています。<br>
This software includes or uses the following open source software.</p>

<h3>Qt & PySide6</h3>
<p>This software uses <b>Qt</b> and <b>PySide6</b> under the terms of the <b>LGPLv3</b> license.</p>
<p>Qt is a registered trademark of The Qt Company Ltd. and/or its subsidiaries.</p>
<ul>
    <li><a href="https://www.gnu.org/licenses/lgpl-3.0.html">GNU Lesser General Public License v3 (LGPLv3)</a></li>
    <li><a href="https://www.qt.io/">The Qt Company</a></li>
</ul>

<h3>Python</h3>
<p>This software includes <b>Python</b> software.</p>
<p>Copyright (c) 2001-2026 Python Software Foundation; All Rights Reserved.</p>
<ul>
    <li><a href="https://docs.python.org/3/license.html">Python Software Foundation License</a></li>
</ul>

<h3>Pillow (PIL Fork)</h3>
<p>Used for image processing.</p>
<p>Copyright (c) 2010-2026 Alex Clark and contributors.</p>
<ul>
    <li><a href="https://raw.githubusercontent.com/python-pillow/Pillow/main/LICENSE">HPND License</a></li>
</ul>

<h3>Nuitka</h3>
<p>This application is compiled using <b>Nuitka</b>.</p>
<p>Copyright (c) 2026 Kay Hayen.</p>
<ul>
    <li><a href="https://nuitka.net/">Nuitka Home Page</a></li>
    <li><a href="https://github.com/Nuitka/Nuitka/blob/main/LICENSE">Apache License 2.0</a></li>
</ul>
"""

# ==========================================
# バージョン情報 (About Dialog Content)
# ==========================================
ABOUT_TEXT_TEMPLATE = """
<div align="center">
    <h1 style="color:#88ccff; margin-bottom: 0;">FTIV</h1>
    <div style="font-size: 14px; font-weight: bold; color: #aaa; margin-bottom: 10px;">
        Floating Text Image Viewer
    </div>

    <p>Desktop Overlay Tool for Creators</p>


    <table border="0" cellpadding="5" cellspacing="0" style="margin-top: 10px; color: #ddd;">
        <tr>
            <td align="right" style="color:#888;">Version:</td>
            <td><b>{version}</b></td>
        </tr>
        <tr>
            <td align="right" style="color:#888;">Data Format:</td>
            <td>v{data_format}</td>
        </tr>
    </table>

    <hr style="margin: 15px 0;">

    <p style="font-size: 12px; color: #888;">
        Copyright © 2026 FTIV Project.<br>
        All rights reserved.
    </p>
</div>
"""

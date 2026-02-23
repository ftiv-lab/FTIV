# -*- coding: utf-8 -*-
"""SP5: ビルトインプリセット一括生成スクリプト.

json/presets/ に34個のプリセットJSONを生成する。
サムネイル生成は別途 StyleManager.generate_thumbnail() で行う。

使い方:
    uv run python scripts/generate_builtin_presets.py
"""

import json
import os
import sys

# プロジェクトルートをパスに追加
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PRESETS_DIR = os.path.join(PROJECT_ROOT, "json", "presets")


def _base(
    *,
    display_name: str,
    description: str,
    category: str,
    tags: list[str],
    font: str = "Yu Gothic UI",
    font_color: str = "#ffffff",
    font_size: int = 48,
    text_opacity: int = 100,
    # background
    background_visible: bool = False,
    background_color: str = "#000000",
    background_opacity: int = 100,
    background_corner_ratio: float = 0.2,
    background_outline_enabled: bool = False,
    background_outline_color: str = "#000000",
    background_outline_opacity: int = 100,
    background_outline_width_ratio: float = 0.05,
    # outline 1
    outline_enabled: bool = False,
    outline_color: str = "#000000",
    outline_opacity: int = 100,
    outline_width: float = 5.0,
    outline_blur: int = 0,
    # outline 2
    second_outline_enabled: bool = False,
    second_outline_color: str = "#ffffff",
    second_outline_opacity: int = 100,
    second_outline_width: float = 10.0,
    second_outline_blur: int = 0,
    # outline 3
    third_outline_enabled: bool = False,
    third_outline_color: str = "#000000",
    third_outline_opacity: int = 100,
    third_outline_width: float = 15.0,
    third_outline_blur: int = 0,
    # shadow
    shadow_enabled: bool = False,
    shadow_color: str = "#000000",
    shadow_opacity: int = 100,
    shadow_blur: int = 0,
    shadow_scale: float = 1.0,
    shadow_offset_x: float = 0.1,
    shadow_offset_y: float = 0.1,
    # text gradient
    text_gradient_enabled: bool = False,
    text_gradient: list | None = None,
    text_gradient_angle: int = 0,
    text_gradient_opacity: int = 100,
    # background gradient
    background_gradient_enabled: bool = False,
    background_gradient: list | None = None,
    background_gradient_angle: int = 0,
    background_gradient_opacity: int = 100,
    # vertical
    is_vertical: bool = False,
) -> dict:
    data: dict = {
        "_type": "ftiv_text_style",
        "_version": "1.1",
        "_display_name": display_name,
        "_description": description,
        "_category": category,
        "_tags": [t.lower() for t in tags],
        "_favorite": False,
        "_builtin": True,
        "_created": "2026-02-23",
        "_author": "ftiv",
        "font": font,
        "font_size": font_size,
        "font_color": font_color,
        "text_opacity": text_opacity,
        "is_vertical": is_vertical,
        "background_visible": background_visible,
        "background_color": background_color,
        "background_opacity": background_opacity,
        "background_corner_ratio": background_corner_ratio,
        "background_outline_enabled": background_outline_enabled,
        "background_outline_color": background_outline_color,
        "background_outline_opacity": background_outline_opacity,
        "background_outline_width_ratio": background_outline_width_ratio,
        "outline_enabled": outline_enabled,
        "outline_color": outline_color,
        "outline_opacity": outline_opacity,
        "outline_width": outline_width,
        "outline_blur": outline_blur,
        "second_outline_enabled": second_outline_enabled,
        "second_outline_color": second_outline_color,
        "second_outline_opacity": second_outline_opacity,
        "second_outline_width": second_outline_width,
        "second_outline_blur": second_outline_blur,
        "third_outline_enabled": third_outline_enabled,
        "third_outline_color": third_outline_color,
        "third_outline_opacity": third_outline_opacity,
        "third_outline_width": third_outline_width,
        "third_outline_blur": third_outline_blur,
        "shadow_enabled": shadow_enabled,
        "shadow_color": shadow_color,
        "shadow_opacity": shadow_opacity,
        "shadow_blur": shadow_blur,
        "shadow_scale": shadow_scale,
        "shadow_offset_x": shadow_offset_x,
        "shadow_offset_y": shadow_offset_y,
        "text_gradient_enabled": text_gradient_enabled,
        "text_gradient": text_gradient or [[0.0, "#000000"], [1.0, "#FFFFFF"]],
        "text_gradient_angle": text_gradient_angle,
        "text_gradient_opacity": text_gradient_opacity,
        "background_gradient_enabled": background_gradient_enabled,
        "background_gradient": background_gradient or [[0.0, "#000000"], [1.0, "#FFFFFF"]],
        "background_gradient_angle": background_gradient_angle,
        "background_gradient_opacity": background_gradient_opacity,
    }
    # background_visible はプリセット適用対象。
    # 非表示プリセットは opacity=0 も併用して、旧環境/視覚的一貫性を保つ。
    if not background_visible:
        data["background_opacity"] = 0
    return data


# ============================================================
# subtitle (4)
# ============================================================
PRESETS: dict[str, dict] = {}

PRESETS["sub_white_outline"] = _base(
    display_name="白字幕・黒縁",
    description="どんな背景でも読みやすい定番の白文字黒縁字幕",
    category="subtitle",
    tags=["字幕", "シンプル", "白", "縁取り"],
    font_color="#ffffff",
    outline_enabled=True,
    outline_color="#000000",
    outline_width=4.0,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=60,
    shadow_blur=3,
    shadow_offset_x=0.05,
    shadow_offset_y=0.05,
)

PRESETS["sub_bar_dark"] = _base(
    display_name="テロップバー・暗",
    description="半透明の暗い帯付きテロップ。ニュース・情報系に最適",
    category="subtitle",
    tags=["字幕", "テロップ", "バー", "ダーク"],
    font_color="#ffffff",
    background_visible=True,
    background_color="#1a1a2e",
    background_opacity=80,
    background_corner_ratio=0.0,
)

PRESETS["sub_yellow_variety"] = _base(
    display_name="バラエティ字幕・黄",
    description="テレビのバラエティ番組風。黄色文字に赤縁で目立つ",
    category="subtitle",
    tags=["字幕", "バラエティ", "黄色", "派手"],
    font_color="#ffee00",
    outline_enabled=True,
    outline_color="#cc0000",
    outline_width=5.0,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_width=8.0,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=80,
    shadow_blur=4,
    shadow_offset_x=0.08,
    shadow_offset_y=0.08,
)

PRESETS["sub_soft_pastel"] = _base(
    display_name="ソフト字幕・パステル",
    description="柔らかいパステル調の字幕。Vlogや落ち着いた動画向け",
    category="subtitle",
    tags=["字幕", "パステル", "ソフト", "やさしい"],
    font_color="#f5f0eb",
    text_opacity=95,
    outline_enabled=True,
    outline_color="#b8a9c9",
    outline_opacity=70,
    outline_width=3.0,
    outline_blur=2,
    shadow_enabled=True,
    shadow_color="#6b5b7b",
    shadow_opacity=40,
    shadow_blur=5,
    shadow_offset_x=0.03,
    shadow_offset_y=0.03,
)

# ============================================================
# title (3)
# ============================================================
PRESETS["ttl_impact_red"] = _base(
    display_name="インパクト赤",
    description="YouTubeサムネイルに最適。赤×白の高コントラストタイトル",
    category="title",
    tags=["タイトル", "赤", "インパクト", "サムネイル"],
    font_color="#ff1744",
    outline_enabled=True,
    outline_color="#ffffff",
    outline_width=6.0,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_width=10.0,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=90,
    shadow_blur=2,
    shadow_offset_x=0.1,
    shadow_offset_y=0.1,
)

PRESETS["ttl_gradient_blue"] = _base(
    display_name="グラデーションブルー",
    description="青のグラデーション文字。テック系・ビジネス動画のタイトルに",
    category="title",
    tags=["タイトル", "グラデーション", "青", "クール"],
    font_color="#4fc3f7",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#0288d1"], [0.5, "#4fc3f7"], [1.0, "#81d4fa"]],
    text_gradient_angle=180,
    outline_enabled=True,
    outline_color="#01579b",
    outline_opacity=90,
    outline_width=4.0,
    shadow_enabled=True,
    shadow_color="#002171",
    shadow_opacity=70,
    shadow_blur=6,
    shadow_offset_x=0.06,
    shadow_offset_y=0.08,
)

PRESETS["ttl_cinematic_gold"] = _base(
    display_name="シネマティック金",
    description="映画タイトル風の金色文字。豪華で格調高い印象",
    category="title",
    tags=["タイトル", "金", "シネマ", "豪華", "グラデーション"],
    font_color="#ffd54f",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#ff8f00"], [0.3, "#ffd54f"], [0.6, "#ffecb3"], [1.0, "#ff8f00"]],
    text_gradient_angle=180,
    outline_enabled=True,
    outline_color="#4e342e",
    outline_opacity=90,
    outline_width=3.0,
    shadow_enabled=True,
    shadow_color="#1a0e00",
    shadow_opacity=80,
    shadow_blur=8,
    shadow_offset_x=0.05,
    shadow_offset_y=0.1,
)

# ============================================================
# game (4)
# ============================================================
PRESETS["game_fire"] = _base(
    display_name="炎属性テキスト",
    description="炎の色彩でゲーム実況の攻撃シーンを演出",
    category="game",
    tags=["ゲーム", "炎", "赤", "グラデーション", "ファンタジー"],
    font_color="#ffab00",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#ff1744"], [0.4, "#ff6d00"], [0.7, "#ffab00"], [1.0, "#ffd740"]],
    text_gradient_angle=180,
    outline_enabled=True,
    outline_color="#b71c1c",
    outline_width=5.0,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_width=8.0,
    shadow_enabled=True,
    shadow_color="#ff6d00",
    shadow_opacity=50,
    shadow_blur=10,
    shadow_offset_x=0.0,
    shadow_offset_y=0.0,
)

PRESETS["game_ice"] = _base(
    display_name="氷属性テキスト",
    description="氷の色彩で冷たさと透明感を表現",
    category="game",
    tags=["ゲーム", "氷", "青", "グラデーション", "ファンタジー"],
    font_color="#e0f7fa",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#4dd0e1"], [0.5, "#e0f7fa"], [1.0, "#80deea"]],
    text_gradient_angle=180,
    outline_enabled=True,
    outline_color="#006064",
    outline_width=4.0,
    outline_blur=1,
    second_outline_enabled=True,
    second_outline_color="#00293b",
    second_outline_opacity=90,
    second_outline_width=7.0,
    shadow_enabled=True,
    shadow_color="#4dd0e1",
    shadow_opacity=40,
    shadow_blur=8,
    shadow_offset_x=0.0,
    shadow_offset_y=0.0,
)

PRESETS["game_poison"] = _base(
    display_name="毒属性テキスト",
    description="毒々しい紫と緑のダークファンタジー風テキスト",
    category="game",
    tags=["ゲーム", "毒", "紫", "ダーク", "ファンタジー"],
    font_color="#ce93d8",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#7b1fa2"], [0.5, "#ce93d8"], [1.0, "#69f0ae"]],
    text_gradient_angle=200,
    outline_enabled=True,
    outline_color="#1b0033",
    outline_width=5.0,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_width=8.0,
    shadow_enabled=True,
    shadow_color="#69f0ae",
    shadow_opacity=30,
    shadow_blur=12,
    shadow_offset_x=0.0,
    shadow_offset_y=0.0,
)

PRESETS["game_rpg_ui"] = _base(
    display_name="RPG風UIテキスト",
    description="RPGのメニュー画面をイメージしたUIスタイルテキスト",
    category="game",
    tags=["ゲーム", "rpg", "ui", "枠", "ダーク"],
    font_color="#e0e0e0",
    outline_enabled=True,
    outline_color="#455a64",
    outline_opacity=80,
    outline_width=2.0,
    background_visible=True,
    background_color="#1a237e",
    background_opacity=85,
    background_corner_ratio=0.15,
    background_outline_enabled=True,
    background_outline_color="#7986cb",
    background_outline_opacity=90,
    background_outline_width_ratio=0.04,
)

# ============================================================
# neon (3)
# ============================================================
PRESETS["neon_cyan"] = _base(
    display_name="サイバーシアン",
    description="サイバーパンク風の青白い発光テキスト。暗い背景で映える",
    category="neon",
    tags=["ネオン", "シアン", "発光", "サイバー", "glow"],
    font_color="#e0f7fa",
    outline_enabled=True,
    outline_color="#00e5ff",
    outline_width=3.0,
    outline_blur=6,
    second_outline_enabled=True,
    second_outline_color="#00b8d4",
    second_outline_opacity=60,
    second_outline_width=8.0,
    second_outline_blur=10,
    shadow_enabled=True,
    shadow_color="#00e5ff",
    shadow_opacity=50,
    shadow_blur=15,
    shadow_offset_x=0.0,
    shadow_offset_y=0.0,
)

PRESETS["neon_magenta"] = _base(
    display_name="ネオンマゼンタ",
    description="華やかなピンクのネオン発光。パーティ・音楽系に",
    category="neon",
    tags=["ネオン", "ピンク", "発光", "華やか", "glow"],
    font_color="#fce4ec",
    outline_enabled=True,
    outline_color="#ff4081",
    outline_width=3.0,
    outline_blur=5,
    second_outline_enabled=True,
    second_outline_color="#f50057",
    second_outline_opacity=50,
    second_outline_width=8.0,
    second_outline_blur=10,
    shadow_enabled=True,
    shadow_color="#ff4081",
    shadow_opacity=45,
    shadow_blur=14,
    shadow_offset_x=0.0,
    shadow_offset_y=0.0,
)

PRESETS["neon_green_matrix"] = _base(
    display_name="マトリックスグリーン",
    description="映画マトリックス風の緑色ネオン。テック・ハッカー系に",
    category="neon",
    tags=["ネオン", "緑", "発光", "マトリックス", "テック", "glow"],
    font_color="#c8e6c9",
    outline_enabled=True,
    outline_color="#00e676",
    outline_width=2.5,
    outline_blur=5,
    second_outline_enabled=True,
    second_outline_color="#00c853",
    second_outline_opacity=50,
    second_outline_width=7.0,
    second_outline_blur=10,
    shadow_enabled=True,
    shadow_color="#00e676",
    shadow_opacity=40,
    shadow_blur=12,
    shadow_offset_x=0.0,
    shadow_offset_y=0.0,
)

# ============================================================
# elegant (3)
# ============================================================
PRESETS["elg_gold_gradient"] = _base(
    display_name="ゴールドエレガント",
    description="上品な金色グラデーション。フォーマルな場面向け",
    category="elegant",
    tags=["エレガント", "金", "グラデーション", "高級", "フォーマル"],
    font_color="#ffd54f",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#bf8f00"], [0.3, "#ffd54f"], [0.7, "#fff8e1"], [1.0, "#bf8f00"]],
    text_gradient_angle=180,
    outline_enabled=True,
    outline_color="#5d4037",
    outline_opacity=80,
    outline_width=2.0,
    shadow_enabled=True,
    shadow_color="#3e2723",
    shadow_opacity=60,
    shadow_blur=6,
    shadow_offset_x=0.04,
    shadow_offset_y=0.06,
)

PRESETS["elg_silver_minimal"] = _base(
    display_name="シルバーミニマル",
    description="銀色の控えめなスタイル。洗練されたミニマルデザイン",
    category="elegant",
    tags=["エレガント", "銀", "ミニマル", "シンプル", "クール"],
    font_color="#eceff1",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#90a4ae"], [0.5, "#eceff1"], [1.0, "#b0bec5"]],
    text_gradient_angle=180,
    outline_enabled=True,
    outline_color="#37474f",
    outline_opacity=60,
    outline_width=1.5,
    shadow_enabled=True,
    shadow_color="#263238",
    shadow_opacity=40,
    shadow_blur=4,
    shadow_offset_x=0.03,
    shadow_offset_y=0.04,
)

PRESETS["elg_wine_dark"] = _base(
    display_name="ワインダーク",
    description="深みのあるワインレッド。大人っぽい落ち着いた雰囲気",
    category="elegant",
    tags=["エレガント", "赤", "ダーク", "大人", "シック"],
    font_color="#ffcdd2",
    outline_enabled=True,
    outline_color="#880e4f",
    outline_opacity=90,
    outline_width=3.0,
    shadow_enabled=True,
    shadow_color="#311b1b",
    shadow_opacity=70,
    shadow_blur=5,
    shadow_offset_x=0.04,
    shadow_offset_y=0.06,
    background_visible=True,
    background_color="#2c0a1a",
    background_opacity=75,
    background_corner_ratio=0.1,
)

# ============================================================
# card (3)
# ============================================================
PRESETS["card_dark_info"] = _base(
    display_name="ダーク情報カード",
    description="暗い背景に白文字の情報カード。データ表示や解説に",
    category="card",
    tags=["カード", "ダーク", "情報", "背景", "シンプル"],
    font_color="#e0e0e0",
    background_visible=True,
    background_color="#212121",
    background_opacity=90,
    background_corner_ratio=0.15,
    background_outline_enabled=True,
    background_outline_color="#616161",
    background_outline_opacity=60,
    background_outline_width_ratio=0.03,
)

PRESETS["card_light_note"] = _base(
    display_name="ライトノートカード",
    description="明るいメモ風のカード。注釈や補足説明をシンプルに表示",
    category="card",
    tags=["カード", "ライト", "メモ", "背景", "やさしい"],
    font_color="#37474f",
    background_visible=True,
    background_color="#fff9c4",
    background_opacity=92,
    background_corner_ratio=0.12,
    background_outline_enabled=True,
    background_outline_color="#f9a825",
    background_outline_opacity=50,
    background_outline_width_ratio=0.03,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=20,
    shadow_blur=6,
    shadow_offset_x=0.04,
    shadow_offset_y=0.04,
)

PRESETS["card_glass_blur"] = _base(
    display_name="グラスカード",
    description="すりガラス風の半透明カード。モダンで洗練された印象",
    category="card",
    tags=["カード", "グラス", "半透明", "モダン", "背景"],
    font_color="#ffffff",
    background_visible=True,
    background_color="#455a64",
    background_opacity=55,
    background_corner_ratio=0.2,
    background_outline_enabled=True,
    background_outline_color="#ffffff",
    background_outline_opacity=25,
    background_outline_width_ratio=0.02,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=30,
    shadow_blur=8,
    shadow_offset_x=0.0,
    shadow_offset_y=0.04,
)

# ============================================================
# pop (4)
# ============================================================
PRESETS["pop_rainbow_bright"] = _base(
    display_name="レインボーブライト",
    description="カラフルなレインボーグラデーション。SNSや楽しい動画に",
    category="pop",
    tags=["ポップ", "レインボー", "カラフル", "グラデーション", "明るい"],
    font_color="#ffffff",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#ff1744"], [0.25, "#ffea00"], [0.5, "#00e676"], [0.75, "#2979ff"], [1.0, "#d500f9"]],
    text_gradient_angle=0,
    outline_enabled=True,
    outline_color="#ffffff",
    outline_width=4.0,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_opacity=80,
    second_outline_width=7.0,
)

PRESETS["pop_pink_cute"] = _base(
    display_name="キュートピンク",
    description="かわいいピンクの文字。美容・ファッション系にぴったり",
    category="pop",
    tags=["ポップ", "ピンク", "かわいい", "女性向け"],
    font_color="#f8bbd0",
    outline_enabled=True,
    outline_color="#e91e63",
    outline_width=4.0,
    second_outline_enabled=True,
    second_outline_color="#ffffff",
    second_outline_width=7.0,
    shadow_enabled=True,
    shadow_color="#ad1457",
    shadow_opacity=40,
    shadow_blur=5,
    shadow_offset_x=0.04,
    shadow_offset_y=0.04,
)

PRESETS["pop_comic_yellow"] = _base(
    display_name="コミック吹き出し・黄",
    description="黄色背景の吹き出し風。リアクションや感想テキストに",
    category="pop",
    tags=["ポップ", "黄色", "吹き出し", "コミック", "背景"],
    font_color="#d84315",
    outline_enabled=True,
    outline_color="#000000",
    outline_width=3.0,
    background_visible=True,
    background_color="#fff176",
    background_opacity=95,
    background_corner_ratio=0.25,
    background_outline_enabled=True,
    background_outline_color="#000000",
    background_outline_opacity=100,
    background_outline_width_ratio=0.05,
)

PRESETS["pop_neon_party"] = _base(
    display_name="ネオンパーティ",
    description="派手なネオンカラーのパーティスタイル。イベント告知に",
    category="pop",
    tags=["ポップ", "ネオン", "パーティ", "派手", "カラフル"],
    font_color="#ffffff",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#ff4081"], [0.5, "#7c4dff"], [1.0, "#00e5ff"]],
    text_gradient_angle=0,
    outline_enabled=True,
    outline_color="#000000",
    outline_width=5.0,
    shadow_enabled=True,
    shadow_color="#7c4dff",
    shadow_opacity=50,
    shadow_blur=10,
    shadow_offset_x=0.0,
    shadow_offset_y=0.0,
)

# ============================================================
# japanese (3)
# ============================================================
PRESETS["jp_sumi_ink"] = _base(
    display_name="墨文字",
    description="墨色の落ち着いた文字。和風動画のナレーションに",
    category="japanese",
    tags=["和風", "墨", "シンプル", "落ち着き", "伝統"],
    font_color="#212121",
    outline_enabled=True,
    outline_color="#4e342e",
    outline_opacity=40,
    outline_width=2.0,
    outline_blur=1,
    shadow_enabled=True,
    shadow_color="#3e2723",
    shadow_opacity=30,
    shadow_blur=4,
    shadow_offset_x=0.03,
    shadow_offset_y=0.05,
)

PRESETS["jp_vermilion_gold"] = _base(
    display_name="朱金テキスト",
    description="朱色と金のグラデーション。祝い事や祭り系コンテンツに",
    category="japanese",
    tags=["和風", "朱色", "金", "グラデーション", "祝い", "華やか"],
    font_color="#ffd54f",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#d84315"], [0.4, "#ff8f00"], [0.7, "#ffd54f"], [1.0, "#d84315"]],
    text_gradient_angle=180,
    outline_enabled=True,
    outline_color="#4e342e",
    outline_width=4.0,
    second_outline_enabled=True,
    second_outline_color="#1a0e00",
    second_outline_opacity=80,
    second_outline_width=7.0,
    shadow_enabled=True,
    shadow_color="#1a0e00",
    shadow_opacity=60,
    shadow_blur=4,
    shadow_offset_x=0.05,
    shadow_offset_y=0.05,
)

PRESETS["jp_indigo_card"] = _base(
    display_name="藍染カード",
    description="藍色背景の和風カード。日本文化の解説テキストに最適",
    category="japanese",
    tags=["和風", "藍", "カード", "背景", "落ち着き"],
    font_color="#e8eaf6",
    background_visible=True,
    background_color="#1a237e",
    background_opacity=85,
    background_corner_ratio=0.08,
    background_outline_enabled=True,
    background_outline_color="#7986cb",
    background_outline_opacity=60,
    background_outline_width_ratio=0.03,
)

# ============================================================
# comic (4)
# ============================================================
PRESETS["comic_shout_red"] = _base(
    display_name="叫びセリフ・赤",
    description="漫画の叫び声風テキスト。衝撃的なリアクションの演出に",
    category="comic",
    tags=["漫画", "叫び", "赤", "太字", "インパクト"],
    font_color="#ffffff",
    outline_enabled=True,
    outline_color="#d50000",
    outline_width=6.0,
    second_outline_enabled=True,
    second_outline_color="#ffeb3b",
    second_outline_width=10.0,
    third_outline_enabled=True,
    third_outline_color="#000000",
    third_outline_width=14.0,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=80,
    shadow_blur=2,
    shadow_offset_x=0.1,
    shadow_offset_y=0.1,
)

PRESETS["comic_speech_bubble"] = _base(
    display_name="セリフ吹き出し",
    description="漫画の通常セリフ風。白い背景に黒文字のクラシックスタイル",
    category="comic",
    tags=["漫画", "セリフ", "吹き出し", "白黒", "シンプル"],
    font_color="#212121",
    background_visible=True,
    background_color="#ffffff",
    background_opacity=95,
    background_corner_ratio=0.3,
    background_outline_enabled=True,
    background_outline_color="#000000",
    background_outline_opacity=100,
    background_outline_width_ratio=0.05,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=25,
    shadow_blur=4,
    shadow_offset_x=0.04,
    shadow_offset_y=0.04,
)

PRESETS["comic_speed_lines"] = _base(
    display_name="スピード感テキスト",
    description="スピード線風のグラデーションで動きと勢いを表現",
    category="comic",
    tags=["漫画", "スピード", "グラデーション", "動き", "青"],
    font_color="#e3f2fd",
    text_gradient_enabled=True,
    text_gradient=[[0.0, "#0d47a1"], [0.3, "#42a5f5"], [0.6, "#e3f2fd"], [1.0, "#0d47a1"]],
    text_gradient_angle=45,
    outline_enabled=True,
    outline_color="#0d47a1",
    outline_width=5.0,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_opacity=90,
    second_outline_width=8.0,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=70,
    shadow_blur=3,
    shadow_offset_x=0.12,
    shadow_offset_y=0.04,
)

PRESETS["comic_horror_drip"] = _base(
    display_name="ホラーテキスト",
    description="不気味な赤と黒のホラー風テキスト。怪談やオカルト系に",
    category="comic",
    tags=["漫画", "ホラー", "赤", "ダーク", "不気味"],
    font_color="#ef5350",
    outline_enabled=True,
    outline_color="#b71c1c",
    outline_width=3.0,
    outline_blur=2,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_width=6.0,
    shadow_enabled=True,
    shadow_color="#d50000",
    shadow_opacity=40,
    shadow_blur=12,
    shadow_offset_x=0.0,
    shadow_offset_y=0.08,
)

# ============================================================
# other (3)
# ============================================================
PRESETS["other_simple_outline"] = _base(
    display_name="シンプル袋文字",
    description="最も基本的な白文字＋黒縁取り。どんな場面にも合う汎用スタイル",
    category="other",
    tags=["袋文字", "シンプル", "白", "黒", "汎用"],
    font_color="#ffffff",
    outline_enabled=True,
    outline_color="#000000",
    outline_width=5.0,
)

PRESETS["other_double_outline"] = _base(
    display_name="二重袋文字",
    description="白→赤→黒の二重縁取り。視認性の高い定番スタイル",
    category="other",
    tags=["袋文字", "二重", "縁取り", "赤", "汎用"],
    font_color="#ffffff",
    outline_enabled=True,
    outline_color="#d50000",
    outline_width=4.0,
    second_outline_enabled=True,
    second_outline_color="#000000",
    second_outline_width=8.0,
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=60,
    shadow_blur=3,
    shadow_offset_x=0.06,
    shadow_offset_y=0.06,
)

PRESETS["other_shadow_only"] = _base(
    display_name="影のみテキスト",
    description="縁取りなしでドロップシャドウのみ。自然で控えめな立体感",
    category="other",
    tags=["影", "シンプル", "ナチュラル", "控えめ", "汎用"],
    font_color="#ffffff",
    shadow_enabled=True,
    shadow_color="#000000",
    shadow_opacity=80,
    shadow_blur=6,
    shadow_offset_x=0.08,
    shadow_offset_y=0.1,
)


def main() -> None:
    os.makedirs(PRESETS_DIR, exist_ok=True)

    for filename, data in PRESETS.items():
        path = os.path.join(PRESETS_DIR, f"{filename}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Generated {len(PRESETS)} preset JSON files in {PRESETS_DIR}")

    # カテゴリ別カウント
    cats: dict[str, int] = {}
    for data in PRESETS.values():
        cat = data["_category"]
        cats[cat] = cats.get(cat, 0) + 1
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()

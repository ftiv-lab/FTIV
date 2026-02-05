# windows/text_renderer.py

import json
import logging
import math
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsBlurEffect, QGraphicsPixmapItem, QGraphicsScene

from models.enums import OffsetMode

logger = logging.getLogger(__name__)


@dataclass
class _RenderProfile:
    """1回の render 中の計測結果を保持する。"""

    parts_ms: dict[str, float] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, name: str, dt_ms: float) -> None:
        self.parts_ms[name] = float(self.parts_ms.get(name, 0.0)) + float(dt_ms)

    def inc(self, name: str, n: int = 1) -> None:
        self.counts[name] = int(self.counts.get(name, 0)) + int(n)


class TextRenderer:
    """TextWindowの描画ロジックを担当するクラス。

    ウィンドウの属性に基づき、テキスト、背景、影、縁取りを合成したQPixmapを生成します。
    """

    def __init__(self, blur_cache_size: int = 32) -> None:
        """TextRenderer を初期化する。

        Args:
            blur_cache_size (int): ぼかし結果のLRUキャッシュ上限数。
        """
        self._blur_cache_size: int = max(0, int(blur_cache_size))
        self._blur_cache: "OrderedDict[tuple[int, int, int, int], QPixmap]" = OrderedDict()
        self._render_cache_size: int = 32
        self._render_cache: "OrderedDict[str, QPixmap]" = OrderedDict()
        # --- profiling (debug) ---
        self._profile_enabled: bool = False
        self._profile_warn_ms: float = 16.0
        self._profile_last_log_ts: float = 0.0
        self._profile_log_cooldown_s: float = 0.2

        # 1回のrender中だけ使う（ネスト計測用）
        self._active_profile: Optional[_RenderProfile] = None

        # --- glyph path cache (LRU) ---
        # addText(QPainterPath) が高コストなので、(font, char) 単位で再利用する
        self._glyph_cache_size: int = 512
        self._glyph_cache: "OrderedDict[tuple[str, int, str], QPainterPath]" = OrderedDict()

    def set_profiling(self, enabled: bool, warn_ms: float = 16.0) -> None:
        """TextRenderer の簡易プロファイルをON/OFFする。

        Args:
            enabled (bool): Trueで計測ログを有効化。
            warn_ms (float): 合計がこのmsを超えたらログ出力対象にする。
        """
        self._profile_enabled = bool(enabled)
        try:
            self._profile_warn_ms = float(warn_ms)
        except Exception:
            self._profile_warn_ms = 16.0

    def _prof_add(self, name: str, dt_ms: float) -> None:
        """現在の render 計測に加算する（有効時のみ）。"""
        p = self._active_profile
        if p is None:
            return
        try:
            p.add(name, float(dt_ms))
        except Exception as e:
            logger.debug(f"Profile add error: {e}")

    def _prof_inc(self, name: str, n: int = 1) -> None:
        """現在の render 計測の回数を加算する（有効時のみ）。"""
        p = self._active_profile
        if p is None:
            return
        try:
            p.inc(name, int(n))
        except Exception as e:
            logger.debug(f"Profile inc error: {e}")

    def render(self, window: Any) -> QPixmap:
        """ウィンドウの状態を読み取り、描画結果を生成します（分解プロファイル対応）。"""
        profiling: bool = bool(getattr(self, "_profile_enabled", False))

        if not profiling:
            if window.is_vertical:
                return self._render_vertical(window)
            return self._render_horizontal(window)

        self._active_profile = _RenderProfile()
        t0: float = time.perf_counter()

        try:
            if window.is_vertical:
                pix = self._render_vertical(window)
                mode = "vertical"
            else:
                pix = self._render_horizontal(window)
                mode = "horizontal"
        finally:
            total_ms: float = (time.perf_counter() - t0) * 1000.0
            prof = self._active_profile
            self._active_profile = None

        # 合計が遅いときだけログ（レート制限あり）
        try:
            warn_ms: float = float(getattr(self, "_profile_warn_ms", 16.0))
            if total_ms < warn_ms:
                return pix

            now: float = time.perf_counter()
            last: float = float(getattr(self, "_profile_last_log_ts", 0.0))
            cooldown: float = float(getattr(self, "_profile_log_cooldown_s", 0.2))
            if (now - last) < cooldown:
                return pix
            self._profile_last_log_ts = now

            try:
                fs = int(getattr(window, "font_size", 0))
            except Exception:
                fs = 0

            try:
                txt = str(getattr(window, "text", "") or "").replace("\n", "\\n")
                if len(txt) > 30:
                    txt = txt[:30] + "..."
            except Exception:
                txt = ""

            parts = {}
            counts = {}
            if prof is not None:
                parts = dict(prof.parts_ms)
                counts = dict(prof.counts)

            logger.debug(
                "TextRenderer.render profile: total=%.1fms mode=%s font=%s text='%s' parts=%s counts=%s",
                total_ms,
                mode,
                fs,
                txt,
                parts,
                counts,
            )
        except Exception as e:
            logger.debug(f"Profile log error: {e}")

        return pix

    def paint_direct(
        self,
        painter: QPainter,
        window: Any,
        target_rect: Optional[QRect] = None,
    ) -> QSize:
        """外部 QPainter に直接描画する（マインドマップ用、DPR 対応）。

        既存の render() は QPixmap を返すが、このメソッドは渡された QPainter に
        直接描画する。QGraphicsItem.paint() から呼び出すことで、DPR（デバイス
        ピクセル比）問題を回避できる。

        Args:
            painter: 描画先の QPainter（例: MindMapNode.paint() から渡される）
            window: TextWindow/MindMapTextAdapter 互換オブジェクト
            target_rect: 描画先の矩形。None の場合は自動計算。

        Returns:
            QSize: 描画に使用したキャンバスサイズ
        """
        if window.is_vertical:
            return self._paint_direct_vertical(painter, window, target_rect)
        return self._paint_direct_horizontal(painter, window, target_rect)

    def _paint_direct_horizontal(
        self,
        painter: QPainter,
        window: Any,
        target_rect: Optional[QRect] = None,
    ) -> QSize:
        """横書きテキストを直接描画する。"""
        font = QFont(window.font_family, int(window.font_size))
        fm = QFontMetrics(font)

        # Spacing Split: Horizontal
        # margin (char spacing)
        margin = int(window.font_size * getattr(window, "char_spacing_h", window.horizontal_margin_ratio))
        # line spacing (extra space between lines)
        line_spacing = int(window.font_size * getattr(window, "line_spacing_h", 0.0))

        shadow_offset_x = int(window.font_size * window.shadow_offset_x)
        shadow_offset_y = int(window.font_size * window.shadow_offset_y)

        m_top = int(window.font_size * window.margin_top_ratio)
        m_bottom = int(window.font_size * window.margin_bottom_ratio)
        m_left = int(window.font_size * window.margin_left_ratio)
        m_right = int(window.font_size * window.margin_right_ratio)

        lines = window.text.split("\n") if window.text else [""]
        max_line_width = 0
        for line in lines:
            line_width = sum(fm.horizontalAdvance(char) for char in line) + margin * (max(0, len(line) - 1))
            max_line_width = max(max_line_width, line_width)

        line_height = fm.height()
        total_height = (line_height + line_spacing) * len(lines)

        outline_width = max(
            window.font_size * window.background_outline_width_ratio if window.background_outline_enabled else 0, 1
        )

        canvas_size = QSize(
            int(max_line_width + max(shadow_offset_x, 0) + m_left + m_right + 2 * outline_width),
            int(total_height + max(shadow_offset_y, 0) + m_top + m_bottom + 2 * outline_width),
        )

        # 座標変換を保存
        painter.save()
        try:
            # target_rect が指定されている場合は、その位置に移動
            if target_rect is not None:
                painter.translate(target_rect.topLeft())

            painter.setFont(font)
            self._draw_background(painter, window, canvas_size, outline_width)
            self._draw_horizontal_text_elements(
                painter,
                window,
                canvas_size,
                lines,
                fm,
                shadow_offset_x,
                shadow_offset_y,
                m_left,
                m_top,
                margin,
                outline_width,
                line_spacing=line_spacing,
            )
        finally:
            painter.restore()

        return canvas_size

    def _paint_direct_vertical(
        self,
        painter: QPainter,
        window: Any,
        target_rect: Optional[QRect] = None,
    ) -> QSize:
        """縦書きテキストを直接描画する。"""
        font = QFont(window.font_family, int(window.font_size))

        # Spacing Split: Vertical
        # margin (char spacing within a column)
        char_spacing = int(window.font_size * getattr(window, "char_spacing_v", 0.0))
        # line spacing (gap between columns)
        # 1.0 + ratio implies ratio is the GAP. Standard vertical_margin_ratio was ~0.2 (gap).
        line_spacing_ratio = getattr(window, "line_spacing_v", window.vertical_margin_ratio)

        m_top = int(window.font_size * window.margin_top_ratio)
        m_bottom = int(window.font_size * window.margin_bottom_ratio)
        m_left = int(window.font_size * window.margin_left_ratio)
        m_right = int(window.font_size * window.margin_right_ratio)

        shadow_offset_x = int(window.font_size * window.shadow_offset_x)
        shadow_offset_y = int(window.font_size * window.shadow_offset_y)

        lines = window.text.split("\n") if window.text else [""]
        max_chars_per_line = max(len(line) for line in lines)
        num_lines = len(lines)

        outline_width = max(
            window.font_size * window.background_outline_width_ratio if window.background_outline_enabled else 0, 1
        )

        # width: Columns flow from right to left (usually).
        # Total width = (font_size + gap) * num_lines
        # Note: Previous logic was (font_size + margin) * num_lines.
        # Here we use line_spacing_ratio which acts as the 'margin' between columns.
        width = int(
            (window.font_size * (1.0 + line_spacing_ratio)) * num_lines
            + m_left
            + m_right
            + abs(shadow_offset_x)
            + 2 * outline_width
        )

        # total_height: Chars flow top to bottom.
        # Total height = (font_size + char_spacing) * max_chars
        total_height = int(
            (window.font_size + char_spacing) * max_chars_per_line
            + m_top
            + m_bottom
            + abs(shadow_offset_y)
            + 2 * outline_width
        )

        canvas_size = QSize(width, total_height)

        # 座標変換を保存
        painter.save()
        try:
            # target_rect が指定されている場合は、その位置に移動
            if target_rect is not None:
                painter.translate(target_rect.topLeft())

            painter.setFont(font)
            self._draw_background(painter, window, canvas_size, outline_width)
            self._draw_vertical_text_elements(
                painter,
                window,
                canvas_size,
                lines,
                m_top,
                char_spacing,  # Uses char_spacing instead of ambiguous margin
                m_right,
                shadow_offset_x,
                shadow_offset_y,
                outline_width,
                line_spacing_ratio=line_spacing_ratio,
            )
        finally:
            painter.restore()

        return canvas_size

    def _render_horizontal(self, window: Any) -> QPixmap:
        """横書きテキストをレンダリングします。"""
        font = QFont(window.font_family, int(window.font_size))
        fm = QFontMetrics(font)

        # Spacing Split: Horizontal
        # margin (char spacing)
        margin = int(window.font_size * getattr(window, "char_spacing_h", window.horizontal_margin_ratio))
        # line spacing (extra space between lines)
        line_spacing = int(window.font_size * getattr(window, "line_spacing_h", 0.0))

        shadow_offset_x = int(window.font_size * window.shadow_offset_x)
        shadow_offset_y = int(window.font_size * window.shadow_offset_y)

        m_top = int(window.font_size * window.margin_top_ratio)
        m_bottom = int(window.font_size * window.margin_bottom_ratio)
        m_left = int(window.font_size * window.margin_left_ratio)
        m_right = int(window.font_size * window.margin_right_ratio)

        lines = window.text.split("\n")
        max_line_width = 0
        for line in lines:
            line_width = sum(fm.horizontalAdvance(char) for char in line) + margin * (max(0, len(line) - 1))
            max_line_width = max(max_line_width, line_width)

        line_height = fm.height()
        total_height = (line_height + line_spacing) * len(lines)

        outline_width = max(
            window.font_size * window.background_outline_width_ratio if window.background_outline_enabled else 0, 1
        )

        canvas_size = QSize(
            int(max_line_width + max(shadow_offset_x, 0) + m_left + m_right + 2 * outline_width),
            int(total_height + max(shadow_offset_y, 0) + m_top + m_bottom + 2 * outline_width),
        )

        window.canvas_size = canvas_size

        # 修正: 編集中は InlineEditorMixin がサイズを管理するため、Rendererによるリサイズを防止する (Flicker対策)
        if not getattr(window, "_is_editing", False):
            window.setGeometry(QRect(window.pos(), canvas_size))

        pixmap = QPixmap(canvas_size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        try:
            painter.setFont(font)
            self._draw_background(painter, window, canvas_size, outline_width)
            self._draw_horizontal_text_elements(
                painter,
                window,
                canvas_size,
                lines,
                fm,
                shadow_offset_x,
                shadow_offset_y,
                m_left,
                m_top,
                margin,
                outline_width,
                line_spacing=line_spacing,
            )
        finally:
            painter.end()

        return pixmap

    def _render_vertical(self, window: Any) -> QPixmap:
        """縦書きテキストをレンダリングします。"""
        font = QFont(window.font_family, int(window.font_size))

        # Spacing Split: Vertical
        char_spacing = int(window.font_size * getattr(window, "char_spacing_v", 0.0))
        line_spacing_ratio = getattr(window, "line_spacing_v", window.vertical_margin_ratio)

        # 縦書き専用余白を使用（v_margin_*_ratio プロパティ）
        # TextWindow に追加された縦書き専用プロパティを直接使用
        m_top = int(window.font_size * getattr(window, "v_margin_top_ratio", 0.3))
        m_bottom = int(window.font_size * getattr(window, "v_margin_bottom_ratio", 0.0))
        m_left = int(window.font_size * getattr(window, "v_margin_left_ratio", 0.0))
        m_right = int(window.font_size * getattr(window, "v_margin_right_ratio", 0.0))

        shadow_offset_x = int(window.font_size * window.shadow_offset_x)
        shadow_offset_y = int(window.font_size * window.shadow_offset_y)

        lines = window.text.split("\n") if window.text else [""]
        max_chars_per_line = max(len(line) for line in lines)
        num_lines = len(lines)

        outline_width = max(
            window.font_size * window.background_outline_width_ratio if window.background_outline_enabled else 0, 1
        )

        width = int(
            (window.font_size * (1.0 + line_spacing_ratio)) * num_lines
            + m_left
            + m_right
            + abs(shadow_offset_x)
            + 2 * outline_width
        )
        total_height = int(
            (window.font_size + char_spacing) * max_chars_per_line
            + m_top
            + m_bottom
            + abs(shadow_offset_y)
            + 2 * outline_width
        )

        canvas_size = QSize(width, total_height)
        window.canvas_size = canvas_size

        # 修正: 編集中は InlineEditorMixin がサイズを管理するため、Rendererによるリサイズを防止する (Flicker対策)
        if not getattr(window, "_is_editing", False):
            window.setGeometry(QRect(window.pos(), canvas_size))

        pixmap = QPixmap(canvas_size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        try:
            painter.setFont(font)
            self._draw_background(painter, window, canvas_size, outline_width)
            self._draw_vertical_text_elements(
                painter,
                window,
                canvas_size,
                lines,
                m_top,
                char_spacing,
                m_right,
                shadow_offset_x,
                shadow_offset_y,
                outline_width,
                line_spacing_ratio=line_spacing_ratio,
            )
        finally:
            painter.end()

        return pixmap

    def _render_cache_get(self, key: str) -> Optional[QPixmap]:
        """最終レンダキャッシュから取得する（LRU更新あり）。"""
        if self._render_cache_size <= 0:
            return None
        try:
            pix = self._render_cache.get(key)
            if pix is None:
                return None
            self._render_cache.move_to_end(key)
            return pix
        except Exception:
            return None

    def _render_cache_put(self, key: str, pixmap: QPixmap) -> None:
        """最終レンダキャッシュへ格納する（LRU上限あり）。"""
        if self._render_cache_size <= 0:
            return
        try:
            self._render_cache[key] = pixmap
            self._render_cache.move_to_end(key)
            while len(self._render_cache) > self._render_cache_size:
                self._render_cache.popitem(last=False)
        except Exception:
            pass

    def _make_render_cache_key(self, window: Any) -> str:
        """window状態から、最終レンダ結果キャッシュ用のキーを生成する。

        Notes:
            - 見た目に影響する値だけをキーに入れるのが理想だが、
              まずは安全側で「config全部 + 実装依存の一部」を含める。
            - 位置(x,y)は見た目に影響しないので除外する（同一見た目でキャッシュを共有できる）。

        Args:
            window (Any): TextWindow/ConnectorLabel互換。

        Returns:
            str: キャッシュキー。
        """
        try:
            cfg = getattr(window, "config", None)
            if cfg is not None and hasattr(cfg, "model_dump"):
                # position/uuid/parent_uuid は除外（見た目に無関係）
                data = cfg.model_dump(mode="json", exclude={"uuid", "parent_uuid", "position"})
            else:
                data = {}

            # TextRendererが参照する補助情報も含める
            # （canvas_sizeは出力結果に依存するのでキーには入れない）
            extra = {
                "_type": type(window).__name__,
            }

            # JSON化（順序を安定させる）
            return json.dumps({"cfg": data, "extra": extra}, ensure_ascii=False, sort_keys=True)
        except Exception:
            # 最終保険
            try:
                return f"{type(window).__name__}:{repr(getattr(window, 'text', ''))}:{repr(getattr(window, 'font_size', ''))}"
            except Exception:
                return str(id(window))

    def _draw_background(self, painter: QPainter, window: Any, canvas_size: QSize, outline_width: float) -> None:
        """背景と背景の縁取りを描画します。"""
        t0: Optional[float] = None
        if self._active_profile is not None:
            t0 = time.perf_counter()

        background_corner_radius = int(window.font_size * window.background_corner_ratio)
        path = QPainterPath()
        rect = QRect(
            int(outline_width / 2),
            int(outline_width / 2),
            int(canvas_size.width() - outline_width),
            int(canvas_size.height() - outline_width),
        )
        path.addRoundedRect(rect, background_corner_radius, background_corner_radius)

        painter.setRenderHint(QPainter.Antialiasing, True)

        if window.background_gradient_enabled and window.background_gradient:
            gradient = self._create_gradient(
                rect, window.background_gradient, window.background_gradient_angle, window.background_gradient_opacity
            )
            painter.setBrush(gradient)
        else:
            bg_color = QColor(window.background_color)
            bg_color.setAlpha(int(window.background_opacity * 2.55))
            painter.setBrush(bg_color)

        if window.background_outline_enabled:
            outline_color = QColor(window.background_outline_color)
            outline_color.setAlpha(int(window.background_outline_opacity * 2.55))
            pen = QPen(outline_color, outline_width)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)

        painter.drawPath(path)
        if t0 is not None:
            self._prof_add("bg_total", (time.perf_counter() - t0) * 1000.0)

    def _draw_horizontal_text_elements(
        self,
        painter: QPainter,
        window: Any,
        canvas_size: QSize,
        lines: List[str],
        fm: QFontMetrics,
        shadow_offset_x: int,
        shadow_offset_y: int,
        margin_left: int,
        margin_top: int,
        margin: int,
        outline_width: float,
        line_spacing: int = 0,
    ) -> None:
        t0_total: Optional[float] = None
        if self._active_profile is not None:
            t0_total = time.perf_counter()
        """横書き時のテキスト要素（影、縁取り、メイン）を順に描画します。"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        font = painter.font()
        start_y = margin_top + fm.ascent() + outline_width
        start_x = margin_left + outline_width

        # 1. 影
        if window.shadow_enabled:
            s_color = QColor(window.shadow_color)
            s_color.setAlpha(int(window.shadow_opacity * 2.55))
            s_font = QFont(window.font_family, int(window.font_size * window.shadow_scale))
            s_fm = QFontMetrics(s_font)

            if window.shadow_blur == 0:
                # 直接描画 (最高品質)
                painter.save()
                painter.setFont(s_font)
                painter.setPen(s_color)
                self._draw_horizontal_text_content(
                    painter,
                    window,
                    lines,
                    fm,
                    margin,
                    start_x,
                    start_y,
                    custom_offset=QPointF(shadow_offset_x, shadow_offset_y),
                    shadow_fm=s_fm,
                    line_spacing=line_spacing,
                )
                painter.restore()
            else:
                # ブラー付き描画 (QPixmap 経由)
                s_pixmap = QPixmap(canvas_size)
                s_pixmap.fill(Qt.transparent)
                s_painter = QPainter(s_pixmap)
                s_painter.setRenderHint(QPainter.Antialiasing, True)
                s_painter.setFont(s_font)
                s_painter.setPen(s_color)
                self._draw_horizontal_text_content(
                    s_painter,
                    window,
                    lines,
                    fm,
                    margin,
                    start_x,
                    start_y,
                    custom_offset=QPointF(shadow_offset_x, shadow_offset_y),
                    shadow_fm=s_fm,
                    line_spacing=line_spacing,
                )
                s_painter.end()
                painter.drawPixmap(0, 0, self._apply_blur_to_pixmap(s_pixmap, window.shadow_blur))

        # 2. 縁取り (背面から前面へ: 3 -> 2 -> 1)
        outlines = [
            (
                window.third_outline_enabled,
                window.third_outline_color,
                window.third_outline_opacity,
                window.third_outline_width,
                window.third_outline_blur,
            ),
            (
                window.second_outline_enabled,
                window.second_outline_color,
                window.second_outline_opacity,
                window.second_outline_width,
                window.second_outline_blur,
            ),
            (
                window.outline_enabled,
                window.outline_color,
                window.outline_opacity,
                window.outline_width,
                window.outline_blur,
            ),
        ]

        for enabled, color, opacity, width, blur in outlines:
            if not enabled:
                continue

            c = QColor(color)
            c.setAlpha(int(opacity * 2.55))
            pen = QPen(c, width)
            pen.setJoinStyle(Qt.RoundJoin)

            if blur == 0:
                # 直接描画 (最高品質)
                painter.setPen(pen)
                self._draw_horizontal_text_content(
                    painter, window, lines, fm, margin, start_x, start_y, is_outline=True, line_spacing=line_spacing
                )
            else:
                # ブラー付き描画 (QPixmap 経由)
                o_pixmap = QPixmap(canvas_size)
                o_pixmap.fill(Qt.transparent)
                o_painter = QPainter(o_pixmap)
                o_painter.setRenderHint(QPainter.Antialiasing, True)
                o_painter.setFont(font)
                o_painter.setPen(pen)
                self._draw_horizontal_text_content(
                    o_painter, window, lines, fm, margin, start_x, start_y, is_outline=True, line_spacing=line_spacing
                )
                o_painter.end()
                painter.drawPixmap(0, 0, self._apply_blur_to_pixmap(o_pixmap, blur))

        # 3. メインテキスト
        main_color = QColor(window.font_color)
        main_color.setAlpha(int(window.text_opacity * 2.55))
        painter.setPen(main_color)
        painter.setBrush(Qt.NoBrush)
        self._draw_horizontal_text_content(
            painter,
            window,
            lines,
            fm,
            margin,
            start_x,
            start_y,
            is_main_text=True,
            line_spacing=line_spacing,
        )

        if t0_total is not None:
            self._prof_add("h_text_elements_total", (time.perf_counter() - t0_total) * 1000.0)

    def _draw_horizontal_text_content(
        self,
        painter: QPainter,
        window: Any,
        lines: List[str],
        fm: QFontMetrics,
        margin: int,
        start_x: float,
        start_y: float,
        is_main_text: bool = False,
        is_outline: bool = False,
        custom_offset: QPointF = QPointF(0, 0),
        shadow_fm: Optional[QFontMetrics] = None,
        line_spacing: int = 0,
    ) -> None:
        """横書きテキストの各文字を実際に描画します（計測＋glyphキャッシュ対応：見た目維持版）。

        方針:
            - 通常文字（グラデ無し・縁取り無し）は drawText を維持（見た目一致を優先）
            - 縁取りは glyph path キャッシュ（translated）で drawPath
            - グラデは glyph path キャッシュ（translated）で fillPath
        """
        t0_total: Optional[float] = None
        if self._active_profile is not None:
            t0_total = time.perf_counter()

        try:
            font: QFont = painter.font()
            y: float = float(start_y)

            for line in lines:
                curr_x: float = float(start_x)
                curr_x_s: float = float(start_x)

                for char in line:
                    draw_x, draw_y = curr_x, y
                    char_width = fm.horizontalAdvance(char)

                    if shadow_fm:
                        draw_x = curr_x_s - (shadow_fm.horizontalAdvance(char) - char_width) / 2
                        draw_y = y + (shadow_fm.ascent() - fm.ascent()) / 2
                        curr_x_s += char_width + margin

                    pos = QPointF(draw_x + custom_offset.x(), draw_y + custom_offset.y())

                    # 1) グラデ文字（メインテキストのみ）
                    if is_main_text and window.text_gradient_enabled and window.text_gradient:
                        char_rect = QRect(int(draw_x), int(draw_y - fm.ascent()), int(char_width), int(fm.height()))
                        gradient = self._create_gradient(
                            char_rect,
                            window.text_gradient,
                            window.text_gradient_angle,
                            window.text_gradient_opacity,
                        )

                        glyph0 = self._get_glyph_path(font, char)  # 0,0(ベースライン)基準
                        path = glyph0.translated(pos)
                        painter.fillPath(path, gradient)

                    # 2) 縁取り（outline）
                    elif is_outline:
                        glyph0 = self._get_glyph_path(font, char)
                        path = glyph0.translated(pos)
                        painter.drawPath(path)

                    # 3) 通常文字（影など）：drawText を維持（見た目を崩さない）
                    else:
                        painter.drawText(pos, char)

                    curr_x += char_width + margin

                y += fm.height() + line_spacing

        finally:
            if t0_total is not None:
                self._prof_add("h_text_content_total", (time.perf_counter() - t0_total) * 1000.0)
                try:
                    self._prof_inc("h_text_chars", sum(len(ln) for ln in lines))
                except Exception:
                    pass

    def _draw_vertical_text_elements(
        self,
        painter: QPainter,
        window: Any,
        canvas_size: QSize,
        lines: List[str],
        top_margin: int,
        margin: int,
        right_margin: int,
        shadow_x: int,
        shadow_y: int,
        outline_width: float,
        line_spacing_ratio: float = 0.5,
    ) -> None:
        t0_total: Optional[float] = None
        if self._active_profile is not None:
            t0_total = time.perf_counter()

        """縦書き時のテキスト要素を順に描画します。"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        font = painter.font()
        x_shift = 1.0 + line_spacing_ratio

        # 1. 影
        if window.shadow_enabled:
            s_color = QColor(window.shadow_color)
            s_color.setAlpha(int(window.shadow_opacity * 2.55))
            s_font = QFont(window.font_family, int(window.font_size * window.shadow_scale))

            if window.shadow_blur == 0:
                # 直接描画 (最高品質)
                painter.save()
                painter.setFont(s_font)
                painter.setPen(s_color)
                self._draw_vertical_text_content(
                    painter,
                    window,
                    lines,
                    x_shift,
                    top_margin,
                    margin,
                    right_margin,
                    shadow_x,
                    outline_width,
                    canvas_size,
                    custom_offset=QPointF(shadow_x, shadow_y),
                )
                painter.restore()
            else:
                # ブラー付き描画 (QPixmap 経由)
                s_pixmap = QPixmap(canvas_size)
                s_pixmap.fill(Qt.transparent)
                s_painter = QPainter(s_pixmap)
                s_painter.setRenderHint(QPainter.Antialiasing, True)
                s_painter.setFont(s_font)
                s_painter.setPen(s_color)
                self._draw_vertical_text_content(
                    s_painter,
                    window,
                    lines,
                    x_shift,
                    top_margin,
                    margin,
                    right_margin,
                    shadow_x,
                    outline_width,
                    canvas_size,
                    custom_offset=QPointF(shadow_x, shadow_y),
                )
                s_painter.end()
                painter.drawPixmap(0, 0, self._apply_blur_to_pixmap(s_pixmap, window.shadow_blur))

        # 2. 縁取り
        outlines = [
            (
                window.third_outline_enabled,
                window.third_outline_color,
                window.third_outline_opacity,
                window.third_outline_width,
                window.third_outline_blur,
            ),
            (
                window.second_outline_enabled,
                window.second_outline_color,
                window.second_outline_opacity,
                window.second_outline_width,
                window.second_outline_blur,
            ),
            (
                window.outline_enabled,
                window.outline_color,
                window.outline_opacity,
                window.outline_width,
                window.outline_blur,
            ),
        ]
        for enabled, color, opacity, width, blur in outlines:
            if not enabled:
                continue

            c = QColor(color)
            c.setAlpha(int(opacity * 2.55))
            pen = QPen(c, width)
            pen.setJoinStyle(Qt.RoundJoin)

            if blur == 0:
                # 直接描画 (最高品質)
                painter.setPen(pen)
                self._draw_vertical_text_content(
                    painter,
                    window,
                    lines,
                    x_shift,
                    top_margin,
                    margin,
                    right_margin,
                    shadow_x,
                    outline_width,
                    canvas_size,
                    is_outline=True,
                )
            else:
                # ブラー付き描画 (QPixmap 経由)
                o_pixmap = QPixmap(canvas_size)
                o_pixmap.fill(Qt.transparent)
                o_painter = QPainter(o_pixmap)
                o_painter.setRenderHint(QPainter.Antialiasing, True)
                o_painter.setFont(font)
                o_painter.setPen(pen)
                self._draw_vertical_text_content(
                    o_painter,
                    window,
                    lines,
                    x_shift,
                    top_margin,
                    margin,
                    right_margin,
                    shadow_x,
                    outline_width,
                    canvas_size,
                    is_outline=True,
                )
                o_painter.end()
                painter.drawPixmap(0, 0, self._apply_blur_to_pixmap(o_pixmap, blur))

        # 3. メイン
        main_color = QColor(window.font_color)
        main_color.setAlpha(int(window.text_opacity * 2.55))
        painter.setPen(main_color)
        self._draw_vertical_text_content(
            painter,
            window,
            lines,
            x_shift,
            top_margin,
            margin,
            right_margin,
            shadow_x,
            outline_width,
            canvas_size,
            is_main_text=True,
        )

        if t0_total is not None:
            self._prof_add("v_text_elements_total", (time.perf_counter() - t0_total) * 1000.0)

    def _draw_vertical_text_content(
        self,
        painter: QPainter,
        window: Any,
        lines: List[str],
        x_shift: float,
        top_margin: int,
        margin: int,
        right_margin: int,
        shadow_x: int,
        outline_width: float,
        canvas_size: QSize,
        is_main_text: bool = False,
        is_outline: bool = False,
        custom_offset: QPointF = QPointF(0, 0),
    ) -> None:
        """縦書きテキストの各文字を座標変換を用いて描画します（計測＋glyphキャッシュ対応：見た目維持版）。

        方針:
            - 回転/記号補正は既存ロジック（_get_vertical_char_transform）を尊重
            - glyphは (font, char) 単位でキャッシュ
            - 描画は painter.translate(cx, cy) + rotate(rot) の後、
              glyph0.translated(dx, dy) を draw/fill する（位置ズレを減らす）
        """
        t0_total: Optional[float] = None
        if self._active_profile is not None:
            t0_total = time.perf_counter()

        try:
            font: QFont = painter.font()
            curr_x = canvas_size.width() - window.font_size - margin - right_margin - shadow_x - outline_width
            y_start = top_margin + outline_width

            for line in lines:
                y = y_start
                for char in line:
                    rot, dx, dy = self._get_vertical_char_transform(window, char, font)

                    cx = float(curr_x) + float(window.font_size) / 2.0
                    cy = float(y) + float(window.font_size) / 2.0

                    painter.save()
                    try:
                        painter.translate(cx + custom_offset.x(), cy + custom_offset.y())
                        if rot != 0:
                            painter.rotate(rot)

                        glyph0 = self._get_glyph_path(font, char)

                        # dx,dy は「文字を中心に置くための補正」なので translated で適用
                        placed = glyph0.translated(float(dx), float(dy))

                        if is_main_text and window.text_gradient_enabled and window.text_gradient:
                            rect = QRect(
                                int(-window.font_size / 2),
                                int(-window.font_size / 2),
                                int(window.font_size),
                                int(window.font_size),
                            )
                            grad = self._create_gradient(
                                rect,
                                window.text_gradient,
                                window.text_gradient_angle,
                                window.text_gradient_opacity,
                            )
                            painter.fillPath(placed, grad)

                        elif is_outline:
                            # 縁取りは drawPath（ペンで輪郭を描く）
                            painter.drawPath(placed)

                        else:
                            # 影・通常文字は drawText を使う（塗りつぶしを確実に出す＝見た目維持）
                            painter.drawText(QPointF(float(dx), float(dy)), char)

                    finally:
                        painter.restore()

                    y += window.font_size + margin

                curr_x -= window.font_size * x_shift

        finally:
            if t0_total is not None:
                self._prof_add("v_text_content_total", (time.perf_counter() - t0_total) * 1000.0)
                try:
                    self._prof_inc("v_text_chars", sum(len(ln) for ln in lines))
                except Exception:
                    pass

    def _get_vertical_char_transform(self, window: Any, char: str, font: QFont) -> Tuple[float, float, float]:
        """縦書き時の文字ごとの回転角と描画オフセットを計算します。"""
        fm = QFontMetrics(font)
        if char in r"[]ー～()（）＜＞「」-=\<>『』〔〕｛｝〈〉《》＝…:;‐":
            path = QPainterPath()
            path.addText(0, 0, font, char)
            rect = path.boundingRect()
            return 90, -(rect.x() + rect.width() / 2), -(rect.y() + rect.height() / 2)

        if char in "、。":
            base_x, base_y = -window.font_size / 2, window.font_size / 2
            if window.offset_mode == OffsetMode.MONO:
                ox, oy = window.font_size * 0.75, window.font_size * -0.55
            else:
                ox, oy = window.font_size * 0.3, window.font_size * -0.5
            return 0, base_x + ox, base_y + oy

        return 0, -fm.horizontalAdvance(char) / 2, -window.font_size / 2 + fm.ascent()

    def _apply_blur_to_pixmap(self, pixmap: QPixmap, blur_val: float) -> QPixmap:
        """QPixmapにぼかしエフェクトを適用します（計測対応）。"""
        if blur_val <= 0:
            return pixmap

        t0: Optional[float] = None
        if self._active_profile is not None:
            t0 = time.perf_counter()
            self._prof_inc("blur_calls", 1)

        try:
            scene = QGraphicsScene()
            item = QGraphicsPixmapItem(pixmap)
            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(float(blur_val) * 20.0 / 100.0)
            item.setGraphicsEffect(blur)
            scene.addItem(item)

            res = QPixmap(pixmap.size())
            res.fill(Qt.transparent)
            p = QPainter(res)
            try:
                scene.render(p)
            finally:
                p.end()
            return res

        finally:
            if t0 is not None:
                self._prof_add("blur_total", (time.perf_counter() - t0) * 1000.0)

    def _create_gradient(
        self,
        rect: QRect,
        definition: List[Tuple[float, str]],
        angle: float,
        opacity: float,
    ) -> QLinearGradient:
        """指定された矩形、定義、角度に基づき線形グラデーションを生成します（計測対応）。"""
        t0: Optional[float] = None
        if self._active_profile is not None:
            t0 = time.perf_counter()
            self._prof_inc("grad_calls", 1)

        try:
            rad = math.radians(angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            factor = math.hypot(rect.width(), rect.height()) / 2
            center = rect.center()

            start = QPointF(center.x() - cos_a * factor, center.y() - sin_a * factor)
            end = QPointF(center.x() + cos_a * factor, center.y() + sin_a * factor)

            grad = QLinearGradient(start, end)
            for stop, color_str in definition:
                color = QColor(color_str)
                color.setAlpha(int(opacity * 2.55))
                grad.setColorAt(stop, color)
            return grad

        finally:
            if t0 is not None:
                self._prof_add("grad_total", (time.perf_counter() - t0) * 1000.0)

    def _blur_cache_get(self, key: tuple[int, int, int, int]) -> Optional[QPixmap]:
        """ぼかしキャッシュから取得する（LRU更新あり）。"""
        if self._blur_cache_size <= 0:
            return None
        try:
            pix = self._blur_cache.get(key)
            if pix is None:
                return None
            # LRU更新
            self._blur_cache.move_to_end(key)
            return pix
        except Exception:
            return None

    def _blur_cache_put(self, key: tuple[int, int, int, int], pixmap: QPixmap) -> None:
        """ぼかしキャッシュへ格納する（LRUで上限管理）。"""
        if self._blur_cache_size <= 0:
            return
        try:
            self._blur_cache[key] = pixmap
            self._blur_cache.move_to_end(key)
            while len(self._blur_cache) > self._blur_cache_size:
                self._blur_cache.popitem(last=False)
        except Exception:
            # キャッシュ失敗は描画に影響させない
            pass

    def _get_glyph_path(self, font: QFont, char: str) -> QPainterPath:
        """指定フォント・指定文字の glyph(QPainterPath) をLRUキャッシュして返す。

        Args:
            font (QFont): 描画フォント（family/sizeが重要）。
            char (str): 1文字。

        Returns:
            QPainterPath: 原点(0,0)基準のglyph path。
        """
        try:
            family: str = str(font.family())
        except Exception:
            family = ""

        try:
            size: int = int(font.pointSize())
        except Exception:
            size = 0

        ch: str = str(char)

        key: tuple[str, int, str] = (family, size, ch)

        try:
            cached = self._glyph_cache.get(key)
            if cached is not None:
                # LRU更新
                self._glyph_cache.move_to_end(key)
                return cached
        except Exception:
            pass

        # キャッシュ無し：生成
        path = QPainterPath()
        try:
            # addText(x, y, font, text) の (x,y) はベースライン基準
            # ここでは原点に置く（後で translate で位置決めする）
            path.addText(0.0, 0.0, font, ch)
        except Exception:
            # 失敗しても空pathで落とさない
            path = QPainterPath()

        # キャッシュへ格納（LRU上限）
        try:
            self._glyph_cache[key] = path
            self._glyph_cache.move_to_end(key)

            while len(self._glyph_cache) > int(self._glyph_cache_size):
                self._glyph_cache.popitem(last=False)
        except Exception:
            pass

        return path

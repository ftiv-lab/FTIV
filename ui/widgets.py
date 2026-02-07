import math
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QLinearGradient, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QColorDialog, QMessageBox, QPushButton, QSizePolicy, QWidget


class ColorButton(QPushButton):
    """色を表示・選択するためのボタン。

    背景色として現在色を表示し、クリック時にシグナルを発行するか、
    ダイアログ表示ロジックをカプセル化（将来）するためのウィジェット。
    """

    colorChanged = Signal(QColor)

    def __init__(self, color: Optional[QColor] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._color = QColor(color) if color else QColor("#ffffff")
        self.setFlat(False)  # QSSのボーダーを有効にするため
        self._update_style()

    def setColor(self, color: QColor):
        """色を設定し、スタイルを更新します。"""
        if self._color == color:
            return
        self._color = color
        self._update_style()
        self.colorChanged.emit(self._color)

    def color(self) -> QColor:
        """現在の色を返します。"""
        return self._color

    def _update_style(self):
        """背景色のみを更新し、ボーダーはQSSに委ねます。"""
        if self._color.isValid():
            # Alpha対応のため HexArgb を使用
            self.setStyleSheet(f"background-color: {self._color.name(QColor.HexArgb)};")
        else:
            self.setStyleSheet("")


class Gradient(QWidget):
    """グラデーションを表示・編集するためのカスタムウィジェット。

    ストップポイントの追加、削除、色の変更、および角度の調整をサポートします。
    """

    gradientChanged = Signal()
    selectedStopChanged = Signal(int)  # 選択中stop indexが変わった

    def __init__(self, gradient: Optional[List[Tuple[float, str]]] = None, angle: int = 0, *args, **kwargs) -> None:
        """Gradientウィジェットを初期化します。

        Args:
            gradient (Optional[List[Tuple[float, str]]]): (位置, HEX色) のタプルのリスト。
            angle (int): グラデーションの角度（0-359）。
        """
        super().__init__(*args, **kwargs)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # デフォルトのグラデーション設定
        self._gradient: List[Tuple[float, str]] = (
            gradient
            if gradient
            else [
                (0.0, "#000000"),
                (1.0, "#ffffff"),
            ]
        )

        self._angle: int = int(angle)
        self._handle_w: int = 12
        self._handle_h: int = 12
        self._drag_position: Optional[int] = None

        # 選択は常に維持（空でなければ0）
        self._selected_index: Optional[int] = 0 if self._gradient else None

        # 初期状態を正規化
        self._constrain_gradient()
        self._sort_gradient()
        self._ensure_selected_index()

    def paintEvent(self, e: QPaintEvent) -> None:
        """ウィジェットの描画処理。

        Args:
            e (QPaintEvent): ペイントイベント。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        width = self.width()
        height = self.height()

        # 対角線から描画範囲を計算
        diag = math.hypot(width, height)
        radians = math.radians(self._angle)
        x_factor = math.cos(radians)
        y_factor = math.sin(radians)

        center_x, center_y = width / 2, height / 2

        # 開始点と終了点の計算
        start_p = QPointF(center_x - x_factor * diag / 2, center_y - y_factor * diag / 2)
        end_p = QPointF(center_x + x_factor * diag / 2, center_y + y_factor * diag / 2)

        gradient = QLinearGradient(start_p, end_p)
        for stop, color in self._gradient:
            gradient.setColorAt(stop, QColor(color))

        # 背景グラデーションの描画
        painter.fillRect(self.rect(), gradient)

        # ストップハンドルの描画
        self._draw_handles(painter, width, height)
        painter.end()

    def _draw_handles(self, painter: QPainter, width: int, height: int) -> None:
        """ストップポイントを操作するためのハンドルを描画します。

        Args:
            painter (QPainter): 使用するペインター。
            width (int): ウィジェットの幅。
            height (int): ウィジェットの高さ。
        """
        self._ensure_selected_index()

        midpoint: float = float(height) / 2.0

        for n, (stop, color_str) in enumerate(self._gradient):
            x_pos: int = int(round(float(stop) * float(width)))

            # ガイド線
            guide_pen: QPen = QPen(QColor(255, 255, 255, 160))
            guide_pen.setWidth(1)
            painter.setPen(guide_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(
                x_pos,
                int(midpoint - self._handle_h),
                x_pos,
                int(midpoint + self._handle_h),
            )

            # ハンドルrect
            handle_rect: QRect = QRect(
                int(x_pos - self._handle_w / 2),
                int(midpoint - self._handle_h / 2),
                int(self._handle_w),
                int(self._handle_h),
            )

            # 塗り（stop色）
            c: QColor = QColor(str(color_str))
            if not c.isValid():
                c = QColor("#ffffff")

            painter.setBrush(c)
            base_pen: QPen = QPen(QColor(0, 0, 0, 220))
            base_pen.setWidth(1)
            painter.setPen(base_pen)
            painter.drawRect(handle_rect)

            # 選択中を強調（二重枠）
            if self._selected_index is not None and n == int(self._selected_index):
                outer_pen: QPen = QPen(QColor("#00aaff"))
                outer_pen.setWidth(2)
                painter.setPen(outer_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(handle_rect.adjusted(-2, -2, 2, 2))

    def sizeHint(self) -> QSize:
        """ウィジェットの推奨サイズを返します。"""
        return QSize(400, 300)

    def _sort_gradient(self) -> None:
        """ストップポイントを位置順にソートします。"""
        self._gradient.sort(key=lambda g: g[0])

    def _constrain_gradient(self) -> None:
        """ストップポイントの位置を 0.0 - 1.0 の範囲に収めます。"""
        self._gradient = [(max(0.0, min(1.0, stop)), color) for stop, color in self._gradient]

    def setGradient(self, gradient: List[Tuple[float, str]]) -> None:
        """グラデーション全体を更新します。

        Args:
            gradient (List[Tuple[float, str]]): 新しいグラデーションリスト。
        """
        # 選択中stopのposを保持（indexはソートで壊れるため）
        selected_pos: Optional[float] = None
        try:
            if self._selected_index is not None and 0 <= int(self._selected_index) < len(self._gradient):
                selected_pos = float(self._gradient[int(self._selected_index)][0])
        except Exception:
            selected_pos = None

        self._gradient = list(gradient) if gradient else []
        self._constrain_gradient()
        self._sort_gradient()

        # 選択維持（pos最近傍）
        if self._gradient:
            if selected_pos is None:
                self._selected_index = 0
            else:
                self._selected_index = int(self._nearest_index_by_pos(float(selected_pos)))
        else:
            self._selected_index = None

        self._ensure_selected_index()

        self.gradientChanged.emit()
        if self._selected_index is not None:
            self.selectedStopChanged.emit(int(self._selected_index))
        self.update()

    def gradient(self) -> List[Tuple[float, str]]:
        """現在のグラデーションリストを取得します。"""
        return self._gradient

    def selected_index(self) -> Optional[int]:
        """現在選択中のストップインデックスを返します。"""
        return self._selected_index

    def set_selected_index(self, index: Optional[int]) -> None:
        """選択中ストップを設定し、UIに通知します。

        Args:
            index (Optional[int]): 選択するインデックス。Noneでも未選択にはしない（v1.1）。
        """
        if not self._gradient:
            self._selected_index = None
            self.update()
            return

        if index is None:
            index = 0

        try:
            i: int = int(index)
        except Exception:
            return

        if i < 0:
            i = 0
        if i >= len(self._gradient):
            i = len(self._gradient) - 1

        if self._selected_index == i:
            return

        self._selected_index = i
        self.selectedStopChanged.emit(i)
        self.update()

    @property
    def _end_stops(self) -> List[int]:
        """両端（0番目と最後）のインデックスを取得します。"""
        return [0, len(self._gradient) - 1]

    def addStop(self, stop: float, color: Optional[str] = None) -> None:
        """指定位置に新しいストップポイントを追加します。

        Args:
            stop (float): 追加する位置 (0.0 - 1.0)。
            color (Optional[str]): 追加する色のHEX値。指定がない場合は近傍の色を使用します。
        """
        for n, g in enumerate(self._gradient):
            if g[0] > stop:
                self._gradient.insert(n, (stop, color or g[1]))
                break
        else:
            self._gradient.append((stop, color or self._gradient[-1][1]))

        self._constrain_gradient()
        self.gradientChanged.emit()
        self.update()

    def setColorAtPosition(self, n: int, color: str) -> None:
        """指定インデックスのストップポイントの色を変更します。

        Args:
            n (int): インデックス。
            color (str): 新しい色のHEX値。
        """
        if 0 <= n < len(self._gradient):
            stop, _ = self._gradient[n]
            self._gradient[n] = (stop, color)
            self.gradientChanged.emit()
            self.update()

    def chooseColorAtPosition(self, n: int, current_color: Optional[str] = None) -> None:
        """カラーダイアログを表示してストップポイントの色を選択します。

        Args:
            n (int): インデックス。
            current_color (Optional[str]): ダイアログ表示時の初期色。
        """
        try:
            dlg = QColorDialog(self)
            if current_color:
                dlg.setCurrentColor(QColor(current_color))

            if dlg.exec():
                self.setColorAtPosition(n, dlg.currentColor().name())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open color dialog: {str(e)}")

    def _find_stop_handle_for_event(self, e: QMouseEvent, to_exclude: Optional[List[int]] = None) -> Optional[int]:
        """マウスイベントの位置にあるストップハンドルのインデックスを探します。

        Args:
            e (QMouseEvent): マウスイベント。
            to_exclude (Optional[List[int]]): 検索から除外するインデックスのリスト。

        Returns:
            Optional[int]: 見つかったインデックス。見つからない場合は None。
        """
        midpoint = self.height() / 2
        pos = e.position()

        # Y軸の判定
        if abs(pos.y() - midpoint) <= self._handle_h:
            width = self.width()
            for n, (stop, _) in enumerate(self._gradient):
                if to_exclude and n in to_exclude:
                    continue
                # X軸の判定
                if abs(pos.x() - (stop * width)) <= self._handle_w:
                    return n
        return None

    def mousePressEvent(self, e: QMouseEvent) -> None:
        """マウス押下時の処理。

        - 左クリック：ストップ選択、ドラッグ開始（端以外）
        - 右クリック：選択＋色変更（従来互換）
        """
        if e.button() == Qt.RightButton:
            n = self._find_stop_handle_for_event(e)
            if n is not None:
                self.set_selected_index(n)
                self.chooseColorAtPosition(n, self._gradient[n][1])
            return

        if e.button() == Qt.LeftButton:
            # まず選択（端も選べる）
            n_any = self._find_stop_handle_for_event(e)
            if n_any is not None:
                self.set_selected_index(n_any)

            # ドラッグ対象は端以外
            n_drag = self._find_stop_handle_for_event(e, to_exclude=self._end_stops)
            if n_drag is not None:
                self._drag_position = n_drag
            return

        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        """マウス離上時の処理。ドラッグを終了しソートを確定します。"""
        try:
            if self._drag_position is not None:
                # ドラッグしていたstop位置を基準に、ソート後も近いものを選択
                try:
                    dragged_pos = float(self._gradient[self._drag_position][0])
                except Exception:
                    dragged_pos = None

                self._drag_position = None
                self._sort_gradient()
                self.update()

                if dragged_pos is not None and self._gradient:
                    best_i = 0
                    best_d = 999.0
                    for i, (s, _c) in enumerate(self._gradient):
                        d = abs(float(s) - dragged_pos)
                        if d < best_d:
                            best_d = d
                            best_i = i
                    self.set_selected_index(best_i)
                return
        except Exception:
            pass

        super().mouseReleaseEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        """マウス移動時の処理。ハンドルをドラッグ移動させます。"""
        if self._drag_position is None:
            return

        try:
            stop = e.position().x() / max(1, float(self.width()))
            stop = max(0.0, min(1.0, float(stop)))

            _, color = self._gradient[self._drag_position]
            self._gradient[self._drag_position] = (stop, color)

            self._constrain_gradient()
            # ★ドラッグ中はソートしない（indexが暴れるため）
            self.gradientChanged.emit()
            self.update()

            # 選択はドラッグしているstopに追従
            if self._selected_index != self._drag_position:
                self._selected_index = self._drag_position
                self.selectedStopChanged.emit(int(self._drag_position))
        except Exception:
            pass

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        """ダブルクリック時の処理。

        - ハンドル上：色変更
        - ハンドル外：新規stop追加＋選択
        """
        n = self._find_stop_handle_for_event(e)
        if n is not None:
            self.set_selected_index(n)
            self.chooseColorAtPosition(n, self._gradient[n][1])
            return

        stop = max(0.0, min(1.0, e.position().x() / max(1.0, float(self.width()))))
        self.addStop(float(stop))

        # 追加したstopを選択（stopに最も近い位置）
        self._sort_gradient()
        best_i = 0
        best_d = 999.0
        for i, (s, _c) in enumerate(self._gradient):
            d = abs(float(s) - float(stop))
            if d < best_d:
                best_d = d
                best_i = i
        self.set_selected_index(best_i)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Delete/Backspace で選択中ストップを削除します（両端は削除不可）。"""
        try:
            if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                idx = self._selected_index
                if idx is None:
                    return

                if idx in self._end_stops:
                    # 両端は削除不可
                    return

                self.removeStopAtPosition(int(idx))

                # 削除後は近傍を選択
                if self._gradient:
                    new_idx = min(int(idx), len(self._gradient) - 1)
                    self.set_selected_index(new_idx)
                else:
                    self._selected_index = None
                    self.update()
                return
        except Exception:
            pass

        super().keyPressEvent(e)

    def removeStopAtPosition(self, n: int) -> None:
        """指定インデックスのストップポイントを削除します（両端は削除不可）。"""
        if n not in self._end_stops and 0 <= n < len(self._gradient):
            del self._gradient[n]

            # 選択の整合
            if self._selected_index is not None:
                if self._selected_index == n:
                    self._selected_index = min(n, len(self._gradient) - 1) if self._gradient else None
                elif self._selected_index > n:
                    self._selected_index -= 1

            self.gradientChanged.emit()
            self.update()

    def setAngle(self, angle: int) -> None:
        """グラデーションの角度を設定します。

        Args:
            angle (int): 角度。
        """
        self._angle = angle % 360
        self.gradientChanged.emit()
        self.update()

    def angle(self) -> int:
        """現在のグラデーション角度を取得します。"""
        return self._angle

    def _ensure_selected_index(self) -> None:
        """選択中インデックスを安全な値に矯正する。

        - グラデが空: None
        - グラデがある: 0..len-1 の範囲に丸める（基本は0）
        """
        if not self._gradient:
            self._selected_index = None
            return

        if self._selected_index is None:
            self._selected_index = 0
            return

        try:
            i: int = int(self._selected_index)
        except Exception:
            self._selected_index = 0
            return

        if i < 0:
            self._selected_index = 0
        elif i >= len(self._gradient):
            self._selected_index = len(self._gradient) - 1

    def _nearest_index_by_pos(self, pos: float) -> int:
        """指定pos(0..1)に最も近いstopのindexを返す。

        Args:
            pos (float): 0.0..1.0

        Returns:
            int: 最近傍stopのindex（最低0）
        """
        if not self._gradient:
            return 0

        best_i: int = 0
        best_d: float = 10**9
        p: float = float(pos)

        for i, (s, _c) in enumerate(self._gradient):
            d: float = abs(float(s) - p)
            if d < best_d:
                best_d = d
                best_i = i
        return best_i

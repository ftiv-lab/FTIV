from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from PySide6.QtWidgets import QApplication

from utils.error_reporter import ErrorNotifyState, report_unexpected_error

if TYPE_CHECKING:
    from ui.main_window import MainWindow
    from windows.image_window import ImageWindow

logger = logging.getLogger(__name__)


class LayoutActions:
    """
    画像の自動整列や配置計算を行うロジックを MainWindow から分離。
    """

    def __init__(self, mw: MainWindow) -> None:
        """
        Args:
            mw (MainWindow): MainWindow (ウィンドウリストへのアクセスに必要)
        """
        self.mw = mw
        self._err_state: ErrorNotifyState = ErrorNotifyState()

    def _get_all_image_windows(self) -> List[ImageWindow]:
        try:
            if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "image_windows"):
                return list(getattr(self.mw.window_manager, "image_windows", []))
            elif hasattr(self.mw, "image_windows"):
                return list(getattr(self.mw, "image_windows", []))
        except Exception:
            pass
        return []

    def pack_all_left_top(self, screen_index: int) -> None:
        """全画像を左上から詰めて配置する。"""
        images = self._get_all_image_windows()
        if not images:
            return

        # 画面情報の取得
        try:
            screens = QApplication.screens()
            if 0 <= screen_index < len(screens):
                screen_geo = screens[screen_index].geometry()
                start_x = screen_geo.x()
                start_y = screen_geo.y()
                # max_w = screen_geo.width() # 改行ロジックを入れるなら必要
            else:
                return  # 無効なスクリーン
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to get screen info for packing.", e, self._err_state)
            return

        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.beginMacro("Pack Left-Top")

        try:
            current_x = start_x + 10
            current_y = start_y + 10
            max_row_h = 0

            # ソートあったほうがいいかもしれないが、現状はリスト順

            for win in images:
                if win is None:
                    continue
                try:
                    w = win.width()
                    h = win.height()

                    # Undo記録付き移動
                    if hasattr(win, "set_undoable_geometry"):
                        win.set_undoable_geometry(current_x, current_y, w, h)
                    else:
                        win.move(current_x, current_y)

                    current_x += w + 10
                    max_row_h = max(max_row_h, h)

                    # 画面端での簡易折り返し（必要なら）
                    # if current_x + 200 > start_x + max_w: ...

                except Exception as e:
                    logger.warning(f"Failed to move image during pack: {e}")

        except Exception as e:
            report_unexpected_error(self.mw, "Error during Pack Left-Top logic.", e, self._err_state)
        finally:
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

    def pack_all_center(self, screen_index: int) -> None:
        """全画像を画面中央付近に集める（簡易実装）。"""
        images = self._get_all_image_windows()
        if not images:
            return

        try:
            screens = QApplication.screens()
            if 0 <= screen_index < len(screens):
                screen_geo = screens[screen_index].geometry()
                center_x = screen_geo.center().x()
                center_y = screen_geo.center().y()
            else:
                return
        except Exception:
            return

        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.beginMacro("Pack Center")

        try:
            # 簡易的に、中心座標にカスケードさせる
            offset = 0
            for win in images:
                if win is None:
                    continue
                try:
                    w = win.width()
                    h = win.height()

                    # 中心基準
                    new_x = center_x - (w // 2) + offset
                    new_y = center_y - (h // 2) + offset

                    if hasattr(win, "set_undoable_geometry"):
                        win.set_undoable_geometry(new_x, new_y, w, h)
                    else:
                        win.move(new_x, new_y)

                    offset += 20
                except Exception:
                    pass
        finally:
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

    def align_images_grid(self, columns: int, space: int, screen_index: int, preview_mode: bool = False) -> None:
        """
        全画像をグリッド状に整列する。

        Args:
            columns: 列数
            space: 間隔(px)
            screen_index: 対象モニタ
            preview_mode: TrueならUndoスタックを使わず直接 move する（ダイアログプレビュー用）
        """
        images = self._get_all_image_windows()
        if not images:
            return

        try:
            screens = QApplication.screens()
            if not (0 <= screen_index < len(screens)):
                return
            screen_geo = screens[screen_index].geometry()
            start_x = screen_geo.x() + 50
            start_y = screen_geo.y() + 50
        except Exception:
            return

        if not preview_mode and hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.beginMacro("Align Grid")

        try:
            current_col = 0

            # グリッド計算用の簡易ロジック
            # 行ごとの最大高さを保持してYを送るような高度なGridではなく、
            # 単純に固定グリッド、あるいは 左上詰めフローにするか
            # ここでは「左上から順に並べ、columns個で改行、高さは行内の最大」とする

            # まず全アイテムをリスト化してループ処理
            # 1行分溜めてから配置計算する方がきれいだが、
            # シンプルに current_x / current_y を更新していく

            x_cursor = start_x
            y_cursor = start_y
            row_max_h = 0

            for i, win in enumerate(images):
                if win is None:
                    continue

                w = win.width()
                h = win.height()

                # 配置実行
                if not preview_mode and hasattr(win, "set_undoable_geometry"):
                    win.set_undoable_geometry(x_cursor, y_cursor, w, h)
                else:
                    win.move(x_cursor, y_cursor)
                    # プレビュー中は position config も更新しておくとちらつき防止になるかも？
                    # ただし永続化はしない

                # 次の計算
                x_cursor += w + space
                row_max_h = max(row_max_h, h)
                current_col += 1

                if current_col >= columns:
                    # 改行
                    current_col = 0
                    x_cursor = start_x
                    y_cursor += row_max_h + space
                    row_max_h = 0

        except Exception as e:
            if not preview_mode:
                report_unexpected_error(self.mw, "Error aligning images.", e, self._err_state)
            else:
                logger.debug(f"Preview align error: {e}")

        finally:
            if not preview_mode and hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

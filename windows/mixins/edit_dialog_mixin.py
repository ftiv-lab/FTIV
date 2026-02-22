"""Mixin providing modeless TextInputDialog lifecycle management.

Provides unified dialog start, finish, cleanup, and Auto-Follow
(release / take-over) logic for both TextWindow and ConnectorLabel.

Assumptions on the host class (self):
    - self.text (str property)
    - self.update_text() method
    - self.set_undoable_property(name, value, updater) method
    - self.uuid (str attribute)
    - self.screen(), self.x(), self.y(), self.width(), self.height() (Qt)
"""

import logging
import traceback
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QDialog

if TYPE_CHECKING:

    class _EditDialogHost:
        """Type-only protocol for Mypy; never instantiated at runtime."""

        text: str
        uuid: str

        def update_text(self) -> None: ...
        def set_undoable_property(self, name: str, value: Any, updater: str) -> None: ...
        def screen(self) -> Any: ...
        def x(self) -> int: ...
        def y(self) -> int: ...
        def width(self) -> int: ...
        def height(self) -> int: ...

else:

    class _EditDialogHost:  # type: ignore[no-redef]
        """Runtime placeholder — no-op base."""


logger = logging.getLogger(__name__)


class EditDialogMixin(_EditDialogHost):
    """Modeless TextInputDialog lifecycle management for text-bearing widgets.

    Drop-in mixin that provides:
        - start_edit_dialog()        : Launch or re-activate the dialog
        - _on_edit_dialog_finished() : Handle accept / reject
        - _position_edit_dialog()    : Smart 4-direction placement
        - _release_edit_dialog()     : Auto-Follow: release ownership
        - _take_over_edit_dialog()   : Auto-Follow: take ownership
        - _cleanup_edit_dialog()     : closeEvent helper
    """

    # Sentinel defaults — overwritten per instance on first use
    _edit_dialog: Any = None
    _edit_original_text: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_edit_dialog(self) -> None:
        """Launch a modeless TextInputDialog, or activate if already open.

        The dialog runs in Persistent Mode: it only closes via
        explicit user actions (OK / Cancel / Esc / ×).
        """
        # Re-entrance guard
        if getattr(self, "_edit_dialog", None) is not None:
            try:
                self._edit_dialog.activateWindow()
                self._edit_dialog.raise_()
            except RuntimeError:
                self._edit_dialog = None
            return

        self._edit_original_text = self.text

        def _live_update(new_text: str) -> None:
            try:
                self.text = new_text
                self.update_text()
            except Exception as e:
                logger.error(f"Live update failed: {e}")

        try:
            # Lazy import to avoid circular dependency
            from ui.dialogs import TextInputDialog

            dialog = TextInputDialog(self.text, self, callback=_live_update)
            self._edit_dialog = dialog

            self._position_edit_dialog(dialog)

            dialog.finished.connect(self._on_edit_dialog_finished)
            dialog.show()
            dialog.activateWindow()

        except Exception as e:
            logger.error(f"Error starting edit dialog: {e}\n{traceback.format_exc()}")
            self._edit_dialog = None
            self.text = self._edit_original_text
            self.update_text()

    # ------------------------------------------------------------------
    # Dialog result handler
    # ------------------------------------------------------------------

    def _on_edit_dialog_finished(self, result: int) -> None:
        """Handle dialog accept/reject and commit or rollback text."""
        dialog = self._edit_dialog
        self._edit_dialog = None

        if dialog is None:
            return

        try:
            if result == QDialog.Accepted:
                final_text = dialog.get_text()
                original = self._edit_original_text
                # Reset to original first so Undo sees the correct "before"
                self.text = original
                if final_text != original:
                    self.set_undoable_property("text", final_text, "update_text")
                    logger.info(f"Text changed for {self.uuid}")
                else:
                    self.update_text()
            else:
                self.text = self._edit_original_text
                self.update_text()
        except RuntimeError:
            pass

        try:
            dialog.deleteLater()
        except RuntimeError:
            pass

    # ------------------------------------------------------------------
    # Smart positioning
    # ------------------------------------------------------------------

    def _position_edit_dialog(self, dialog: Any) -> None:
        """Place the dialog near the widget using saved pos or 4-direction layout."""
        screen = self.screen()
        if not screen:
            return

        screen_geo = screen.availableGeometry()
        dlg_w = dialog.width()
        dlg_h = dialog.height()

        # Prefer saved position if it is still on-screen
        saved_pos = dialog.get_saved_position()
        if saved_pos is not None:
            sx, sy = saved_pos
            if (
                screen_geo.left() <= sx <= screen_geo.right() - 50
                and screen_geo.top() <= sy <= screen_geo.bottom() - 50
            ):
                dialog.move(sx, sy)
                return

        # 4-direction candidates (right → left → below → above)
        padding = 20
        candidates = [
            (self.x() + self.width() + padding, self.y()),
            (self.x() - dlg_w - padding, self.y()),
            (self.x(), self.y() + self.height() + padding),
            (self.x(), self.y() - dlg_h - padding),
        ]

        for cx, cy in candidates:
            if (
                screen_geo.left() <= cx
                and cx + dlg_w <= screen_geo.right()
                and screen_geo.top() <= cy
                and cy + dlg_h <= screen_geo.bottom()
            ):
                dialog.move(cx, cy)
                return

        # Fallback: clamp to screen
        target_x = min(self.x() + self.width() + padding, screen_geo.right() - dlg_w)
        target_x = max(screen_geo.left(), target_x)
        target_y = max(screen_geo.top(), min(self.y(), screen_geo.bottom() - dlg_h))
        dialog.move(target_x, target_y)

    # ------------------------------------------------------------------
    # Auto-Follow helpers
    # ------------------------------------------------------------------

    def _release_edit_dialog(self) -> Any:
        """Auto-Follow: release dialog ownership with auto-commit.

        Returns:
            The TextInputDialog instance if released, None otherwise.
        """
        dialog = self._edit_dialog
        if dialog is None:
            return None

        self._edit_dialog = None

        # Auto-commit current edits as a single Undo entry
        try:
            final_text = dialog.get_text()
            original = self._edit_original_text
            self.text = original
            if final_text != original:
                self.set_undoable_property("text", final_text, "update_text")
                logger.info(f"Auto-commit text for {self.uuid}")
            else:
                self.update_text()
        except RuntimeError:
            pass

        # Disconnect finished signal from this widget
        try:
            dialog.finished.disconnect(self._on_edit_dialog_finished)
        except (RuntimeError, TypeError):
            pass

        return dialog

    def _take_over_edit_dialog(self, dialog: Any) -> None:
        """Auto-Follow: take ownership of a dialog from another widget."""
        self._edit_original_text = self.text
        self._edit_dialog = dialog

        def _live_update(new_text: str) -> None:
            try:
                self.text = new_text
                self.update_text()
            except Exception as e:
                logger.error(f"Live update failed: {e}")

        dialog.switch_target(self.text, _live_update)
        dialog.finished.connect(self._on_edit_dialog_finished)

    # ------------------------------------------------------------------
    # closeEvent helper
    # ------------------------------------------------------------------

    def _cleanup_edit_dialog(self) -> None:
        """Disconnect + reject any open edit dialog. Call from closeEvent."""
        if getattr(self, "_edit_dialog", None) is None:
            return

        # Disconnect first to prevent _on_edit_dialog_finished from
        # calling update_text() on a dying widget.
        try:
            self._edit_dialog.finished.disconnect(self._on_edit_dialog_finished)
        except (RuntimeError, TypeError):
            pass
        try:
            self._edit_dialog.reject()
        except RuntimeError:
            pass
        self._edit_dialog = None

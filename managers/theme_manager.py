# managers/theme_manager.py

import logging
import os
from typing import Any, Dict

from PySide6.QtWidgets import QApplication

# Logger
logger = logging.getLogger(__name__)

# Default Dark Theme Tokens
# TODO: Move to json or separate config file in Phase 2
DARK_THEME: Dict[str, str] = {
    "@bg_primary": "#2b2b2b",  # Legacy Gray (User Requested)
    "@bg_secondary": "#323232",  # Legacy Surface
    "@surface": "#333333",  # Standard Surface
    "@border": "#404040",  # Darker Border
    "@accent_primary": "#007acc",
    "@accent_hover": "#0098ff",
    "@text_primary": "#e0e0e0",  # Standard text brightness
    "@text_dim": "#aaaaaa",
    "@danger": "#d32f2f",
}


class ThemeManager:
    """
    Global Style System Manager.
    Handles loading QSS templates, injecting design tokens, and applying styles to the QApplication.
    """

    def __init__(self, main_window: Any) -> None:
        self.main_window = main_window
        # MainWindow _init_paths must be called before this
        self.base_dir = getattr(main_window, "base_directory", ".")
        self.template_path = os.path.join(self.base_dir, "assets", "style", "theme.qss.template")

    def apply_theme(self) -> None:
        """Load template, replace tokens, and apply to QApplication."""
        try:
            if not os.path.exists(self.template_path):
                logger.warning(f"Theme template not found at {self.template_path}")
                return

            with open(self.template_path, "r", encoding="utf-8") as f:
                qss_template = f.read()

            # Pre-process: Replace Design Tokens
            final_qss = qss_template
            for token, value in DARK_THEME.items():
                final_qss = final_qss.replace(token, value)

            # Apply Global
            app = QApplication.instance()
            if app:
                app.setStyleSheet(final_qss)
                logger.info("Global theme applied successfully.")
            else:
                logger.warning("No QApplication instance found to apply theme.")

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}", exc_info=True)

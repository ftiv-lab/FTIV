import logging
import os
from typing import Dict

from PySide6.QtWidgets import QApplication

from utils.paths import get_base_dir

logger = logging.getLogger(__name__)


class ThemeManager:
    """アプリケーション全体のスタイル(QSS)を管理するクラス。

    QSSの変数機能が弱いため、Python側でプリプロセス（変数置換）を行ってからQSSを適用する。
    将来的なテーマ切り替え（ダーク/ライト）もここで行う。
    """

    # デフォルトの変数パレット (Design System)
    DEFAULT_PALETTE: Dict[str, str] = {
        # Backgrounds
        "@bg_primary": "#f0f0f0",  # Main Window, Tabs (inactive)
        "@bg_secondary": "#ffffff",  # Inputs, Active Tabs, Property Panel
        "@surface": "#f8f9fa",  # Buttons (normal)
        # Text
        "@text_primary": "#333333",
        "@text_dim": "#666666",
        # Accents
        "@accent_primary": "#3a6ea5",  # Main Brand Color
        "@accent_hover": "#2a5482",
        "@accent_light": "#eef6fc",  # Secondary Action BG
        # Status / Functional
        "@danger": "#d9534f",
        "@border": "#cccccc",
    }

    @staticmethod
    def load_theme(app: QApplication, theme_name: str = "default") -> None:
        """指定されたテーマをロードしてアプリに適用する。

        Args:
            app (QApplication): 現在のアプリインスタンス
            theme_name (str): 未来の拡張用 (現在は無視)
        """
        try:
            base_dir = get_base_dir()
            template_path = os.path.join(base_dir, "assets", "style", "theme.qss.template")

            if not os.path.exists(template_path):
                logger.warning(f"Theme template not found: {template_path}")
                return

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # 変数置換 (Preprocessor)
            qss_content = ThemeManager._process_template(template_content)

            # 適用
            app.setStyleSheet(qss_content)
            logger.info("Global theme applied successfully.")

        except Exception as e:
            logger.error(f"Failed to load theme: {e}")

    @staticmethod
    def _process_template(content: str) -> str:
        """テンプレート内の @variable を実際のカラーコードに置換する。"""
        processed = content
        for key, value in ThemeManager.DEFAULT_PALETTE.items():
            # キーそのものを置換 (@bg_primary -> #f0f0f0)
            processed = processed.replace(key, value)
        return processed

    @staticmethod
    def reload_theme(app: QApplication) -> None:
        """開発用：テーマをホットリロードする。"""
        logger.info("Hot-reloading theme...")
        ThemeManager.load_theme(app)

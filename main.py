import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow

# 堅牢化したパス解決 (ログ設定前にも使えるように)
# 翻訳システム (言語設定のため)
from utils.translator import set_lang


def run_app():
    """アプリケーションの起動エントリーポイント。"""

    # 1. アプリケーションインスタンス作成 (GUI表示のために必要)
    app = QApplication(sys.argv)

    try:
        # 2. ロギング設定
        from utils.logger import setup_logging

        setup_logging()

        # 3. 言語設定
        set_lang("jp")

        # 3.5 Runtime Self-Diagnostic (Config Guardian)
        from managers.config_guardian import ConfigGuardian
        from utils.paths import get_base_dir

        guardian = ConfigGuardian(get_base_dir())
        if guardian.validate_all():
            report = guardian.get_report_text()
            # 深刻な修復が行われた場合はユーザーに通知
            QMessageBox.warning(
                None,
                "Configuration Auto-Repaired",
                f"Some settings were corrupted and have been reset to defaults:\n\n{report}",
            )

        # 4. メインウィンドウ起動
        _ = MainWindow()

        # 5. アプリ実行
        sys.exit(app.exec())

    except Exception:
        # 予期せぬ起動エラーをキャッチして表示
        # (コンソールが無いexe環境で重要)
        err_msg = traceback.format_exc()
        try:
            # ログにも出す
            import logging

            logging.getLogger("root").critical("Failed to start app:\n%s", err_msg)
        except Exception:
            pass

        QMessageBox.critical(None, "Critical Error", f"Failed to start application:\n\n{err_msg}")
        sys.exit(1)


if __name__ == "__main__":
    run_app()

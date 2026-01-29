# utils/logger.py
import logging
import os
import platform
import sys
import traceback
from datetime import datetime
from typing import Any

from PySide6.QtWidgets import QMessageBox

from utils.paths import get_base_dir
from utils.translator import tr


def _get_log_dir() -> str:
    """ログ保存先（base_directory/logs）を返す。"""
    return os.path.join(get_base_dir(), "logs")


# ログディレクトリの設定（MainWindow.open_log_folder と一致させる）
LOG_DIR = _get_log_dir()
os.makedirs(LOG_DIR, exist_ok=True)

# ログファイル名の生成 (例: logs/ftiv_20251218.log)
log_filename = os.path.join(LOG_DIR, f"ftiv_{datetime.now().strftime('%Y%m%d')}.log")


def setup_logging() -> None:
    """
    ロギングシステムの初期化を行います。
    ファイルとコンソールの両方にログを出力するように設定します。
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # INFOに戻す

    # 二重初期化でハンドラが重複しないようにする（安全策）
    if logger.handlers:
        logging.info("--- Logging already initialized ---")
        return

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # ファイル出力ハンドラ
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # コンソール出力ハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logging.info("--- Logging Started ---")
    log_diagnostics()


def log_diagnostics() -> None:
    """実行環境の診断情報をログに出力します。"""
    logging.info(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    logging.info(f"Python: {sys.version}")
    logging.info(f"Executable Path: {sys.executable}")

    try:
        from utils.version import APP_VERSION

        logging.info(f"App: {APP_VERSION.name} {APP_VERSION.version} (data_format={APP_VERSION.data_format_version})")
    except Exception:
        pass

    try:
        # edition は開発用に固定でもOK。将来差し替えやすいようにここで取得。
        from utils.edition import get_edition

        ed = get_edition()
        logging.info(f"Edition: {ed.value}")
    except Exception:
        pass


def handle_exception(exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
    """
    未捕捉の例外をキャッチしてログに記録し、ユーザーに通知します。
    sys.excepthook にセットして使用します。
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.critical("Uncaught Exception:\n%s", error_msg)

    from PySide6.QtWidgets import QApplication

    if QApplication.instance():
        QMessageBox.critical(
            None,
            tr("msg_error"),
            f"A critical error occurred. Please check the log file:\n{log_filename}\n\n{exc_value}",
        )


# 未捕捉の例外ハンドラを登録
sys.excepthook = handle_exception


def get_logger(name: str) -> logging.Logger:
    """各モジュール用のロガーを取得します。"""
    return logging.getLogger(name)

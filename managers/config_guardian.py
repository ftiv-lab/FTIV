import json
import logging
import os
import shutil

logger = logging.getLogger(__name__)


class ConfigGuardian:
    """
    アプリケーション起動時の自己診断・修復を行うクラス。
    設定ファイルの破損や欠損を検知し、デフォルト値で復旧させた上で警告を出す。
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.json_dir = os.path.join(base_dir, "json")
        self.settings_path = os.path.join(self.json_dir, "settings.json")
        self.reports = []

    def validate_all(self) -> bool:
        """
        全ての診断を実行する。
        重大な修復が行われた場合は True を返す。
        """
        self.reports = []
        restored = False

        if not os.path.exists(self.json_dir):
            os.makedirs(self.json_dir, exist_ok=True)
            self._report("INFO", f"Created missing json directory: {self.json_dir}")

        if self._check_settings_json():
            restored = True

        # 将来的なチェック項目追加場所
        # if self._check_assets(): ...

        return restored

    def _check_settings_json(self) -> bool:
        """settings.json の整合性チェック"""
        if not os.path.exists(self.settings_path):
            self._report("INFO", "settings.json not found. Creating default.")
            self._create_default_settings()
            return False

        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 必須キーの簡易チェック
            required_keys = ["app_settings", "overlay_settings"]
            missing = [k for k in required_keys if k not in data]

            if missing:
                self._report("ERROR", f"settings.json is missing keys: {missing}. Backing up and resetting.")
                self._backup_and_reset(self.settings_path)
                return True

        except json.JSONDecodeError:
            self._report("ERROR", "settings.json is corrupted (JSON decode error). Backing up and resetting.")
            self._backup_and_reset(self.settings_path)
            return True
        except Exception as e:
            self._report("ERROR", f"Unexpected error reading settings.json: {e}")
            return False

        return False

    def _create_default_settings(self):
        default_data = {
            "app_settings": {"theme": "dark", "language": "ja", "font_family": "Meiryo UI", "ui_scale": 1.0},
            "overlay_settings": {"opacity": 1.0},
        }
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)

    def _backup_and_reset(self, target_path: str):
        backup_path = target_path + ".bak"
        if os.path.exists(target_path):
            shutil.copy2(target_path, backup_path)
            self._report("INFO", f"Backed up corrupted file to {backup_path}")

        self._create_default_settings()

    def _report(self, level: str, message: str):
        entry = f"[{level}] {message}"
        self.reports.append(entry)
        logger.info(f"Guardian: {message}")

    def get_report_text(self) -> str:
        return "\n".join(self.reports)

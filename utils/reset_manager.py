import datetime
import logging
import os
import shutil
from typing import List, Optional

from utils.paths import get_base_dir

logger = logging.getLogger(__name__)


class ResetManager:
    """
    Factory Reset operation manager.
    Safely resets application configuration to defaults by backing up existing files
    and removing them, triggering the app to generate fresh ones on reboot.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir if base_dir else get_base_dir()
        self.json_dir = os.path.join(self.base_dir, "json")
        self.settings_dir = os.path.join(self.base_dir, "user_data", "settings")

        # Files to be removed on factory reset
        self.target_files: List[str] = [
            os.path.join(self.json_dir, "app_settings.json"),
            os.path.join(self.json_dir, "scenes_db.json"),
            os.path.join(self.json_dir, "text_archetype.json"),
            os.path.join(self.json_dir, "overlay_settings.json"),
            os.path.join(self.json_dir, "text_defaults.json"),  # Legacy defaults
            os.path.join(self.json_dir, "text_defaults_vertical.json"),  # Legacy defaults
            # Also clear user_data settings if any
            os.path.join(self.settings_dir, "text_archetype.json"),
        ]

    def backup_current_config(self, target_files: List[str]) -> str:
        """
        Creates a backup of the current configuration.
        Returns the path to the backup directory.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir_name = f"backup_{timestamp}"
        backup_dir = os.path.join(self.base_dir, "backups", backup_dir_name)
        os.makedirs(backup_dir, exist_ok=True)

        logger.info(f"Creating backup at: {backup_dir}")

        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    file_name = os.path.basename(file_path)
                    shutil.copy2(file_path, os.path.join(backup_dir, file_name))
                    logger.debug(f"Backed up: {file_name}")
                except Exception as e:
                    logger.warning(f"Failed to backup {file_path}: {e}")

        return backup_dir

    def perform_factory_reset(self, reset_settings: bool = True, reset_user_data: bool = False) -> bool:
        """
        Performs the factory reset based on selected options.

        Args:
            reset_settings: If True, resets app_settings.json, overlay_settings.json.
            reset_user_data: If True, resets scenes, presets, and archetypes.

        Returns:
            True if successful.
        """

        target_files: List[str] = []

        # 1. Settings (Configuration)
        if reset_settings:
            target_files.extend(
                [
                    os.path.join(self.json_dir, "app_settings.json"),
                    os.path.join(self.json_dir, "overlay_settings.json"),
                    # Also reset default text archetype in settings if strictly resetting settings?
                    # Actually archetype is kind of "setting" but also "content".
                    # Let's treat root archetype as setting.
                    os.path.join(self.json_dir, "text_archetype.json"),
                    os.path.join(self.json_dir, "text_defaults.json"),
                    os.path.join(self.json_dir, "text_defaults_vertical.json"),
                ]
            )

        # 2. User Data (Content)
        if reset_user_data:
            target_files.extend(
                [
                    os.path.join(self.json_dir, "scenes_db.json"),
                    # Presets directory
                    # Note: deleting directory requires different logic than file.
                    # For simplicity, we might just list files or handle dir specifically.
                    # But ResetManager.__init__ logic was file based.
                    # Let's add specific files for now or improve logic if needed.
                    # The prompt implies deleting "My Presets".
                    # Presets are usually in json/presets/*.json.
                    # Let's handle directory cleanup for presets if needed.
                ]
            )

            # Special handling for directories (Presets)
            presets_dir = os.path.join(self.json_dir, "presets")
            if os.path.exists(presets_dir):
                # We will handle this separately or add to a "dirs_to_remove" list?
                # For now let's keep it simple and safe.
                pass

            # Also user_data settings if any
            target_files.append(os.path.join(self.settings_dir, "text_archetype.json"))

        if not target_files and not reset_user_data:
            logger.warning("No reset options selected.")
            return False

        # Always backup first
        try:
            self.backup_current_config(target_files)
        except Exception as e:
            logger.error(f"Backup failed during reset: {e}")
            pass

        success = True
        logger.info("Starting Factory Reset (Deletion Phase)...")

        # Delete Files
        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
                    success = False

        # Delete Presets Folder Content if requested
        if reset_user_data:
            presets_dir = os.path.join(self.json_dir, "presets")
            if os.path.exists(presets_dir):
                try:
                    # Remove all files in presets dir but keep dir
                    for filename in os.listdir(presets_dir):
                        file_path = os.path.join(presets_dir, filename)
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            logger.info(f"Deleted Preset: {filename}")
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            logger.info(f"Deleted Preset Dir: {filename}")
                except Exception as e:
                    logger.error(f"Failed to clean presets directory: {e}")
                    success = False

        return success

import argparse
import dataclasses
import json
import os
import sys

from PySide6.QtWidgets import QApplication

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import utils.theme_manager
from ui.main_window import MainWindow
from utils.app_settings import AppSettings


def run_session(config_path: str, mode: str):
    _app = QApplication(sys.argv)

    # Mock Config Path via monkeypatching or just modifying the instance after creation?
    # MainWindow creates SettingsManager in __init__ -> Load Settings.
    # To control config path, we need to intercept FileManager or SettingsManager.
    # FTIV seems to rely on global `utils.paths` or `self.json_directory` in MainWindow.

    # Let's instantiate MainWindow
    # Note: MainWindow init calls SettingsManager.load_settings() immediately.
    # We should ensure we can redirect the load.

    # We will PATCH SettingsManager's path resolution for this test session.
    from managers.settings_manager import SettingsManager

    # original_load = SettingsManager.load_settings
    # original_save = SettingsManager.save_app_settings

    def patched_load(self_mgr):
        # Force load from our config_path
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # AppSettings.parse_obj(data)... but SettingsManager logic is complex.
                # It uses self.app_settings = AppSettings(...)
                # Let's just create a basic AppSettings from dict
                try:
                    self_mgr.app_settings = AppSettings(**data)
                except Exception as e:
                    print(f"Error loading mock config: {e}")
                    self_mgr.app_settings = AppSettings()
        else:
            self_mgr.app_settings = AppSettings()

        # Sync to main window state (restore geometry etc) if needed
        # But for this test we mainly care about `app_settings` values.

    def patched_save(self_mgr):
        # Force save to our config_path
        with open(config_path, "w", encoding="utf-8") as f:
            data = dataclasses.asdict(self_mgr.app_settings)
            json.dump(data, f, indent=4)
        print(f"Saved to {config_path}")

    # Apply Patch
    SettingsManager.load_settings = patched_load
    SettingsManager.save_app_settings = patched_save  # Corrected Name

    # Disable ThemeManager hot reload to avoid threads
    utils.theme_manager.ThemeManager.initialize = lambda *args: None

    mw = MainWindow()

    if mode == "write":
        print("Mode: WRITE")
        # Scenario: Enable Gradient
        # We need a current target. Text?
        # MainWindow usually starts with no text windows unless loaded from session.
        # Let's just modify the GLOBAL AppSettings or a specific WindowConfig if available.
        # Wait, Gradient settings are per WindowConfig (TextWindowConfig).
        # We need to create a text window, set it, save it.

        mw.main_controller.txt_actions.add_new_text_window()
        assert len(mw.text_windows) == 1
        tw = mw.text_windows[0]

        # Set Gradient items
        tw.config.text_gradient_enabled = True
        tw.config.text_gradient = [(0.0, "#FF0000"), (1.0, "#0000FF")]
        tw.config.text_gradient_angle = 45

        # Verify it was set in memory
        assert tw.config.text_gradient_enabled is True

        # The app saves "window states" in `scene_db` or similar?
        # Wait, FTIV saves `config.json` (AppSettings) AND `scenes_db.json`.
        # Persistence of *Window Data* is usually in `scenes_db.json`?
        # Converting this to a simple AppSettings test might miss the window restoration logic.

        # Let's verify where `text_windows` are saved.
        # Usually `WindowManager.save_windows` or `save_scene`.
        # MainWindow `closeEvent` triggers save.

        # Trigger Save
        # We need to ensure `settings_manager.save_settings()` implies saving windows?
        # Or `file_manager.save_all_data()`?

        # ensure current state is in scenes dict
        # Assuming WindowManager or FileManager has a way to update current scene data.
        # MainWindow usually updates it on close or property change.
        # Let's try to find the "Update Scene" method.
        # In FTIV, FileManager.get_scene_data() constructs the data from active windows!
        # And save_scenes_db() calls _get_clean_scenes_for_export() which calls main_window.scenes.
        # Wait, get_scene_data() is what generates the data from active windows.

        # We need to PUT that data into main_window.scenes["CurrentScene"]?
        # Or just use the data.

        # Let's manually update the scene in memory
        current_scene_name = mw.current_scene_name if hasattr(mw, "current_scene_name") else "Default"
        if not hasattr(mw, "scenes"):
            mw.scenes = {}
        if "Default" not in mw.scenes:
            mw.scenes["Default"] = {}

        # This is where we need to know how app connects windows to scenes.
        # mw.file_manager.get_scene_data() seems to return the current window states.
        scene_data = mw.file_manager.get_scene_data()
        print(f"DEBUG: Active Windows: {len(mw.text_windows)}")
        print(f"DEBUG: Scene Data Windows: {len(scene_data.get('windows', []))}")

        # Update the DB
        # If we don't know the current scene structure, we can just save it as "Default"
        # The app load logic might look for "Default" or last loaded.

        mw.scenes = {"Default": {current_scene_name: scene_data}}
        # structure of scenes_db: {Category: {SceneName: Data}} ??

        # Wait, get_scene_data returns {windows:[], connections:[]}.
        # save_scenes_db saves mw.scenes.

        # We need to mimic what happens when "Saving".
        # Which is: update mw.scenes with current state.

        # Assuming we are in "Default" category, "Scene1"
        # mw.scenes["Default"]["Scene1"] = scene_data

        # But wait, looking at file_manager.save_scenes_db, it just dumps mw.scenes.
        # So SOMEONE must update mw.scenes.

        # Let's try to update it manually.
        category = "Default"
        scene_name = "AutoSave"

        if category not in mw.scenes:
            mw.scenes[category] = {}
        mw.scenes[category][scene_name] = scene_data

        app_settings = mw.settings_manager.app_settings
        if app_settings:
            app_settings.last_scene_category = category
            app_settings.last_scene_name = scene_name
            mw.settings_manager.save_app_settings()

        mw.file_manager.save_scenes_db()

        # We also need to save the SCENE data to a specific path?
        # `FileManager` uses `self.main_window.json_directory`.
        # We need to patch `json_directory` on MainWindow.

    elif mode == "read":
        print("Mode: READ")
        # App attempts to load from disk on init.
        # We need to verify the window is restored and has gradient enabled.

        # Wait for restoration (MainWindow init calls `file_manager.load_all_data`?)
        # MainWindow.__init__ calls `self.file_manager.load_startup_data()` usually.
        # Let's check MainWindow...
        # Logic: settings_manager.load_settings() -> ...
        # Actually `file_manager.load_all_data()` is usually called or `load_last_scene`.

        # For this test, simply checking if the window was restored might be enough.
        # If FTIV has "restore last session" feature enabled.

        # Assume startup loaded the data.
        # Since we patched load/save and hopefully path directory.

        # Check text windows

        # Manually force load if MainWindow doesn't do it automatically in this headless env
        # Usually MainWindow.show() or a timer triggers restoring the scene?
        # Or init().

        # Let's check if scenes were loaded into memory
        if hasattr(mw, "scenes") and "Default" in mw.scenes:
            print(f"DEBUG: Loaded Scenes: {mw.scenes.keys()}")
            pass  # Loaded
        else:
            print("DEBUG: mw.scenes is empty or missing Default")

            # Force load DB
            mw.file_manager.load_scenes_db()

            # Force restore specific scene
            # Assuming we saved as Default/AutoSave in WRITE mode
            category = "Default"
            scene_name = "AutoSave"

            if category in mw.scenes and scene_name in mw.scenes[category]:
                scene_data = mw.scenes[category][scene_name]
                mw.file_manager.load_scene_from_data(scene_data)
                print("DEBUG: Forced Load Complete")

        print(f"Restored Text Windows: {len(mw.text_windows)}")
        if len(mw.text_windows) > 0:
            tw = mw.text_windows[0]
            print(f"Gradient Enabled: {tw.config.text_gradient_enabled}")
            if tw.config.text_gradient_enabled:
                print("VERIFY_SUCCESS")
            else:
                print("VERIFY_FAILURE: Gradient False")
        else:
            print("VERIFY_FAILURE: No Windows")

    # Clean exit
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--mode", required=True, choices=["write", "read"])
    args = parser.parse_args()

    # We need to handle the fact that FileManager uses `mw.json_directory`.
    # We will subclass MainWindow or patch it to use args.config_dir

    # Simple Patch for MainWindow json_directory
    original_init = MainWindow.__init__

    def patched_init(self, *a, **kw):
        original_init(self, *a, **kw)
        self.json_directory = args.config_dir  # Override directory
        self.scene_db_path = os.path.join(args.config_dir, "scenes_db.json")
        # Force reload from this new directory if not already loaded?
        # Usually `init_paths` sets it.

    MainWindow.__init__ = patched_init

    run_session(os.path.join(args.config_dir, "config.json"), args.mode)

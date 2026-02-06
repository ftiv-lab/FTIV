# Phase 6: Reliability & Safety Net Implementation Plan

## Goal Description
Implement **Persistence Assurance Tests** and a **Factory Reset (Safety Net)** feature.
Ensure the application is robust against restart cycles and user misconfiguration.

## User Review Required
No new visuals until Reset UI. Technical approach for tests uses `subprocess`.

## Proposed Changes

### 1. Persistence Assurance (E2E Tests)
Create `tests/test_e2e_persistence.py`.
**Strategy**: "Process Reincarnation"
1.  **Setup**: Create a temporary config environment.
2.  **Process 1**: Launch App (Headless/Scripted if possible, or minimal UI).
    *   Write specific settings (e.g., set `text_gradient_enabled = True`).
    *   Save & Exit.
3.  **Process 2**: Launch App again pointing to same config.
    *   Read settings.
    *   Assert `text_gradient_enabled` is True.
4.  **Teardown**: Cleanup temp config.

*   **Implementation**: Use `subprocess` to call `main.py`.
*   *Note*: Since `main.py` is a GUI app, we might need a "test mode" argument or a dedicated test script that imports `main` but runs specific setup/teardown logic, OR we rely on writing config files directly and just checking if the app loads them correctly.
*   *Better Approach*: Use `SettingsManager` and `WindowManager` purely for the test without full GUI launch for the "Logic Persistence", AND a lightweight GUI test for "Visual Persistence".
*   *Agreed Approach*: Since we want to test "App Restart", we will simulate the behavior by creating a script that acts as the app session.

### 2. Factory Reset Logic
Refactor `scripts/reset_defaults.py`.
*   Create `utils/reset_manager.py`.
*   Class `ResetManager`:
    *   `backup_current_config()`: Copy `config.json` to `.bak`.
    *   `perform_factory_reset()`: Delete config, branding, themes, etc.
    *   `request_restart()`: (Optional) Signal app to restart.

### 3. Factory Reset UI (Smart Reset)
*   Modify `ui/tabs/general_tab.py`:
    *   Add "Danger Zone" GroupBox at bottom.
    *   Add "App Initialization" Button.
*   Update `ui/reset_confirm_dialog.py`:
    *   Add Checkbox: "Reset Settings" (Default: ON).
    *   Add Checkbox: "Delete Presets & Scenes" (Default: OFF).
    *   Pass selection flags to `ResetManager`.

## Verification Plan

### Automated Tests
*   `tests/test_e2e_persistence.py`: Verify settings survive restart.
*   `tests/test_reset.py`: Verify `ResetManager` correctly backs up and deletes files.

### Manual Verification
1.  **Reset Flow**: Change settings -> Click Reset -> App Restarts (or closes) -> Reopen -> Settings are default.
2.  **Backup Check**: Verify `.bak` file exists after reset.

### 4. Spacing UI Refinement
Refining terminology and defaults for text spacing settings to be cleaner and more accurate.

#### [MODIFY] [spacing_settings.py](file:///O:/Tkinter/FTIV/models/spacing_settings.py)
- Change default line spacing from 0.2 to 0.0

#### [MODIFY] [dialogs.py](file:///O:/Tkinter/FTIV/ui/dialogs.py)
- Update `TextSpacingDialog` labels to use new neutral keys
- Remove legacy " (Vertical)" suffix logic

#### [MODIFY] [text_tab.py](file:///O:/Tkinter/FTIV/ui/tabs/text_tab.py)
- Update "Toggle Vertical" button to "Switch Orientation"

#### [MODIFY] [jp.json](file:///O:/Tkinter/FTIV/utils/locales/jp.json)
- Add/Update spacing and orientation related keys

#### [MODIFY] [en.json](file:///O:/Tkinter/FTIV/utils/locales/en.json)
- Add/Update spacing and orientation related keys


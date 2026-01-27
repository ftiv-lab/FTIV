# Phase 11 Retry: Incremental User Interaction & Command Flow Decoupling

## Goal Description
Decouple `TextTab`, `ImageTab`, and `SceneTab` from `MainWindow` by routing user actions directly to `MainController` and its specialized Action classes. This reduces `MainWindow` complexity and enforces a cleaner MVC/Controller pattern.
**Strategy**: Incremental migration. We will first enable direct access, then migrate one tab at a time, protecting the application from "mass change" regressions.

## User Review Required
> [!IMPORTANT]
> This plan changes the initialization order of `MainWindow`. `MainController` will be initialized **before** `setup_ui()`. This is necessary for Tabs to access the controller during their construction.

## Proposed Changes

### 1. MainController Enhancement and Initialization
#### [MODIFY] [main_controller.py](file:///o:/Tkinter用/FTIV/ui/controllers/main_controller.py)
- Add property accessors for `txt_actions`, `img_actions`, `conn_actions`, and `bulk_manager`.
- These properties will delegate to `self.view.txt_actions`, etc. ensuring loose coupling but easy access.

#### [MODIFY] [main_window.py](file:///o:/Tkinter用/FTIV/ui/main_window.py)
- Move `MainController` initialization (lines 123-125) to **before** `setup_ui()` (line 105).
- Ensure `MainController` is ready to be used by Tabs during their `_setup_ui` calls.

### 2. Tab Migration (Incremental)
#### [MODIFY] [image_tab.py](file:///o:/Tkinter用/FTIV/ui/tabs/image_tab.py)
- Update signal connections to use `self.mw.main_controller.image_actions.*` instead of `self.mw.*` wrappers.
- Update bulk references to `self.mw.main_controller.bulk_manager.*`.

#### [MODIFY] [text_tab.py](file:///o:/Tkinter用/FTIV/ui/tabs/text_tab.py)
- Update signal connections to use `self.mw.main_controller.txt_actions.*`.
- Update bulk references to `self.mw.main_controller.bulk_manager.*`.

#### [MODIFY] [general_tab.py](file:///o:/Tkinter用/FTIV/ui/tabs/general_tab.py)
- Update signal connections to use `self.mw.main_controller.bulk_manager.*`.

#### [MODIFY] [scene_tab.py](file:///o:/Tkinter用/FTIV/ui/tabs/scene_tab.py)
- Update signal connections to use `self.mw.main_controller.scene_actions.*` and `connector_actions.*`.

### 3. Cleanup (Final Step)
#### [MODIFY] [main_window.py](file:///o:/Tkinter用/FTIV/ui/main_window.py)
- **Only after Verification**: Delete the ~50 wrapper methods (e.g., `_txt_hide_other_text_windows`, `add_image`) that are no longer used by any tab.

## Verification Plan

### Automated Tests
- Run `pytest` after Step 1 (Init Order Change) to ensure no regressions.
- Run `pytest` after each Tab migration.

### Manual Verification
- **Startup Check**: Launch app after Step 1 to ensure no "NoneType" errors.
- **Tab Functionality**:
    - **ImageTab**: Test Add Image, Flip, Rotate, Show/Hide All.
    - **TextTab**: Test Add Text, Bulk Style, Layout Actions.
    - **SceneTab**: Test Connector creation/deletion.

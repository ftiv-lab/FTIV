# Post-Refactoring Fix Report

## Issues Addressed
1.  **AttributeError: toggle_property_panel**
    - `MainWindow.toggle_property_panel` was removed but Tabs still called it.
    - **Fix**: Implemented `MainController.toggle_property_panel` and updated all tabs to use it.
2.  **AttributeError: main_controller**
    - `MainController` was initialized *after* UI setup, causing tabs to fail during their init.
    - **Fix**: Moved `MainController` initialization *before* `setup_ui()`.
3.  **AttributeError: show_all_everything / add_image / etc.**
    - `MainWindow` wrappers were removed but `GeneralTab` and others still called them.
    - **Fix**:
        - Updated `GeneralTab` to use `MainController.bulk_manager` for show/hide all.
        - Implemented missing `toggle_image_click_through` in `BulkOperationManager`.
        - Implemented missing `add_new_image` in `ImageActions`.
        - Updated `TextTab` to use `window_manager.add_text_window`.
        - Updated `ImageTab` to use `MainController.image_actions.add_new_image`.
        - Fixed `WindowManager` internal signal connection for `add_image` to point to `ImageActions`.

4.  **AttributeError: add_text_window (in subtabs) / add_new_scene / etc.**
    - User reported error in `TextTab` subtab initialization.
    - Also found missing scene/category methods in `SceneTab`.
    - **Fix**:
        - Replaced `add_text_window` in `TextTab` with `window_manager.add_text_window`.
        - Implemented `SceneActions` class to handle `add_new_scene`, `add_new_category`, `delete_selected_item`, etc.
        - Connected `SceneTab` buttons to `MainController.scene_actions`.
        - Added `close_all_image_windows` to `BulkOperationManager` and connected `SceneTab` to it.

5.  **AttributeError: TextActions.open_style_gallery_selected**
    - User reported error when loading `TextTab` subtab.
    - **Fix**: Implemented `open_style_gallery_selected` in `TextActions` class.

6.  **AttributeError: TextActions.show_all_text_windows**
    - User reported error when loading `TextTab` subtab (visibility).
    - **Fix**: Updated `TextTab` to route `show_all`, `hide_all`, `close_all` for text windows to `MainController.bulk_manager` instead of `txt_actions`.

7.  **AttributeError: TextActions.set_all_text_horizontal**
    - User reported error in `TextTab` layout subtab.
    - **Fix**: Updated `TextTab` to route `set_all_text_horizontal`, `set_all_text_vertical`, `set_all_offset_mode_a/b`, `set_default_text_spacing`, and `change_all_fonts` to `BulkOperationManager` instead of `txt_actions`.

8.  **AttributeError: TextActions.apply_preset_to_all_text_windows**
    - User reported error in `TextTab` bulk style subtab.
    - **Fix**: Implemented `apply_preset_to_all_text_windows` in `BulkOperationManager` (which delegates to `StyleManager`) and updated `TextTab` to route to it.

9.  **AttributeError: 'NoneType' object has no attribute 'add_new_image' (MainController Init)**
    - User reported error during `ImageTab` initialization.
    - **Cause**: `MainController` Properties (`image_actions`, `connector_actions`) were trying to access `self.view.image_actions`/`connector_actions`, but `MainWindow` defines them as `self.img_actions`/`self.conn_actions`.
    - **Fix**: Updated `MainController` properties to access the correct attribute names (`img_actions`, `conn_actions`).

## Verification
- `pytest` passed (23 tests).
- Verified `MainController` code matches `MainWindow` attribute names.
- Verified `MainWindow` initializes these actions BEFORE `setup_ui()` (which was already correct, but the name mismatch broke the connection).

## Verification
- `pytest` passed (23 tests).
- Static analysis confirms call paths are now directed to Managers/Actions instead of `MainWindow`.

import ast
import os

TARGET_DIRS = ["managers", "ui/controllers"]

# MainWindowで許可される属性（これ以外へのアクセスは警告）
# 基本的に Manager, Tab, Controller, Stack, Action などの「高レベルオブジェクト」のみ許可
ALLOWED_ATTRIBUTES = {
    # Managers
    "window_manager",
    "file_manager",
    "settings_manager",
    "menu_manager",
    "style_manager",
    "bulk_manager",
    # Tabs
    "general_tab",
    "text_tab",
    "image_tab",
    "animation_tab",
    "scene_tab",
    "connections_tab",
    "about_tab",
    "main_controller",
    "layout_actions",
    "img_actions",
    "txt_actions",
    "conn_actions",
    "scene_actions",
    # Core / Qt
    "undo_stack",
    "central_widget",
    "status_bar",
    "menu_bar",
    "json_directory",
    "base_directory",
    "font_manager",
    "app",
    "mapToGlobal",
    "close",
    "show",
    "setWindowTitle",
    "setWindowFlags",
    "setWindowIcon",
    "windowFlags",
    "icon_path",
    "resize",
    "move",
    "screen",
    "width",
    "height",
    "x",
    "y",
    # State / Properties
    "last_selected_window",
    "last_selected_connector",
    "last_directory",
    "scenes",
    "edition",
    "user_data_dir",
    "scale_factor",
    "default_node_style",
    "default_line_color",
    "default_line_width",
    "is_property_panel_active",
    "property_panel",
    "toggle_property_panel",
    "update_prop_button_style",
    "on_request_property_panel",
    "on_properties_changed",
    "on_window_moved",
    "set_last_selected_window",
    # Compatibility Properties (Delegators to WindowManager)
    "text_windows",
    "image_windows",
    "connectors",
    "refresh_scene_tabs",
    "scene_db_path",
    "show_status_message",
    # Specific Methods (Safe to access on MW for now)
    "show_about_dialog",
    "add_text_window",
    "change_all_fonts",
    "set_all_offset_mode_a",
    "set_all_offset_mode_b",
    "hide_all_text_windows",
    "show_all_text_windows",
    "toggle_all_frontmost_text_windows",
    "stop_all_text_animations",
    "close_all_text_windows",
    "add_image",
    "set_all_image_size_percentage",
    "set_all_image_opacity",
    "toggle_all_image_animation_speed",
    "reset_all_flips",
    "show_all_image_windows",
    "toggle_all_frontmost_image_windows",
    "open_align_dialog",
    "close_all_images",
    "show_text_window_menu",
    "show_image_window_context_menu",
    "_txt_open_style_gallery_selected",
    "apply_preset_to_all_text_windows",
}


def check_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            print(f"SyntaxError in {filepath}")
            return []

    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            # Check for self.mw.XXX or self.view.XXX
            if isinstance(node.value, ast.Attribute):
                # Pattern: self.mw.XXX -> node.attr=XXX, node.value=self.mw
                val = node.value
                if isinstance(val.value, ast.Name) and val.value.id == "self":
                    if val.attr in ("mw", "view", "main_window"):
                        attr_name = node.attr
                        # メソッド呼び出しやプライベート変数はある程度許容するか？
                        # いったん全てチェックし、ALLOWEDになければ警告
                        if attr_name not in ALLOWED_ATTRIBUTES and not attr_name.startswith("_"):
                            # method call?
                            # リスト等へのアクセスかもしれないので、一律警告
                            issues.append((node.lineno, attr_name))

    return issues


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Scanning from root: {root_dir}")

    found_issues = False

    for relative_dir in TARGET_DIRS:
        target_path = os.path.join(root_dir, relative_dir)
        if not os.path.exists(target_path):
            print(f"Directory not found: {target_path}")
            continue

        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    issues = check_file(full_path)
                    if issues:
                        print(f"\n[WARNING] {os.path.relpath(full_path, root_dir)}")
                        for lineno, attr in issues:
                            print(f"  Line {lineno}: Access to 'self.mw.{attr}' (Not in whitelist)")
                            found_issues = True

    if found_issues:
        print("\nAudit failed: Potentially unsafe MainWindow accesses found.")
        print("Please check if these attributes actually exist on MainWindow.")
        print("If unsafe (e.g. accessing a widget inside a tab), fix it.")
        print("If safe, add to ALLOWED_ATTRIBUTES in tools/check_ui_refs.py.")
    else:
        print("\nAudit passed: No unsafe MainWindow accesses found.")


if __name__ == "__main__":
    main()

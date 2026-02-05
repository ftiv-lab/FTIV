import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Target paths
    paths = [
        os.path.join(base_dir, "json", "text_archetype.json"),
        os.path.join(base_dir, "user_data", "settings", "text_archetype.json"),
    ]

    # Clean Defaults (Factory Settings)
    clean_dev_defaults = {
        "is_frontmost": True,
        "is_click_through": False,
        "move_loop_enabled": False,
        "move_position_only_enabled": False,
        "move_speed": 1000,
        "move_pause_time": 0,
        "start_position": None,
        "end_position": None,
        "move_use_relative": False,
        "move_offset": {"x": 0, "y": 0},
        "move_easing": "Linear",
        "fade_easing": "Linear",
        "anchor_position": "auto",
        "is_fading_enabled": False,
        "fade_in_only_loop_enabled": False,
        "fade_out_only_loop_enabled": False,
        "fade_speed": 1000,
        "fade_pause_time": 0,
        "font": "Arial",
        "font_size": 48,
        "font_color": "#ffffffff",  # White
        "background_color": "#000000",
        "background_visible": True,
        "text_opacity": 100,
        "background_opacity": 100,
        "shadow_enabled": False,
        "shadow_color": "#000000",
        "shadow_opacity": 100,
        "shadow_blur": 0,
        "shadow_scale": 1.0,
        "shadow_offset_x": 0.1,
        "shadow_offset_y": 0.1,
        "is_vertical": False,  # Horizontal
        "outline_enabled": False,
        "outline_color": "#000000",
        "outline_opacity": 100,
        "outline_width": 5.0,
        "outline_blur": 0,
        "second_outline_enabled": False,
        "second_outline_color": "#ffffff",
        "second_outline_opacity": 100,
        "second_outline_width": 10.0,
        "second_outline_blur": 0,
        "third_outline_enabled": False,
        "third_outline_color": "#000000",
        "third_outline_opacity": 100,
        "third_outline_width": 15.0,
        "third_outline_blur": 0,
        "background_outline_enabled": False,
        "background_outline_color": "#000000",
        "background_outline_opacity": 100,
        "background_outline_width_ratio": 0.05,
        "text_gradient_enabled": False,
        "text_gradient": [[0.0, "#000000"], [1.0, "#FFFFFF"]],
        "text_gradient_angle": 0,
        "text_gradient_opacity": 100,
        "background_gradient_enabled": False,
        "background_gradient": [[0.0, "#000000"], [1.0, "#FFFFFF"]],
        "background_gradient_angle": 0,
        "background_gradient_opacity": 100,
        "horizontal_margin_ratio": 0.0,
        "vertical_margin_ratio": 0.0,
        "char_spacing_h": 0.0,
        "line_spacing_h": 0.0,
        "char_spacing_v": 0.0,
        "line_spacing_v": 0.0,
        "margin_top": 0.0,
        "margin_bottom": 0.0,
        "margin_left": 0.0,
        "margin_right": 0.0,
        "background_corner_ratio": 0.2,
        "v_margin_top": 0.0,
        "v_margin_bottom": 0.0,
        "v_margin_left": 0.0,
        "v_margin_right": 0.0,
    }

    print("Resetting Defaults...")
    for path in paths:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(clean_dev_defaults, f, ensure_ascii=False, indent=4)
            print(f"✅ Reset: {path}")
        except Exception as e:
            print(f"⚠️ Failed to reset {path}: {e}")


if __name__ == "__main__":
    main()

import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from models.window_config import TextWindowConfig


def verify_defaults():
    config = TextWindowConfig()
    errors = []

    checks = {
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
    }

    print("Verifying TextWindowConfig defaults...")
    for attr, expected in checks.items():
        val = getattr(config, attr)
        if val != expected:
            errors.append(f"{attr}: Expected {expected}, got {val}")
        else:
            print(f"  OK: {attr} == {val}")

    if errors:
        print("\nERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nSUCCESS: All defaults match canonical baseline (0.0).")
        sys.exit(0)


if __name__ == "__main__":
    verify_defaults()

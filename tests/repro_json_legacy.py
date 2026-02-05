import os
import sys

# Create a valid test env
sys.path.append(os.getcwd())

from models.window_config import TextWindowConfig


def test_legacy_json():
    # Simulate legacy JSON with 'offset_mode' which was removed
    legacy_data = {
        "text": "Hello Legacy",
        "offset_mode": "A",  # This field should be ignored
        "is_vertical": True,
        # Required fields in Base or Default
        "uuid": "test-123",
    }

    print("Attempting to load legacy JSON with 'offset_mode'...")
    try:
        # Pydantic V2 behavior check
        config = TextWindowConfig(**legacy_data)
        print("Success! Config loaded.")
        print("Dump:", config.model_dump(exclude_unset=True))

        if hasattr(config, "offset_mode"):
            print("WARNING: offset_mode attribute still exists (unexpected but not fatal if ignored)")
        else:
            print("CONFIRMED: offset_mode attribute is gone.")

    except Exception as e:
        print(f"CRITICAL FAILURE: Failed to load legacy JSON: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_legacy_json()

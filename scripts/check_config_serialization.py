import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json

from models.mindmap_node_config import MindMapNodeConfig


def check_serialization():
    # 1. Create config with new fields
    config = MindMapNodeConfig(
        uuid="test-uuid",
        text="Test Node",
        icon="✅",
        memo="This is a test memo",
        hyperlink="https://example.com",
        image_path="./images/test.png",
    )

    # 2. Serialize
    data = config.to_dict()
    print("Serialized Data:", json.dumps(data, indent=2, ensure_ascii=False))

    # 3. Verify fields
    assert data["icon"] == "✅"
    assert data["memo"] == "This is a test memo"
    assert data["hyperlink"] == "https://example.com"
    assert data["image_path"] == "./images/test.png"

    # 4. Deserialize
    restored = MindMapNodeConfig.from_dict(data)

    # 5. Verify restored object
    assert restored.icon == "✅"
    assert restored.memo == "This is a test memo"
    assert restored.hyperlink == "https://example.com"
    assert restored.image_path == "./images/test.png"

    print("\nSerialization/Deserialization Verification PASSED!")


if __name__ == "__main__":
    check_serialization()

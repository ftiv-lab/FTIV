from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_profiles() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    path = root / "config" / "ui" / "phase10b_visual_profiles.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_visual_profile_contract_file_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "config" / "ui" / "phase10b_visual_profiles.json"
    assert path.exists()


def test_visual_profile_contract_has_minimum_cases() -> None:
    payload = _load_profiles()
    cases = payload.get("cases", {})
    assert isinstance(cases, dict)
    assert len(cases) >= 8


def test_visual_profile_contract_required_fields() -> None:
    payload = _load_profiles()
    cases = payload["cases"]
    required = {"window_size", "density_mode", "locale", "font_policy", "target_widget"}
    for case_id, profile in cases.items():
        assert isinstance(profile, dict), f"{case_id} must be an object"
        assert required.issubset(profile.keys()), f"{case_id} missing required keys"


def test_visual_profile_contract_field_values() -> None:
    payload = _load_profiles()
    for case_id, profile in payload["cases"].items():
        window_size = profile["window_size"]
        assert isinstance(window_size, list), f"{case_id} window_size must be a list"
        assert len(window_size) == 2, f"{case_id} window_size must have 2 entries"
        assert all(isinstance(v, int) and v > 0 for v in window_size), f"{case_id} window_size values must be +int"
        assert profile["density_mode"] in {"compact", "comfortable", "auto"}, f"{case_id} invalid density_mode"
        assert isinstance(profile["locale"], str) and profile["locale"], f"{case_id} locale must be non-empty"
        assert isinstance(profile["font_policy"], str) and profile["font_policy"], (
            f"{case_id} font_policy must be non-empty"
        )
        assert isinstance(profile["target_widget"], str) and profile["target_widget"], (
            f"{case_id} target_widget must be non-empty"
        )

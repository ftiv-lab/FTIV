from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


def _load_policy() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    path = root / "config" / "ui" / "phase10d_visual_gate_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_visual_gate_policy_contract_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "config" / "ui" / "phase10d_visual_gate_policy.json"
    assert path.exists()


def test_visual_gate_policy_has_required_fields() -> None:
    payload = _load_policy()
    assert payload.get("schema_version") == 1
    assert isinstance(payload.get("enforce_rollout"), dict)
    assert isinstance(payload.get("promotion_rule"), dict)
    assert isinstance(payload.get("temporary_exceptions"), list)


def test_visual_gate_policy_rollout_dates_are_valid() -> None:
    payload = _load_policy()
    rollout = payload["enforce_rollout"]
    start_date = date.fromisoformat(str(rollout["start_date"]))
    grace_until = date.fromisoformat(str(rollout["grace_until"]))
    assert grace_until >= start_date
    assert isinstance(rollout["enabled"], bool)


def test_visual_gate_policy_exceptions_have_reason_and_expiry() -> None:
    payload = _load_policy()
    exceptions = payload["temporary_exceptions"]
    for entry in exceptions:
        assert isinstance(entry, dict)
        case_id = str(entry.get("case_id") or "").strip()
        reason = str(entry.get("reason") or "").strip()
        expires_at = str(entry.get("expires_at") or "").strip()
        assert case_id
        assert reason
        _ = date.fromisoformat(expires_at)

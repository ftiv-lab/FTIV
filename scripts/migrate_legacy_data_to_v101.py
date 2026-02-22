#!/usr/bin/env python
"""One-shot legacy data migration for FTIV v1.0.1.

This script performs file-based migrations for JSON artifacts under the
project's ``json/`` directory.

Scope (Phase 8A-1):
- Remove deprecated AppSettings keys:
  - text_editing_mode
  - info_operations_expanded
- Remove legacy absolute move keys recursively:
  - start_position
  - end_position
- Migrate legacy task prefixes in task-mode text payloads:
  - [ ] foo
  - [x] foo
  into ``task_states`` while cleaning text bodies.

Safety:
- dry-run by default
- apply mode requires ``--apply``
- backup files are created before writes in apply mode
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

LEGACY_TASK_LINE_PATTERN = re.compile(r"^\s*\[(?P<state>[ xX])\]\s?(?P<body>.*)$")
DEPRECATED_APP_SETTINGS_KEYS = ("text_editing_mode", "info_operations_expanded")
LEGACY_ABSOLUTE_MOVE_KEYS = ("start_position", "end_position")


@dataclass
class MigrationStats:
    files_scanned: int = 0
    files_changed: int = 0
    backups_written: int = 0
    app_settings_keys_removed: int = 0
    absolute_move_keys_removed: int = 0
    task_texts_migrated: int = 0
    task_states_normalized: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)


def _split_lines(text: str) -> list[str]:
    src = str(text or "")
    return src.split("\n") if src else [""]


def _normalize_task_states(states: Any, line_count: int) -> list[bool]:
    normalized = [bool(v) for v in states] if isinstance(states, list) else []
    if line_count <= 0:
        return []
    if len(normalized) < line_count:
        normalized.extend([False] * (line_count - len(normalized)))
    elif len(normalized) > line_count:
        normalized = normalized[:line_count]
    return normalized


def _extract_legacy_task_data(text: str) -> tuple[str, list[bool], bool]:
    lines = _split_lines(text)
    migrated_lines: list[str] = []
    migrated_states: list[bool] = []
    migrated_any = False

    for line in lines:
        match = LEGACY_TASK_LINE_PATTERN.match(str(line or ""))
        if match:
            migrated_any = True
            state = str(match.group("state") or " ").strip().lower() == "x"
            body = str(match.group("body") or "")
            migrated_lines.append(body)
            migrated_states.append(state)
        else:
            migrated_lines.append(str(line or ""))
            migrated_states.append(False)

    return "\n".join(migrated_lines), migrated_states, migrated_any


def _migrate_task_window_payload(payload: dict[str, Any], stats: MigrationStats) -> bool:
    mode = str(payload.get("content_mode", "note") or "note").strip().lower()
    if mode != "task":
        return False

    text_now = str(payload.get("text", "") or "")
    lines_now = _split_lines(text_now)
    existing_states = _normalize_task_states(payload.get("task_states", []), len(lines_now))
    cleaned_text, migrated_states, migrated_any = _extract_legacy_task_data(text_now)

    changed = False
    if migrated_any:
        has_non_default_state = any(existing_states)
        final_states_source = existing_states if has_non_default_state else migrated_states
        final_states = _normalize_task_states(final_states_source, len(_split_lines(cleaned_text)))
        if payload.get("text") != cleaned_text:
            payload["text"] = cleaned_text
            changed = True
        if payload.get("task_states") != final_states:
            payload["task_states"] = final_states
            changed = True
        if changed:
            stats.task_texts_migrated += 1
        return changed

    normalized_states = _normalize_task_states(existing_states, len(lines_now))
    if payload.get("task_states") != normalized_states:
        payload["task_states"] = normalized_states
        stats.task_states_normalized += 1
        changed = True
    return changed


def _migrate_recursive(obj: Any, stats: MigrationStats) -> bool:
    changed = False
    if isinstance(obj, dict):
        for key in LEGACY_ABSOLUTE_MOVE_KEYS:
            if key in obj:
                obj.pop(key, None)
                stats.absolute_move_keys_removed += 1
                changed = True

        if _migrate_task_window_payload(obj, stats):
            changed = True

        for value in obj.values():
            if isinstance(value, (dict, list)) and _migrate_recursive(value, stats):
                changed = True
        return changed

    if isinstance(obj, list):
        for value in obj:
            if isinstance(value, (dict, list)) and _migrate_recursive(value, stats):
                changed = True
        return changed

    return False


def _migrate_app_settings_dict(data: Any, stats: MigrationStats) -> bool:
    if not isinstance(data, dict):
        return False

    changed = False
    for key in DEPRECATED_APP_SETTINGS_KEYS:
        if key in data:
            data.pop(key, None)
            stats.app_settings_keys_removed += 1
            changed = True
    return changed


def _resolve_backup_path(backup_dir: Path, source_path: Path) -> Path:
    target = backup_dir / source_path.name
    if not target.exists():
        return target
    stem = source_path.stem
    suffix = source_path.suffix
    index = 1
    while True:
        candidate = backup_dir / f"{stem}.{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _backup_file(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = _resolve_backup_path(backup_dir, source_path)
    shutil.copy2(source_path, target)
    return target


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _collect_json_files(json_dir: Path) -> list[Path]:
    if not json_dir.exists():
        return []
    return sorted([p for p in json_dir.glob("*.json") if p.is_file()], key=lambda p: p.name.lower())


def migrate_json_directory(json_dir: Path, apply: bool, backup_dir: Path | None = None) -> MigrationStats:
    stats = MigrationStats()
    for path in _collect_json_files(json_dir):
        stats.files_scanned += 1

        try:
            data = _load_json(path)
        except Exception as exc:
            stats.errors += 1
            stats.error_messages.append(f"{path.name}: failed to load JSON ({exc})")
            continue

        changed = False
        if path.name.lower() == "app_settings.json":
            if _migrate_app_settings_dict(data, stats):
                changed = True
        else:
            if _migrate_recursive(data, stats):
                changed = True

        if not changed:
            continue

        stats.files_changed += 1
        if not apply:
            continue

        if backup_dir is None:
            raise ValueError("backup_dir is required when apply=True")

        try:
            _backup_file(path, backup_dir)
            stats.backups_written += 1
            _write_json(path, data)
        except Exception as exc:
            stats.errors += 1
            stats.error_messages.append(f"{path.name}: failed to write migrated data ({exc})")

    return stats


def _default_backup_dir(json_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return json_dir / f"backup_migrate_legacy_{stamp}"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate FTIV legacy JSON data to v1.0.1 schema assumptions.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Project base directory. Default: repository root inferred from this script.",
    )
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=None,
        help="Explicit JSON directory path. Default: <base-dir>/json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes only (default behavior when --apply is not specified).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply migration and write files.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Backup output directory for apply mode. Default: <json-dir>/backup_migrate_legacy_<timestamp>",
    )
    return parser


def _print_summary(stats: MigrationStats, *, apply: bool, json_dir: Path, backup_dir: Path | None) -> None:
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[migrate_legacy_data_to_v101] mode={mode}")
    print(f"json_dir={json_dir}")
    if apply and backup_dir is not None:
        print(f"backup_dir={backup_dir}")
    print(f"files_scanned={stats.files_scanned}")
    print(f"files_changed={stats.files_changed}")
    print(f"backups_written={stats.backups_written}")
    print(f"app_settings_keys_removed={stats.app_settings_keys_removed}")
    print(f"absolute_move_keys_removed={stats.absolute_move_keys_removed}")
    print(f"task_texts_migrated={stats.task_texts_migrated}")
    print(f"task_states_normalized={stats.task_states_normalized}")
    print(f"errors={stats.errors}")
    if stats.error_messages:
        print("error_details:")
        for msg in stats.error_messages:
            print(f"- {msg}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run cannot be used together.")

    base_dir = args.base_dir.resolve()
    json_dir = args.json_dir.resolve() if args.json_dir is not None else (base_dir / "json")
    apply = bool(args.apply)
    if not apply:
        # Explicitly dry-run when apply is not set.
        args.dry_run = True

    if apply:
        backup_dir = args.backup_dir.resolve() if args.backup_dir is not None else _default_backup_dir(json_dir)
    else:
        backup_dir = args.backup_dir.resolve() if args.backup_dir is not None else None

    stats = migrate_json_directory(json_dir=json_dir, apply=apply, backup_dir=backup_dir)
    _print_summary(stats, apply=apply, json_dir=json_dir, backup_dir=backup_dir)

    if stats.errors > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

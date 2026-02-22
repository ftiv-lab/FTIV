import json
from pathlib import Path

from scripts.migrate_legacy_data_to_v101 import migrate_json_directory


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_migrate_legacy_data_dry_run_does_not_write_or_backup(tmp_path: Path) -> None:
    json_dir = tmp_path / "json"
    backup_dir = tmp_path / "backup"

    app_settings_path = json_dir / "app_settings.json"
    scenes_db_path = json_dir / "scenes_db.json"
    project_path = json_dir / "my_project.json"

    app_settings_data = {
        "main_window_frontmost": True,
        "text_editing_mode": "inline",
        "info_operations_expanded": True,
    }
    scene_data = {
        "__default__": {
            "scene_1": {
                "format_version": 1,
                "windows": [
                    {
                        "type": "text",
                        "content_mode": "task",
                        "text": "[x] done\n[ ] todo\nplain line",
                        "task_states": [],
                        "start_position": {"x": 1, "y": 2},
                    }
                ],
                "connections": [],
            }
        }
    }
    project_data = {
        "type": "ftiv_project",
        "current_state": {
            "format_version": 1,
            "windows": [
                {
                    "type": "text",
                    "content_mode": "task",
                    "text": "[ ] first",
                    "task_states": [],
                    "end_position": {"x": 3, "y": 4},
                }
            ],
            "connections": [],
        },
    }

    _write_json(app_settings_path, app_settings_data)
    _write_json(scenes_db_path, scene_data)
    _write_json(project_path, project_data)

    stats = migrate_json_directory(json_dir=json_dir, apply=False, backup_dir=backup_dir)

    assert stats.files_scanned == 3
    assert stats.files_changed == 3
    assert stats.backups_written == 0
    assert stats.app_settings_keys_removed == 2
    assert stats.task_texts_migrated == 2
    assert stats.errors == 0
    assert not backup_dir.exists()

    # Dry-run: files must remain unchanged.
    assert _read_json(app_settings_path) == app_settings_data
    assert _read_json(scenes_db_path) == scene_data
    assert _read_json(project_path) == project_data


def test_migrate_legacy_data_apply_writes_files_and_backups(tmp_path: Path) -> None:
    json_dir = tmp_path / "json"
    backup_dir = tmp_path / "backup"

    app_settings_path = json_dir / "app_settings.json"
    scene_path = json_dir / "scene_export.json"

    _write_json(
        app_settings_path,
        {
            "main_window_frontmost": True,
            "text_editing_mode": "inline",
            "info_operations_expanded": True,
        },
    )
    _write_json(
        scene_path,
        {
            "format_version": 1,
            "windows": [
                {
                    "type": "text",
                    "content_mode": "task",
                    "text": "[x] done\n[ ] todo\nplain",
                    "task_states": [],
                    "start_position": {"x": 10, "y": 10},
                    "end_position": {"x": 11, "y": 11},
                }
            ],
            "connections": [],
        },
    )

    stats = migrate_json_directory(json_dir=json_dir, apply=True, backup_dir=backup_dir)

    assert stats.files_scanned == 2
    assert stats.files_changed == 2
    assert stats.backups_written == 2
    assert stats.app_settings_keys_removed == 2
    assert stats.absolute_move_keys_removed == 2
    assert stats.task_texts_migrated == 1
    assert stats.errors == 0

    migrated_settings = _read_json(app_settings_path)
    assert isinstance(migrated_settings, dict)
    assert "text_editing_mode" not in migrated_settings
    assert "info_operations_expanded" not in migrated_settings

    migrated_scene = _read_json(scene_path)
    assert isinstance(migrated_scene, dict)
    win = migrated_scene["windows"][0]
    assert win["text"] == "done\ntodo\nplain"
    assert win["task_states"] == [True, False, False]
    assert "start_position" not in win
    assert "end_position" not in win

    backups = sorted(p.name for p in backup_dir.glob("*.json"))
    assert "app_settings.json" in backups
    assert "scene_export.json" in backups


def test_migrate_legacy_data_apply_is_idempotent(tmp_path: Path) -> None:
    json_dir = tmp_path / "json"
    backup_dir = tmp_path / "backup"
    scene_path = json_dir / "scene_export.json"

    _write_json(
        scene_path,
        {
            "format_version": 1,
            "windows": [
                {
                    "type": "text",
                    "content_mode": "task",
                    "text": "[ ] first\n[x] second",
                    "task_states": [],
                }
            ],
            "connections": [],
        },
    )

    first = migrate_json_directory(json_dir=json_dir, apply=True, backup_dir=backup_dir)
    second = migrate_json_directory(json_dir=json_dir, apply=True, backup_dir=backup_dir)

    assert first.files_changed == 1
    assert first.backups_written == 1
    assert second.files_changed == 0
    assert second.backups_written == 0
    assert second.errors == 0


def test_migrate_legacy_data_preserves_existing_non_default_task_states(tmp_path: Path) -> None:
    json_dir = tmp_path / "json"
    scene_path = json_dir / "scene_export.json"

    _write_json(
        scene_path,
        {
            "format_version": 1,
            "windows": [
                {
                    "type": "text",
                    "content_mode": "task",
                    "text": "[ ] first\n[x] second",
                    "task_states": [True, False],
                }
            ],
            "connections": [],
        },
    )

    stats = migrate_json_directory(json_dir=json_dir, apply=True, backup_dir=tmp_path / "backup")
    assert stats.files_changed == 1

    migrated_scene = _read_json(scene_path)
    win = migrated_scene["windows"][0]
    assert win["text"] == "first\nsecond"
    assert win["task_states"] == [True, False]


def test_migrate_legacy_data_records_invalid_json_errors(tmp_path: Path) -> None:
    json_dir = tmp_path / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    (json_dir / "broken.json").write_text("{ not-json ", encoding="utf-8")
    _write_json(json_dir / "valid.json", {"ok": True})

    stats = migrate_json_directory(json_dir=json_dir, apply=False, backup_dir=tmp_path / "backup")

    assert stats.files_scanned == 2
    assert stats.errors == 1
    assert len(stats.error_messages) == 1
    assert "broken.json" in stats.error_messages[0]

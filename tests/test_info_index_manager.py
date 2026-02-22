from types import SimpleNamespace

from managers.info_index_manager import InfoIndexManager, InfoQuery


def _make_task_ref(line_index: int, text: str, done: bool):
    return SimpleNamespace(line_index=line_index, text=text, done=done)


def _make_window(
    *,
    uuid: str,
    text: str,
    content_mode: str = "note",
    title: str = "",
    tags=None,
    is_starred: bool = False,
    created_at: str = "",
    updated_at: str = "",
    due_at: str = "",
    due_time: str = "",
    due_timezone: str = "",
    due_precision: str = "date",
    is_archived: bool = False,
    task_refs=None,
):
    if tags is None:
        tags = []
    if task_refs is None:
        task_refs = []
    return SimpleNamespace(
        uuid=uuid,
        text=text,
        content_mode=content_mode,
        title=title,
        tags=tags,
        is_starred=is_starred,
        created_at=created_at,
        updated_at=updated_at,
        due_at=due_at,
        due_time=due_time,
        due_timezone=due_timezone,
        due_precision=due_precision,
        is_archived=is_archived,
        iter_task_items=lambda: task_refs,
    )


class TestInfoIndexManager:
    def test_build_index_extracts_tasks_and_notes(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w-task",
                text="buy milk\ncall",
                content_mode="task",
                title="Today",
                tags=["home", "errands"],
                is_starred=True,
                created_at="2026-02-10T10:00:00",
                updated_at="2026-02-10T10:10:00",
                task_refs=[
                    _make_task_ref(0, "buy milk", False),
                    _make_task_ref(1, "call", True),
                ],
            ),
            _make_window(
                uuid="w-note",
                text="meeting memo",
                content_mode="note",
                title="Work",
                tags=["work"],
            ),
        ]

        tasks, notes = manager.build_index(windows)

        assert len(tasks) == 2
        assert len(notes) == 2
        assert tasks[0].window_uuid == "w-task"
        assert tasks[0].item_key in {"w-task:0", "w-task:1"}
        assert any(n.window_uuid == "w-note" and n.content_mode == "note" for n in notes)

    def test_query_tasks_filters_open_star_tag_and_search(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="a\nb",
                content_mode="task",
                title="Home",
                tags=["home"],
                is_starred=True,
                task_refs=[_make_task_ref(0, "Buy milk", False), _make_task_ref(1, "Done", True)],
            ),
            _make_window(
                uuid="w2",
                text="c",
                content_mode="task",
                title="Work",
                tags=["work"],
                is_starred=False,
                task_refs=[_make_task_ref(0, "Ship release", False)],
            ),
        ]
        tasks, _ = manager.build_index(windows)

        query = InfoQuery(
            text="buy",
            tag="home",
            starred_only=True,
            open_tasks_only=True,
            include_archived=False,
        )
        filtered = manager.query_tasks(tasks, query)
        assert len(filtered) == 1
        assert filtered[0].window_uuid == "w1"
        assert filtered[0].text == "Buy milk"
        assert filtered[0].done is False

    def test_query_notes_excludes_archived_by_default(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="visible", content_mode="note", title="Visible", is_archived=False),
            _make_window(uuid="n2", text="hidden", content_mode="note", title="Archived", is_archived=True),
        ]
        _, notes = manager.build_index(windows)

        default_filtered = manager.query_notes(notes, InfoQuery())
        assert len(default_filtered) == 1
        assert default_filtered[0].window_uuid == "n1"

        include_archived = manager.query_notes(notes, InfoQuery(include_archived=True))
        assert len(include_archived) == 2

    def test_archive_scope_filters_notes(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="visible", content_mode="note", is_archived=False),
            _make_window(uuid="n2", text="hidden", content_mode="note", is_archived=True),
        ]
        _, notes = manager.build_index(windows)

        active = manager.query_notes(notes, InfoQuery(archive_scope="active"))
        archived = manager.query_notes(notes, InfoQuery(archive_scope="archived"))
        all_items = manager.query_notes(notes, InfoQuery(archive_scope="all"))

        assert [item.window_uuid for item in active] == ["n1"]
        assert [item.window_uuid for item in archived] == ["n2"]
        assert len(all_items) == 2
        assert {item.window_uuid for item in all_items} == {"n1", "n2"}

    def test_archive_scope_prioritizes_over_include_archived_except_legacy_active(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="visible", content_mode="note", is_archived=False),
            _make_window(uuid="n2", text="hidden", content_mode="note", is_archived=True),
        ]
        _, notes = manager.build_index(windows)

        legacy_all = manager.query_notes(notes, InfoQuery(include_archived=True, archive_scope="active"))
        forced_archived = manager.query_notes(notes, InfoQuery(include_archived=True, archive_scope="archived"))

        assert len(legacy_all) == 2
        assert {item.window_uuid for item in legacy_all} == {"n1", "n2"}
        assert [item.window_uuid for item in forced_archived] == ["n2"]

    def test_query_tasks_due_filter_overdue(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="t1",
                content_mode="task",
                due_at="2001-01-01T00:00:00",
                task_refs=[_make_task_ref(0, "old", False)],
            ),
            _make_window(
                uuid="w2",
                text="t2",
                content_mode="task",
                due_at="2999-01-01T00:00:00",
                task_refs=[_make_task_ref(0, "future", False)],
            ),
        ]
        tasks, _ = manager.build_index(windows)

        filtered = manager.query_tasks(tasks, InfoQuery(due_filter="overdue", sort_by="updated", sort_desc=True))
        assert len(filtered) == 1
        assert filtered[0].window_uuid == "w1"

    def test_query_tasks_due_filter_upcoming(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="t1",
                content_mode="task",
                due_at="2001-01-01T00:00:00",
                task_refs=[_make_task_ref(0, "old", False)],
            ),
            _make_window(
                uuid="w2",
                text="t2",
                content_mode="task",
                due_at="2999-01-01T00:00:00",
                task_refs=[_make_task_ref(0, "future", False)],
            ),
        ]
        tasks, _ = manager.build_index(windows)

        filtered = manager.query_tasks(tasks, InfoQuery(due_filter="upcoming"))
        assert len(filtered) == 1
        assert filtered[0].window_uuid == "w2"

    def test_query_notes_due_filter_dated_and_undated(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="dated", content_mode="note", due_at="2026-03-01T00:00:00"),
            _make_window(uuid="n2", text="undated", content_mode="note", due_at=""),
        ]
        _, notes = manager.build_index(windows)

        dated = manager.query_notes(notes, InfoQuery(due_filter="dated"))
        undated = manager.query_notes(notes, InfoQuery(due_filter="undated"))

        assert [n.window_uuid for n in dated] == ["n1"]
        assert [n.window_uuid for n in undated] == ["n2"]

    def test_query_notes_item_scope_tasks_and_notes(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="memo", content_mode="note"),
            _make_window(
                uuid="t1",
                text="task line",
                content_mode="task",
                task_refs=[_make_task_ref(0, "task line", False)],
            ),
        ]
        _, notes = manager.build_index(windows)

        only_task = manager.query_notes(notes, InfoQuery(item_scope="tasks", content_mode_filter="task"))
        only_note = manager.query_notes(notes, InfoQuery(item_scope="notes", content_mode_filter="note"))

        assert [item.window_uuid for item in only_task] == ["t1"]
        assert [item.window_uuid for item in only_note] == ["n1"]

    def test_query_tasks_and_notes_respect_item_scope(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="memo", content_mode="note"),
            _make_window(
                uuid="t1",
                text="task line",
                content_mode="task",
                task_refs=[_make_task_ref(0, "task line", False)],
            ),
        ]
        tasks, notes = manager.build_index(windows)

        tasks_when_note_scope = manager.query_tasks(tasks, InfoQuery(item_scope="notes", content_mode_filter="note"))
        notes_when_task_scope = manager.query_notes(notes, InfoQuery(item_scope="tasks", content_mode_filter="task"))

        assert tasks_when_note_scope == []
        assert [item.window_uuid for item in notes_when_task_scope] == ["t1"]

    def test_query_item_scope_contract_is_primary(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="memo", content_mode="note"),
            _make_window(
                uuid="t1",
                text="task line",
                content_mode="task",
                task_refs=[_make_task_ref(0, "task line", False)],
            ),
        ]
        tasks, notes = manager.build_index(windows)

        notes_with_tasks_scope = manager.query_notes(
            notes,
            InfoQuery(item_scope="tasks", content_mode_filter="task"),
        )
        tasks_with_notes_scope = manager.query_tasks(
            tasks,
            InfoQuery(item_scope="notes", content_mode_filter="note"),
        )

        assert [item.window_uuid for item in notes_with_tasks_scope] == ["t1"]
        assert tasks_with_notes_scope == []

    def test_query_tasks_due_filter_uses_datetime_when_due_precision_datetime(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="t1",
                content_mode="task",
                due_at="2099-01-01T00:00:00",
                due_time="09:30",
                due_timezone="",
                due_precision="datetime",
                task_refs=[_make_task_ref(0, "future", False)],
            )
        ]
        tasks, _ = manager.build_index(windows)
        filtered = manager.query_tasks(tasks, InfoQuery(due_filter="upcoming"))
        assert [item.window_uuid for item in filtered] == ["w1"]

    def test_query_notes_sort_by_due(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="a", content_mode="note", due_at="2026-03-01T00:00:00"),
            _make_window(uuid="n2", text="b", content_mode="note", due_at="2026-02-01T00:00:00"),
        ]
        _, notes = manager.build_index(windows)

        ordered = manager.query_notes(notes, InfoQuery(sort_by="due", sort_desc=False))
        assert [n.window_uuid for n in ordered] == ["n2", "n1"]

    def test_build_stats_counts_open_done_overdue_and_starred(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="t1\nt2",
                content_mode="task",
                is_starred=True,
                due_at="2001-01-01T00:00:00",
                task_refs=[_make_task_ref(0, "open old", False), _make_task_ref(1, "done", True)],
            ),
            _make_window(
                uuid="n1",
                text="memo",
                content_mode="note",
                is_starred=True,
            ),
        ]
        tasks, notes = manager.build_index(windows)
        stats = manager.build_stats(tasks, notes)

        assert stats.open_tasks == 1
        assert stats.done_tasks == 1
        assert stats.overdue_tasks == 1
        assert stats.starred_notes == 2

    def test_group_tasks_by_tag(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="a",
                content_mode="task",
                tags=["work"],
                task_refs=[_make_task_ref(0, "task1", False)],
            ),
            _make_window(
                uuid="w2",
                text="b",
                content_mode="task",
                tags=["home"],
                task_refs=[_make_task_ref(0, "task2", False)],
            ),
            _make_window(
                uuid="w3",
                text="c",
                content_mode="task",
                task_refs=[_make_task_ref(0, "untagged", False)],
            ),
        ]
        tasks, _ = manager.build_index(windows)
        groups = manager.group_tasks_by_tag(tasks)
        keys = [g.group_key for g in groups]
        assert "tag:work" in keys
        assert "tag:home" in keys
        assert "tag:" in keys
        for g in groups:
            assert len(g.items) == 1

    def test_group_tasks_by_tag_untagged_last(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="a",
                content_mode="task",
                task_refs=[_make_task_ref(0, "untagged", False)],
                updated_at="2026-02-10T12:00:00",
            ),
            _make_window(
                uuid="w2",
                text="b",
                content_mode="task",
                tags=["work"],
                task_refs=[_make_task_ref(0, "tagged", False)],
                updated_at="2026-02-10T11:00:00",
            ),
        ]
        tasks, _ = manager.build_index(windows)
        groups = manager.group_tasks_by_tag(tasks)
        # untagged item comes first (sorted by updated_at desc) but group order follows item order
        assert len(groups) == 2

    def test_group_tasks_by_window(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="a\nb",
                content_mode="task",
                title="Project A",
                is_starred=True,
                task_refs=[_make_task_ref(0, "t1", False), _make_task_ref(1, "t2", True)],
            ),
            _make_window(
                uuid="w2",
                text="c",
                content_mode="task",
                title="Project B",
                task_refs=[_make_task_ref(0, "t3", False)],
            ),
        ]
        tasks, _ = manager.build_index(windows)
        groups = manager.group_tasks_by_window(tasks)
        assert len(groups) == 2
        keys = [g.group_key for g in groups]
        assert "window:w1" in keys
        assert "window:w2" in keys
        # w1 is starred so label should contain star
        w1_group = next(g for g in groups if g.group_key == "window:w1")
        assert "\u2605" in w1_group.label

    def test_group_notes_by_tag(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="memo1", tags=["work"]),
            _make_window(uuid="n2", text="memo2", tags=["home"]),
            _make_window(uuid="n3", text="memo3"),
        ]
        _, notes = manager.build_index(windows)
        groups = manager.group_notes_by_tag(notes)
        assert len(groups) == 3
        keys = [g.group_key for g in groups]
        assert "tag:work" in keys
        assert "tag:home" in keys
        assert "tag:" in keys

    def test_group_notes_by_window(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(uuid="n1", text="memo1", title="Doc A"),
            _make_window(uuid="n2", text="memo2", title="Doc B"),
        ]
        _, notes = manager.build_index(windows)
        groups = manager.group_notes_by_window(notes)
        assert len(groups) == 2

    def test_group_mixed_smart(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="a",
                content_mode="task",
                is_starred=True,
                task_refs=[_make_task_ref(0, "starred task", False)],
            ),
            _make_window(uuid="n1", text="memo", is_starred=True),
            _make_window(uuid="n2", text="other memo"),
        ]
        tasks, notes = manager.build_index(windows)
        groups = manager.group_mixed_smart(tasks, notes)
        keys = [g.group_key for g in groups]
        assert "starred" in keys
        assert "other" in keys
        starred_group = next(g for g in groups if g.group_key == "starred")
        # w1: 1 task + 1 note (both starred), n1: 1 note (starred) = 3
        assert len(starred_group.items) == 3

    def test_group_mixed_by_tag(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="a",
                content_mode="task",
                tags=["work"],
                task_refs=[_make_task_ref(0, "task", False)],
            ),
            _make_window(uuid="n1", text="memo", tags=["work"]),
        ]
        tasks, notes = manager.build_index(windows)
        groups = manager.group_mixed_by_tag(tasks, notes)
        assert len(groups) == 1
        assert groups[0].group_key == "tag:work"
        # w1: 1 task + 1 note, n1: 1 note = 3 items total
        assert len(groups[0].items) == 3

    def test_group_mixed_by_window(self):
        manager = InfoIndexManager()
        windows = [
            _make_window(
                uuid="w1",
                text="a",
                content_mode="task",
                title="Proj",
                task_refs=[_make_task_ref(0, "task", False)],
            ),
        ]
        tasks, notes = manager.build_index(windows)
        groups = manager.group_mixed_by_window(tasks, notes)
        # Task items and note items from same window should be in same group
        assert len(groups) == 1
        assert groups[0].group_key == "window:w1"
        assert len(groups[0].items) == 2  # 1 task + 1 note (from same window)

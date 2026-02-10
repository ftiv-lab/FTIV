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

from typing import Any, List


def task_progress_counts(window: Any) -> tuple[int, int]:
    lines = window._split_lines(str(getattr(window, "text", "") or ""))
    total = len(lines)
    raw_states = getattr(window, "task_states", [])
    normalized = window._normalize_task_states(list(raw_states) if isinstance(raw_states, list) else [], total)
    done = sum(1 for state in normalized if state)
    return done, total


def toggle_task_line_by_index(window: Any, idx: int) -> None:
    window.toggle_task_line_state(idx)


def get_task_progress(window: Any) -> tuple[int, int]:
    if not window.is_task_mode():
        return 0, 0
    total = len(window._split_lines(window.text))
    states = window._normalize_task_states(window.task_states, total)
    done = sum(1 for state in states if state)
    return done, total


def iter_task_items(window: Any) -> List[Any]:
    if not window.is_task_mode():
        return []

    # Local import to avoid module import cycle at load time.
    from windows.text_window import TaskLineRef

    lines = window._split_lines(window.text)
    states = window._normalize_task_states(window.task_states, len(lines))
    window_uuid = str(getattr(window, "uuid", ""))
    return [
        TaskLineRef(
            window_uuid=window_uuid,
            line_index=i,
            text=str(line or ""),
            done=bool(states[i]),
        )
        for i, line in enumerate(lines)
    ]


def get_task_line_state(window: Any, index: int) -> bool:
    if not window.is_task_mode():
        return False
    lines = window._split_lines(window.text)
    if index < 0 or index >= len(lines):
        return False
    states = window._normalize_task_states(window.task_states, len(lines))
    return bool(states[index])


def set_task_line_state(window: Any, index: int, done: bool) -> None:
    if not window.is_task_mode():
        return
    lines = window._split_lines(window.text)
    if index < 0 or index >= len(lines):
        return

    states = window._normalize_task_states(window.task_states, len(lines))
    target = bool(done)
    if bool(states[index]) == target:
        return

    new_states = list(states)
    new_states[index] = target
    window.set_undoable_property("task_states", new_states, "update_text")
    window._touch_updated_at()


def toggle_task_line_state(window: Any, index: int) -> None:
    if not window.is_task_mode():
        return
    window.set_task_line_state(index, not window.get_task_line_state(index))


def bulk_set_task_done(window: Any, indices: List[int], value: bool) -> None:
    if not window.is_task_mode():
        return
    total = len(window._split_lines(window.text))
    states = window._normalize_task_states(window.task_states, total)
    new_states = list(states)
    target = bool(value)
    changed = False
    for idx in sorted(set(indices or [])):
        if idx < 0 or idx >= total:
            continue
        if bool(new_states[idx]) == target:
            continue
        new_states[idx] = target
        changed = True
    if changed:
        window.set_undoable_property("task_states", new_states, "update_text")
        window._touch_updated_at()


def complete_all_tasks(window: Any) -> None:
    if not window.is_task_mode():
        return
    total = len(window._split_lines(window.text))
    states = window._normalize_task_states(window.task_states, total)
    new_states = [True for _ in states]
    if new_states != states:
        window.set_undoable_property("task_states", new_states, "update_text")
        window._touch_updated_at()


def uncomplete_all_tasks(window: Any) -> None:
    if not window.is_task_mode():
        return
    total = len(window._split_lines(window.text))
    states = window._normalize_task_states(window.task_states, total)
    new_states = [False for _ in states]
    if new_states != states:
        window.set_undoable_property("task_states", new_states, "update_text")
        window._touch_updated_at()

"""TextWindow decomposition modules (phase 9C)."""

from .metadata_ops import clear_due_at, set_archived, set_due_at, set_starred, set_tags, set_title_and_tags
from .runtime_bridge import ensure_runtime_services
from .selection_ops import (
    after_set_selected,
    hit_test_task_checkbox,
    mouse_move,
    mouse_press,
    mouse_release_should_toggle,
)
from .task_ops import (
    bulk_set_task_done,
    complete_all_tasks,
    get_task_line_state,
    get_task_progress,
    iter_task_items,
    set_task_line_state,
    task_progress_counts,
    toggle_task_line_by_index,
    toggle_task_line_state,
    uncomplete_all_tasks,
)

__all__ = [
    "after_set_selected",
    "bulk_set_task_done",
    "complete_all_tasks",
    "clear_due_at",
    "ensure_runtime_services",
    "get_task_line_state",
    "get_task_progress",
    "hit_test_task_checkbox",
    "iter_task_items",
    "mouse_move",
    "mouse_press",
    "mouse_release_should_toggle",
    "set_task_line_state",
    "set_archived",
    "set_due_at",
    "set_starred",
    "set_tags",
    "set_title_and_tags",
    "task_progress_counts",
    "toggle_task_line_by_index",
    "toggle_task_line_state",
    "uncomplete_all_tasks",
]

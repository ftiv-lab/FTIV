#!/usr/bin/env python
"""Phase 9E lightweight performance harness.

This script executes the baseline scenarios defined in:
`docs/internal/architecture/phase9e_performance_baseline.md`

Key properties:
- writes JSON + Markdown reports
- keeps partial results when a scenario fails
- supports scenario filtering for fast local iteration
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication

from models.window_config import TextWindowConfig
from ui.property_panel import PropertyPanel
from ui.property_panel_sections.text_content_section import build_text_content_section
from ui.property_panel_sections.text_style_section import build_text_style_section
from ui.tabs.info_tab import InfoTab
from windows.text_renderer import TextRenderer
from windows.text_window_parts import metadata_ops, task_ops

Numeric = int | float
Counters = dict[str, Numeric]
ScenarioFn = Callable[[], Counters]


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    name: str
    build_runner: Callable[[], ScenarioFn]


@dataclass
class ScenarioResult:
    scenario_id: str
    name: str
    status: str
    warmup: int
    samples: int
    elapsed_ms: dict[str, float]
    counters: Counters
    error: str = ""


def _git_commit(base_dir: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _ensure_qapp() -> QApplication:
    app = QApplication.instance()
    if app is not None:
        return app
    return QApplication([])


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"median": 0.0, "p95": 0.0, "max": 0.0, "min": 0.0}
    ordered = sorted(float(v) for v in values)
    median = float(statistics.median(ordered))
    if len(ordered) == 1:
        p95 = ordered[0]
    else:
        p95 = float(statistics.quantiles(ordered, n=100, method="inclusive")[94])
    return {
        "median": round(median, 4),
        "p95": round(p95, 4),
        "max": round(max(ordered), 4),
        "min": round(min(ordered), 4),
    }


def _aggregate_counters(samples: list[Counters]) -> Counters:
    if not samples:
        return {}
    buckets: dict[str, list[float]] = {}
    for sample in samples:
        for key, raw in sample.items():
            value = float(raw)
            buckets.setdefault(key, []).append(value)
    out: Counters = {}
    for key, values in buckets.items():
        mean = float(sum(values) / max(len(values), 1))
        if all(float(v).is_integer() for v in values):
            out[key] = int(round(mean))
        else:
            out[key] = round(mean, 4)
    return out


class _RendererWindowStub:
    def __init__(
        self, text: str, *, content_mode: str = "note", font_size: int = 48, task_states: list[bool] | None = None
    ):
        self.text = text
        self.content_mode = content_mode
        self.task_states = list(task_states or [])
        self.is_vertical = False

        self.font_family = "Arial"
        self.font_size = int(font_size)
        self.font_color = "#FFFFFFFF"
        self.text_opacity = 100

        self.background_visible = True
        self.background_color = "#000000FF"
        self.background_opacity = 100
        self.background_corner_ratio = 0.2

        self.background_outline_enabled = False
        self.background_outline_color = "#000000FF"
        self.background_outline_opacity = 100
        self.background_outline_width_ratio = 0.05

        self.shadow_enabled = False
        self.shadow_color = "#000000FF"
        self.shadow_opacity = 100
        self.shadow_blur = 0
        self.shadow_scale = 1.0
        self.shadow_offset_x = 0.1
        self.shadow_offset_y = 0.1

        self.outline_enabled = False
        self.outline_color = "#000000FF"
        self.outline_opacity = 100
        self.outline_width = 5.0
        self.outline_blur = 0

        self.second_outline_enabled = False
        self.second_outline_color = "#FFFFFFFF"
        self.second_outline_opacity = 100
        self.second_outline_width = 10.0
        self.second_outline_blur = 0

        self.third_outline_enabled = False
        self.third_outline_color = "#000000FF"
        self.third_outline_opacity = 100
        self.third_outline_width = 15.0
        self.third_outline_blur = 0

        self.text_gradient_enabled = False
        self.text_gradient = [(0.0, "#000000"), (1.0, "#FFFFFF")]
        self.text_gradient_angle = 0
        self.text_gradient_opacity = 100

        self.background_gradient_enabled = False
        self.background_gradient = [(0.0, "#000000"), (1.0, "#FFFFFF")]
        self.background_gradient_angle = 0
        self.background_gradient_opacity = 100

        self.horizontal_margin_ratio = 0.0
        self.vertical_margin_ratio = 0.0
        self.char_spacing_h = 0.0
        self.line_spacing_h = 0.0
        self.char_spacing_v = 0.0
        self.line_spacing_v = 0.0
        self.margin_top_ratio = 0.0
        self.margin_bottom_ratio = 0.0
        self.margin_left_ratio = 0.0
        self.margin_right_ratio = 0.0

        self.canvas_size = None
        self._pos = QPoint(0, 0)
        self._geometry = None
        self.config = TextWindowConfig(text=text, content_mode=content_mode, font_size=int(font_size), font="Arial")

    def pos(self) -> QPoint:
        return QPoint(self._pos)

    def setGeometry(self, rect) -> None:  # Qt QRect
        self._geometry = rect


class _DummyServices:
    def begin_undo_macro(self, _label: str) -> bool:
        return False

    def end_undo_macro(self) -> None:
        return None


class _TaskWindowStub:
    def __init__(self, text: str, *, task_states: list[bool] | None = None, task_mode: bool = True) -> None:
        self.text = text
        self.task_states = list(task_states or [])
        self._task_mode = bool(task_mode)
        self.undo_calls: list[tuple[str, object, object]] = []
        self.touch_count = 0
        self.title = "old"
        self.tags = ["alpha"]
        self.is_starred = False
        self.is_archived = False
        self.due_at = ""
        self.due_precision = "date"
        self.due_time = ""
        self.due_timezone = ""
        self.uuid = "bench-window"
        self._services = _DummyServices()

    def _runtime_services(self) -> _DummyServices:
        return self._services

    def is_task_mode(self) -> bool:
        return self._task_mode

    @staticmethod
    def _split_lines(text: str) -> list[str]:
        if not text:
            return []
        return str(text).splitlines()

    @staticmethod
    def _normalize_task_states(states: list[bool], total: int) -> list[bool]:
        normalized = [bool(v) for v in list(states or [])[:total]]
        if len(normalized) < total:
            normalized.extend([False] * (total - len(normalized)))
        return normalized

    def set_undoable_property(self, key: str, value: object, action: object = None) -> None:
        self.undo_calls.append((key, value, action))
        setattr(self, key, value)

    def _touch_updated_at(self) -> None:
        self.touch_count += 1

    def get_task_line_state(self, index: int) -> bool:
        return task_ops.get_task_line_state(self, index)

    def set_task_line_state(self, index: int, done: bool) -> None:
        task_ops.set_task_line_state(self, index, done)

    def toggle_task_line_state(self, index: int) -> None:
        task_ops.toggle_task_line_state(self, index)


class _BenchInfoTaskWindow:
    def __init__(self, uuid: str, text: str, due_at: str, *, done: bool, is_archived: bool, is_starred: bool) -> None:
        self.uuid = uuid
        self.text = text
        self.content_mode = "task"
        self.title = f"Task-{uuid}"
        self.tags = ["bench"]
        self.is_starred = bool(is_starred)
        self.created_at = ""
        self.updated_at = ""
        self.due_at = due_at
        self.due_time = ""
        self.due_timezone = ""
        self.due_precision = "date"
        self.is_archived = bool(is_archived)
        self._states = [bool(done)]

    def iter_task_items(self):
        return [SimpleNamespace(line_index=0, text=self.text, done=bool(self._states[0]))]


class _BenchInfoNoteWindow:
    def __init__(self, uuid: str, *, is_starred: bool, is_archived: bool) -> None:
        self.uuid = uuid
        self.text = f"Note body {uuid}"
        self.content_mode = "note"
        self.title = f"Note-{uuid}"
        self.tags = ["bench", "note"]
        self.is_starred = bool(is_starred)
        self.created_at = ""
        self.updated_at = ""
        self.due_at = ""
        self.due_time = ""
        self.due_timezone = ""
        self.due_precision = "date"
        self.is_archived = bool(is_archived)


class _InfoActionsStub:
    def get_operation_logs(self, limit=None):
        _ = limit
        return []


def _make_info_tab() -> InfoTab:
    _ensure_qapp()

    task_windows: list[object] = []
    for i in range(200):
        if i % 3 == 0:
            due_at = "2001-01-01T00:00:00"
        elif i % 3 == 1:
            due_at = "2999-01-01T00:00:00"
        else:
            due_at = ""
        task_windows.append(
            _BenchInfoTaskWindow(
                uuid=f"t-{i}",
                text=f"task-{i}",
                due_at=due_at,
                done=(i % 4 == 0),
                is_archived=(i % 10 == 0),
                is_starred=(i % 8 == 0),
            )
        )

    note_windows = [
        _BenchInfoNoteWindow(uuid=f"n-{i}", is_starred=(i % 5 == 0), is_archived=(i % 12 == 0)) for i in range(300)
    ]
    text_windows = [*task_windows, *note_windows]

    app_settings = SimpleNamespace(
        main_window_width=0,
        main_window_height=0,
        main_window_pos_x=None,
        main_window_pos_y=None,
        info_view_presets=[],
        info_last_view_preset_id="builtin:all",
        info_operation_logs=[],
        info_layout_mode="auto",
        info_advanced_filters_expanded=False,
    )
    settings_manager = SimpleNamespace(save_app_settings=lambda: None)
    main_controller = SimpleNamespace(info_actions=_InfoActionsStub())
    mw = SimpleNamespace(
        window_manager=SimpleNamespace(text_windows=text_windows),
        app_settings=app_settings,
        settings_manager=settings_manager,
        main_controller=main_controller,
    )
    return InfoTab(mw)


def _count_task_rows(tab: InfoTab) -> int:
    count = 0
    for i in range(tab.tasks_list.count()):
        item = tab.tasks_list.item(i)
        if item is None:
            continue
        key = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if ":" in key:
            count += 1
    return count


def _count_note_rows(tab: InfoTab) -> int:
    count = 0
    for i in range(tab.notes_list.count()):
        item = tab.notes_list.item(i)
        if item is None:
            continue
        key = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if key:
            count += 1
    return count


class _PropertyTarget:
    def __init__(self) -> None:
        self._task_mode = False
        self.mode_calls: list[str] = []
        self.update_text_calls = 0
        self.undo_calls: list[tuple[str, object, object]] = []
        self._tick = 0

        self.text = "benchmark text"
        self.is_vertical = False
        self.title = "Bench Title"
        self.tags = ["alpha", "beta"]
        self.due_at = "2026-03-10T00:00:00"
        self.due_precision = "date"
        self.due_time = ""
        self.due_timezone = ""
        self.is_starred = True
        self.is_archived = False

        self.font_family = "Arial"
        self.font_size = 24
        self.font_color = "#FFFFFFFF"
        self.text_opacity = 85
        self.text_gradient_enabled = True
        self.text_gradient_opacity = 70
        self.text_gradient = [(0.0, "#000000"), (1.0, "#FFFFFF")]
        self.text_gradient_angle = 0

        self.background_visible = True
        self.background_color = "#000000FF"
        self.background_opacity = 100
        self.background_corner_ratio = 0.2
        self.background_gradient_enabled = False
        self.background_gradient_opacity = 100
        self.background_gradient = [(0.0, "#000000"), (1.0, "#FFFFFF")]
        self.background_gradient_angle = 0

        self.shadow_enabled = False
        self.shadow_color = "#000000FF"
        self.shadow_opacity = 100
        self.shadow_blur = 0
        self.shadow_offset_x = 0.1
        self.shadow_offset_y = 0.1

        self.outline_enabled = False
        self.outline_color = "#000000FF"
        self.outline_opacity = 100
        self.outline_width = 5.0
        self.outline_blur = 0

        self.second_outline_enabled = False
        self.second_outline_color = "#FFFFFFFF"
        self.second_outline_opacity = 100
        self.second_outline_width = 10.0
        self.second_outline_blur = 0

        self.third_outline_enabled = False
        self.third_outline_color = "#000000FF"
        self.third_outline_opacity = 100
        self.third_outline_width = 15.0
        self.third_outline_blur = 0

        self.background_outline_enabled = False
        self.background_outline_color = "#000000FF"
        self.background_outline_opacity = 100
        self.background_outline_width_ratio = 0.05

    def is_task_mode(self) -> bool:
        return self._task_mode

    def set_content_mode(self, mode: str) -> None:
        self.mode_calls.append(mode)
        self._task_mode = mode == "task"

    def get_task_progress(self) -> tuple[int, int]:
        return 1, 3

    def complete_all_tasks(self) -> None:
        return None

    def uncomplete_all_tasks(self) -> None:
        return None

    def set_undoable_property(self, key: str, value: object, action: object = None) -> None:
        self.undo_calls.append((key, value, action))
        setattr(self, key, value)

    def update_text(self) -> None:
        self.update_text_calls += 1


def _make_property_panel() -> tuple[PropertyPanel, _PropertyTarget]:
    _ensure_qapp()
    mw = SimpleNamespace(
        info_tab=SimpleNamespace(refresh_data=lambda: None),
        main_controller=SimpleNamespace(txt_actions=SimpleNamespace(save_as_default=lambda: None)),
    )
    panel = PropertyPanel(main_window=mw)
    target = _PropertyTarget()
    panel.current_target = target
    build_text_content_section(panel, target)
    build_text_style_section(panel, target)
    return panel, target


def _scenario_s01_renderer_render() -> ScenarioFn:
    _ensure_qapp()
    renderer = TextRenderer()
    window = _RendererWindowStub("新しいテキスト benchmark sample", content_mode="note", font_size=48)

    def run() -> Counters:
        pixmap = renderer.render(window)
        return {
            "render_call_count": 1,
            "pixmap_width": pixmap.width(),
            "pixmap_height": pixmap.height(),
        }

    return run


def _scenario_s02_renderer_task_rects_and_render() -> ScenarioFn:
    _ensure_qapp()
    renderer = TextRenderer()
    lines = [f"task-{i}" for i in range(100)]
    window = _RendererWindowStub(
        "\n".join(lines),
        content_mode="task",
        font_size=36,
        task_states=[(i % 2 == 0) for i in range(100)],
    )

    def run() -> Counters:
        rects = renderer.get_task_line_rects(window)
        _ = renderer.render(window)
        return {
            "render_call_count": 1,
            "task_rect_count": len(rects),
        }

    return run


def _scenario_s03_task_toggle() -> ScenarioFn:
    window = _TaskWindowStub(
        "\n".join(f"line-{i}" for i in range(100)),
        task_states=[False] * 100,
        task_mode=True,
    )

    def run() -> Counters:
        before = window.touch_count
        for i in range(10):
            task_ops.toggle_task_line_by_index(window, i)
        changed = window.touch_count - before
        return {
            "updated_line_count": changed,
            "total_lines": len(window._split_lines(window.text)),
        }

    return run


def _scenario_s04_metadata_update() -> ScenarioFn:
    window = _TaskWindowStub("single-line", task_states=[False], task_mode=False)
    rev = {"n": 0}

    def run() -> Counters:
        rev["n"] += 1
        title = f"bench-title-{rev['n']}"
        before = len(window.undo_calls)
        metadata_ops.set_title_and_tags(window, title, ["alpha", "beta", "gamma"])
        metadata_ops.set_due_at(window, "2026-03-10")
        changed_calls = len(window.undo_calls) - before

        before_noop = len(window.undo_calls)
        metadata_ops.set_title_and_tags(window, window.title, list(window.tags))
        metadata_ops.set_due_at(window, "2026-03-10")
        noop_delta = len(window.undo_calls) - before_noop
        no_op_ratio = 1.0 if noop_delta == 0 else 0.0
        return {
            "mutation_calls": changed_calls,
            "no_op_ratio": no_op_ratio,
        }

    return run


def _scenario_s05_info_refresh_all() -> ScenarioFn:
    tab = _make_info_tab()

    def run() -> Counters:
        tab.refresh_data(immediate=True)
        return {
            "task_item_count": _count_task_rows(tab),
            "note_item_count": _count_note_rows(tab),
        }

    return run


def _scenario_s06_info_filter_switch() -> ScenarioFn:
    tab = _make_info_tab()
    idx_today = tab.cmb_due_filter.findData("today")
    idx_overdue = tab.cmb_due_filter.findData("overdue")
    idx_starred_view = tab.cmb_smart_view.findData("starred")
    idx_all_view = tab.cmb_smart_view.findData("all")

    def run() -> Counters:
        tab.cmb_due_filter.setCurrentIndex(idx_today if idx_today >= 0 else 0)
        tab.refresh_data(immediate=True)
        tab.cmb_due_filter.setCurrentIndex(idx_overdue if idx_overdue >= 0 else 0)
        tab.refresh_data(immediate=True)
        tab.cmb_smart_view.setCurrentIndex(idx_starred_view if idx_starred_view >= 0 else 0)
        tab.refresh_data(immediate=True)
        tab.cmb_smart_view.setCurrentIndex(idx_all_view if idx_all_view >= 0 else 0)
        tab.refresh_data(immediate=True)
        return {
            "filter_apply_count": 3,
            "task_item_count": _count_task_rows(tab),
            "note_item_count": _count_note_rows(tab),
        }

    return run


def _scenario_s07_property_content_sync() -> ScenarioFn:
    panel, target = _make_property_panel()
    tick = {"n": 0}

    def run() -> Counters:
        tick["n"] += 1
        target.title = f"content-{tick['n']}"
        target.tags = ["alpha", f"tag-{tick['n']}"]
        target.due_at = "2026-03-10T00:00:00" if tick["n"] % 2 == 0 else "2026-03-11T00:00:00"
        panel.current_target = target
        panel._update_text_values()
        widget_count = sum(
            int(widget is not None)
            for widget in [
                panel.edit_note_title,
                panel.edit_note_tags,
                panel.edit_note_due_at,
                panel.cmb_note_due_precision,
                panel.edit_note_due_time,
                panel.edit_note_due_timezone,
                panel.btn_note_star,
                panel.btn_note_archived,
            ]
        )
        return {"widget_update_count": widget_count}

    return run


def _scenario_s08_property_style_sync() -> ScenarioFn:
    panel, target = _make_property_panel()
    tick = {"n": 0}

    def run() -> Counters:
        tick["n"] += 1
        target.font_size = 20 + (tick["n"] % 10)
        target.text_opacity = 50 + (tick["n"] % 40)
        target.background_opacity = 60 + (tick["n"] % 30)
        target.shadow_enabled = (tick["n"] % 2) == 0
        panel.current_target = target
        panel._update_text_values()
        widget_count = sum(
            int(widget is not None)
            for widget in [
                panel.btn_text_font,
                panel.spin_text_font_size,
                panel.btn_text_color,
                panel.spin_text_opacity,
                panel.btn_bg_color,
                panel.spin_bg_opacity,
                panel.btn_shadow_color,
                panel.spin_shadow_blur,
            ]
        )
        return {"widget_update_count": widget_count}

    return run


def _scenario_specs() -> list[ScenarioSpec]:
    return [
        ScenarioSpec("P9E-S01", "TextRenderer render (DS-01)", _scenario_s01_renderer_render),
        ScenarioSpec(
            "P9E-S02", "TextRenderer task rects + render (DS-02)", _scenario_s02_renderer_task_rects_and_render
        ),
        ScenarioSpec("P9E-S03", "TextWindow task toggle burst", _scenario_s03_task_toggle),
        ScenarioSpec("P9E-S04", "TextWindow metadata update/no-op ratio", _scenario_s04_metadata_update),
        ScenarioSpec("P9E-S05", "InfoTab refresh all filter", _scenario_s05_info_refresh_all),
        ScenarioSpec("P9E-S06", "InfoTab filter switch sequence", _scenario_s06_info_filter_switch),
        ScenarioSpec("P9E-S07", "PropertyPanel text content sync", _scenario_s07_property_content_sync),
        ScenarioSpec("P9E-S08", "PropertyPanel text style sync", _scenario_s08_property_style_sync),
    ]


def _run_one(spec: ScenarioSpec, *, warmup: int, samples: int) -> ScenarioResult:
    runner = spec.build_runner()
    durations: list[float] = []
    counter_samples: list[Counters] = []

    try:
        for _ in range(max(0, warmup)):
            _ = runner()

        for _ in range(max(1, samples)):
            t0 = perf_counter()
            counters = runner()
            dt_ms = (perf_counter() - t0) * 1000.0
            durations.append(dt_ms)
            counter_samples.append(counters)

        return ScenarioResult(
            scenario_id=spec.scenario_id,
            name=spec.name,
            status="ok",
            warmup=warmup,
            samples=max(1, samples),
            elapsed_ms=_stats(durations),
            counters=_aggregate_counters(counter_samples),
        )
    except Exception:
        err = traceback.format_exc()
        return ScenarioResult(
            scenario_id=spec.scenario_id,
            name=spec.name,
            status="error",
            warmup=warmup,
            samples=len(durations),
            elapsed_ms=_stats(durations),
            counters=_aggregate_counters(counter_samples),
            error=err.strip(),
        )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_markdown(path: Path, payload: dict[str, object], results: list[ScenarioResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = payload["meta"]
    with path.open("w", encoding="utf-8") as f:
        f.write("# Phase 9E Measurement Report\n")
        f.write(f"- Timestamp: `{meta['timestamp']}`\n")
        f.write(f"- Git commit: `{meta['git_commit']}`\n")
        f.write(f"- Python: `{meta['python']}`\n")
        f.write(f"- OS: `{meta['os']}`\n")
        f.write(f"- Window size baseline: `{meta['window_size'][0]} x {meta['window_size'][1]}`\n")
        f.write(f"- Warmup/Samples: `{meta['warmup']}/{meta['samples']}`\n\n")

        f.write("## Scenario Summary\n\n")
        f.write("| ID | Status | Median ms | p95 ms | Max ms |\n")
        f.write("|---|---|---:|---:|---:|\n")
        for r in results:
            f.write(
                f"| {r.scenario_id} | {r.status} | {r.elapsed_ms.get('median', 0.0):.4f} | "
                f"{r.elapsed_ms.get('p95', 0.0):.4f} | {r.elapsed_ms.get('max', 0.0):.4f} |\n"
            )

        f.write("\n## Scenario Details\n\n")
        for r in results:
            f.write(f"### {r.scenario_id} - {r.name}\n")
            f.write(f"- Status: `{r.status}`\n")
            f.write(
                f"- Elapsed ms: median={r.elapsed_ms.get('median', 0.0):.4f}, "
                f"p95={r.elapsed_ms.get('p95', 0.0):.4f}, max={r.elapsed_ms.get('max', 0.0):.4f}\n"
            )
            if r.counters:
                f.write("- Counters:\n")
                for key, value in sorted(r.counters.items()):
                    f.write(f"  - `{key}`: `{value}`\n")
            if r.error:
                f.write("- Error:\n")
                f.write("```text\n")
                f.write(r.error + "\n")
                f.write("```\n")
            f.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 9E lightweight performance baseline scenarios.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Project base directory (default: repository root).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for JSON/Markdown reports (default: <base-dir>/docs/internal/architecture/performance_runs).",
    )
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per scenario (default: 1).")
    parser.add_argument("--samples", type=int, default=5, help="Measured runs per scenario (default: 5).")
    parser.add_argument(
        "--scenario",
        action="append",
        default=None,
        help="Scenario ID to run. Can be specified multiple times (e.g. --scenario P9E-S01 --scenario P9E-S05).",
    )
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenario IDs and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    base_dir = args.base_dir.resolve()
    specs = _scenario_specs()
    by_id = {spec.scenario_id: spec for spec in specs}

    if args.list_scenarios:
        print("Available scenarios:")
        for spec in specs:
            print(f"- {spec.scenario_id}: {spec.name}")
        return 0

    selected_ids = list(args.scenario or [])
    if selected_ids:
        unknown = [sid for sid in selected_ids if sid not in by_id]
        if unknown:
            print(f"Unknown scenario IDs: {', '.join(unknown)}")
            return 2
        run_specs = [by_id[sid] for sid in selected_ids]
    else:
        run_specs = specs

    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else (base_dir / "docs" / "internal" / "architecture" / "performance_runs")
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"phase9e_measurement_{stamp}.json"
    md_path = output_dir / f"phase9e_measurement_{stamp}.md"

    results: list[ScenarioResult] = []
    for spec in run_specs:
        print(f"[Phase9E] running {spec.scenario_id} ...")
        result = _run_one(spec, warmup=max(0, int(args.warmup)), samples=max(1, int(args.samples)))
        results.append(result)
        print(
            f"[Phase9E] {spec.scenario_id} status={result.status} median={result.elapsed_ms.get('median', 0.0):.4f}ms"
        )

    payload: dict[str, object] = {
        "meta": {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "git_commit": _git_commit(base_dir),
            "python": sys.version.split()[0],
            "os": f"{platform.system()}-{platform.release()}",
            "window_size": [433, 640],
            "warmup": max(0, int(args.warmup)),
            "samples": max(1, int(args.samples)),
            "scenarios": [spec.scenario_id for spec in run_specs],
        },
        "scenarios": [
            {
                "id": r.scenario_id,
                "name": r.name,
                "status": r.status,
                "warmup": r.warmup,
                "samples": r.samples,
                "elapsed_ms": r.elapsed_ms,
                "counters": r.counters,
                "error": r.error,
            }
            for r in results
        ],
    }

    _write_json(json_path, payload)
    _write_markdown(md_path, payload, results)

    print(f"[Phase9E] json report: {json_path}")
    print(f"[Phase9E] md report:   {md_path}")

    failed = [r for r in results if r.status != "ok"]
    if failed:
        print(f"[Phase9E] completed with {len(failed)} failed scenario(s). Partial results were saved.")
        return 1
    print("[Phase9E] completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from ui.tabs.about_tab import AboutTab


def _make_main_window_stub() -> SimpleNamespace:
    settings = SimpleNamespace(
        about_section_state={},
        render_debounce_ms=25,
        wheel_debounce_ms=50,
        glyph_cache_size=512,
    )
    settings_manager = SimpleNamespace(save_app_settings=MagicMock())
    return SimpleNamespace(
        app_settings=settings,
        settings_manager=settings_manager,
        show_manual_dialog=MagicMock(),
        show_license_dialog=MagicMock(),
        show_about_dialog=MagicMock(),
        open_log_folder=MagicMock(),
        open_shop_page=MagicMock(),
        copy_shop_url=MagicMock(),
        apply_performance_settings=MagicMock(),
    )


def test_about_tab_default_sections_state(qapp) -> None:
    _ = qapp
    mw = _make_main_window_stub()
    tab = AboutTab(mw)
    assert tab.edition_group.toggle_button.isChecked() is True
    assert tab.system_group.toggle_button.isChecked() is True
    assert tab.shortcuts_group.toggle_button.isChecked() is False
    assert tab.perf_group.toggle_button.isChecked() is False
    tab.deleteLater()


def test_about_tab_compact_hides_hints_and_sets_tooltips(qapp) -> None:
    mw = _make_main_window_stub()
    tab = AboutTab(mw)

    tab.set_compact_mode(True)
    qapp.processEvents()

    assert tab.hint_debounce.isHidden() is True
    assert tab.hint_wheel.isHidden() is True
    assert tab.hint_cache.isHidden() is True
    assert tab.spin_debounce.toolTip()
    assert tab.spin_wheel.toolTip()
    assert tab.spin_cache.toolTip()
    tab.deleteLater()


def test_about_tab_comfortable_restores_hints(qapp) -> None:
    mw = _make_main_window_stub()
    tab = AboutTab(mw)
    tab.perf_group.toggle_button.setChecked(True)
    qapp.processEvents()

    tab.set_compact_mode(True)
    qapp.processEvents()
    tab.set_compact_mode(False)
    qapp.processEvents()

    assert tab.hint_debounce.isHidden() is False
    assert tab.hint_wheel.isHidden() is False
    assert tab.hint_cache.isHidden() is False
    assert tab.spin_debounce.toolTip() == ""
    assert tab.spin_wheel.toolTip() == ""
    assert tab.spin_cache.toolTip() == ""
    tab.deleteLater()


def test_about_tab_section_state_persists(qapp) -> None:
    _ = qapp
    mw = _make_main_window_stub()
    tab = AboutTab(mw)

    tab.shortcuts_group.toggle_button.setChecked(True)
    tab.perf_group.toggle_button.setChecked(True)

    assert mw.app_settings.about_section_state.get("shortcuts") is True
    assert mw.app_settings.about_section_state.get("performance") is True
    assert mw.settings_manager.save_app_settings.called
    tab.deleteLater()


def test_about_tab_loads_saved_section_state(qapp) -> None:
    _ = qapp
    mw = _make_main_window_stub()
    mw.app_settings.about_section_state = {
        "edition": False,
        "system": False,
        "shortcuts": True,
        "performance": True,
    }
    tab = AboutTab(mw)

    assert tab.edition_group.toggle_button.isChecked() is False
    assert tab.system_group.toggle_button.isChecked() is False
    assert tab.shortcuts_group.toggle_button.isChecked() is True
    assert tab.perf_group.toggle_button.isChecked() is True
    tab.deleteLater()


def test_about_tab_overflow_actions_are_reachable(qapp) -> None:
    _ = qapp
    mw = _make_main_window_stub()
    tab = AboutTab(mw)

    tab.act_open_log.trigger()
    tab.act_open_shop.trigger()
    tab.act_copy_shop_url.trigger()

    assert mw.open_log_folder.called
    assert mw.open_shop_page.called
    assert mw.copy_shop_url.called
    tab.deleteLater()

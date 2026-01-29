# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QInputDialog, QMessageBox

from utils.error_reporter import ErrorNotifyState, report_unexpected_error
from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class SceneActions:
    """
    シーン・カテゴリ操作に関するビジネスロジックを管理するクラス。
    MainWindowのラッパーメソッドを代替する。
    """

    def __init__(self, mw: MainWindow) -> None:
        self.mw = mw
        self._err_state = ErrorNotifyState()

    def add_new_category(self) -> None:
        """新しいカテゴリを追加する。"""
        try:
            name, ok = QInputDialog.getText(self.mw, tr("btn_add_category"), tr("msg_input_name"))
            if ok and name:
                # category_manager が存在すればそれを使う、なければ簡易実装
                # 現状の実装に合わせて scenes 辞書を直接操作するか、CategoryManager を探す
                # ここでは MainWindow.scenes を操作していた既存ロジックを模倣・復元する

                if name in self.mw.scenes:
                    QMessageBox.warning(self.mw, tr("msg_warning"), tr("msg_duplicate_name"))
                    return

                self.mw.scenes[name] = {}
                # UI更新 (SceneTabのrefresh)
                if hasattr(self.mw, "scene_tab") and hasattr(self.mw.scene_tab, "refresh_category_list"):
                    self.mw.scene_tab.refresh_category_list()

                # DB保存などがもしあればここで呼ぶ
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to add category", e, self._err_state)

    def add_new_scene(self) -> None:
        """現在のカテゴリに新しいシーンを追加する。"""
        try:
            # 1. カテゴリ選択チェック
            # SceneTabから現在選択中のカテゴリを取得する必要がある
            current_category = None
            if hasattr(self.mw, "scene_tab"):
                current_category = self.mw.scene_tab.get_current_category()

            if not current_category:
                QMessageBox.warning(self.mw, tr("msg_warning"), tr("msg_select_category_first"))
                return

            name, ok = QInputDialog.getText(self.mw, tr("btn_add_scene"), tr("msg_input_name"))
            if ok and name:
                category_data = self.mw.scenes.get(current_category, {})
                if name in category_data:
                    QMessageBox.warning(self.mw, tr("msg_warning"), tr("msg_duplicate_name"))
                    return

                # 現在のシーン状態を取得して保存
                scene_data = self.mw.file_manager.get_scene_data()
                self.mw.scenes[current_category][name] = scene_data

                # UI更新
                if hasattr(self.mw, "scene_tab"):
                    self.mw.scene_tab.refresh_scene_list()

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to add scene", e, self._err_state)

    def load_selected_scene(self) -> None:
        """選択されたシーンをロードする。"""
        try:
            if not hasattr(self.mw, "scene_tab"):
                return

            category = self.mw.scene_tab.get_current_category()
            scene_name = self.mw.scene_tab.get_current_scene()

            if not category or not scene_name:
                return

            scene_data = self.mw.scenes.get(category, {}).get(scene_name)
            if scene_data:
                self.mw.file_manager.load_scene_from_data(scene_data)

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to load scene", e, self._err_state)

    def update_selected_scene(self) -> None:
        """現在表示中のウィンドウ状態で、選択されたシーンデータを上書き更新する。"""
        try:
            if not hasattr(self.mw, "scene_tab"):
                return

            category = self.mw.scene_tab.get_current_category()
            scene_name = self.mw.scene_tab.get_current_scene()

            if not category or not scene_name:
                QMessageBox.warning(self.mw, tr("msg_warning"), tr("msg_select_scene_first"))
                return

            ret = QMessageBox.question(
                self.mw,
                tr("btn_update_scene"),
                tr("msg_confirm_update_scene").format(scene_name),
                QMessageBox.Yes | QMessageBox.No,
            )
            if ret != QMessageBox.Yes:
                return

            new_data = self.mw.file_manager.get_scene_data()
            self.mw.scenes[category][scene_name] = new_data

            if hasattr(self.mw, "show_status_message"):
                self.mw.show_status_message(tr("msg_scene_updated"))

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to update scene", e, self._err_state)

    def delete_selected_item(self) -> None:
        """選択されたカテゴリまたはシーンを削除する。"""
        try:
            if not hasattr(self.mw, "scene_tab"):
                return

            # SceneTab側で何が選ばれているか判定するのは複雑なので、
            # SceneTab自体に delete_current_selection のようなメソッドがあれば委譲したいが
            # ここでは「シーンが選ばれていればシーン削除、なければカテゴリ削除」のようなロジックにする

            category = self.mw.scene_tab.get_current_category()
            scene = self.mw.scene_tab.get_current_scene()

            target_name = scene if scene else category
            if not target_name:
                return

            # シーンかカテゴリかでメッセージを使い分ける
            if scene:
                msg = tr("msg_confirm_delete").format(target_name)
            else:
                msg = tr("msg_confirm_delete_category").format(target_name)

            ret = QMessageBox.question(self.mw, tr("btn_delete_scene"), msg, QMessageBox.Yes | QMessageBox.No)
            if ret != QMessageBox.Yes:
                return

            if scene:
                # シーン削除
                if category in self.mw.scenes and scene in self.mw.scenes[category]:
                    del self.mw.scenes[category][scene]
                    self.mw.scene_tab.refresh_scene_list()
            else:
                # カテゴリ削除
                if category in self.mw.scenes:
                    del self.mw.scenes[category]
                    self.mw.scene_tab.refresh_category_list()

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to delete item", e, self._err_state)

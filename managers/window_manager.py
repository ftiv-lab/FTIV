# managers/window_manager.py

import logging
import math
import traceback
from typing import TYPE_CHECKING, Any, List, Optional

from PySide6.QtCore import QObject, QPoint, Qt, Signal
from PySide6.QtWidgets import QMessageBox

from utils.edition import get_edition, get_limits, is_over_limit, show_limit_message
from utils.translator import tr
from windows.connector import ConnectorLine
from windows.image_window import ImageWindow
from windows.text_window import TextWindow

if TYPE_CHECKING:
    from ui.main_window import MainWindow

# ロガーの取得
logger = logging.getLogger(__name__)


class WindowManager(QObject):
    """
    シーン内の全てのオブジェクト（テキスト、画像、接続線）の生成、削除、選択、
    およびシグナル受信を一元管理するクラス。
    MainWindowの負担を軽減するために分離。
    """

    # UI更新用シグナル
    sig_selection_changed = Signal(object)  # 選択対象が変わったとき
    sig_status_message = Signal(str)  # フッターメッセージ用
    sig_undo_command_requested = Signal(object)  # Undoコマンド発行用

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.main_window = main_window  # 親ウィジェットとして保持

        # データコンテナ（ここがデータの「正」となる）
        self.text_windows: List[TextWindow] = []
        self.image_windows: List[ImageWindow] = []
        self.connectors: List[ConnectorLine] = []

        # 状態
        self.last_selected_window: Optional[QObject] = None

    @property
    def all_windows(self):
        """テキストと画像の全ウィンドウリストを返す"""
        return self.text_windows + self.image_windows

    def _prune_invalid_refs(self) -> None:
        """WindowManager が保持する参照から、無効なQObject参照を除去する。

        目的:
            - close/delete のタイミング差で、すでに破棄された参照が残るのを防ぐ
            - 保存/一括操作/選択変更での RuntimeError を減らす

        注意:
            - できるだけ軽くする（頻繁に呼んでも落ちないように）
        """
        try:
            import shiboken6
        except Exception as e:
            # shiboken6 が使えない環境では何もしない（落とさない）
            logger.debug(f"shiboken6 import failed: {e}")
            return

        # --- text_windows / image_windows ---
        try:
            self.text_windows = [w for w in list(self.text_windows) if w is not None and shiboken6.isValid(w)]
        except Exception as e:
            logger.debug(f"Error pruning text_windows: {e}")

        try:
            self.image_windows = [w for w in list(self.image_windows) if w is not None and shiboken6.isValid(w)]
        except Exception as e:
            logger.debug(f"Error pruning image_windows: {e}")

        # --- connectors ---
        # connectors は start/end のどちらかが死んでいたら削除する
        try:
            valid_connectors: list[Any] = []
            for c in list(self.connectors):
                if c is None or not shiboken6.isValid(c):
                    continue

                sw = getattr(c, "start_window", None)
                ew = getattr(c, "end_window", None)

                # start/end が無効なら削除対象
                if sw is None or ew is None:
                    try:
                        self.delete_connector(c)
                    except Exception as e:
                        logger.debug(f"Error deleting invalid connector: {e}")
                    continue

                try:
                    if not shiboken6.isValid(sw) or not shiboken6.isValid(ew):
                        try:
                            self.delete_connector(c)
                        except Exception:
                            logger.debug("Failed to delete connector (inner)", exc_info=True)
                        continue
                except Exception:
                    # start/end の isValid 判定ができないなら残す（安全側）
                    pass

                valid_connectors.append(c)

            self.connectors = valid_connectors
        except Exception:
            # 全体的なエラーは無視せずログに残す
            logger.debug("Error in _prune_invalid_refs loop", exc_info=True)

    # ==========================================
    # Window Creation (生成)
    # ==========================================

    def add_text_window(
        self,
        text: Optional[str] = None,
        pos: Optional[QPoint] = None,
        suppress_limit_message: bool = False,
    ) -> Optional[TextWindow]:
        """テキストウィンドウを生成・登録・表示する。

        Args:
            text (Optional[str]): 表示するテキスト。Noneの場合はデフォルト値を使用。
            pos (Optional[QPoint]): 表示位置。Noneの場合はメインウィンドウの相対位置を使用。
            suppress_limit_message (bool): True の場合、上限制限メッセージを出さない。

        Returns:
            Optional[TextWindow]: 生成されたテキストウィンドウ。制限到達時は None。
        """
        ed = get_edition(self.main_window, getattr(self.main_window, "base_directory", None))
        limits = get_limits(ed)
        if is_over_limit(len(self.text_windows), limits.max_text_windows):
            show_limit_message(self.main_window, "msg_limit_text_windows", suppress=suppress_limit_message)
            return None

        if text is None:
            text = tr("new_text_default")

        if pos is None:
            pos = self.main_window.mapToGlobal(QPoint(100, 100))

        window = TextWindow(self.main_window, text, pos)

        # --- Archetype (Default Styles) Application ---
        try:
            if hasattr(self.main_window, "settings_manager"):
                archetype = self.main_window.settings_manager.load_text_archetype()
                if archetype:
                    # Apply all settings from archetype to window config
                    # WindowConfigBase inherits from Pydantic BaseModel, so we can use model_validate
                    # but we want to MERGE with existing instance-specific data (uuid, position, text)
                    for key, value in archetype.items():
                        if hasattr(window.config, key) and key not in ("uuid", "position", "text"):
                            try:
                                setattr(window.config, key, value)
                            except Exception as e:
                                logger.debug(f"Failed to apply archetype key {key}: {e}")

                    # Update window state from config
                    if hasattr(window, "update_text"):
                        window.update_text()
        except Exception as e:
            logger.warning(f"Failed to apply text archetype during creation: {e}")

        self._setup_window_connections(window)

        self.text_windows.append(window)
        window.show()

        self.set_selected_window(window)

        logger.info(f"TextWindow created: UUID={window.uuid}, Text='{text[:20]}...'")
        return window

    def add_image_window(
        self,
        image_path: str,
        pos: Optional[QPoint] = None,
        suppress_limit_message: bool = False,
    ) -> Optional[ImageWindow]:
        """画像ウィンドウを生成・登録・表示する。

        Args:
            image_path (str): 画像ファイルのパス。
            pos (Optional[QPoint]): 表示位置。
            suppress_limit_message (bool): True の場合、上限制限メッセージを出さない。

        Returns:
            Optional[ImageWindow]: 生成されたウィンドウ。失敗時はNone。
        """
        ed = get_edition(self.main_window, getattr(self.main_window, "base_directory", None))
        limits = get_limits(ed)
        if is_over_limit(len(self.image_windows), limits.max_image_windows):
            show_limit_message(self.main_window, "msg_limit_image_windows", suppress=suppress_limit_message)
            return None

        if pos is None:
            pos = self.main_window.mapToGlobal(QPoint(150, 150))

        try:
            window = ImageWindow(self.main_window, image_path, position=pos)

            self._setup_window_connections(window)

            self.image_windows.append(window)
            window.show()
            self.set_selected_window(window)

            logger.info(f"ImageWindow created: UUID={window.uuid}, Path='{image_path}'")
            return window

        except Exception as e:
            error_detail = traceback.format_exc()
            logger.error(f"Error adding image window: {e}\n{error_detail}")
            QMessageBox.critical(self.main_window, tr("msg_error"), f"Failed to add image: {e}")
            return None

    def add_connector(
        self, start_window: "TextWindow | ImageWindow", end_window: "TextWindow | ImageWindow"
    ) -> Optional[ConnectorLine]:
        """2つのウィンドウ間に接続線を生成する。

        Args:
            start_window (TextWindow | ImageWindow): 開始地点のウィンドウ。
            end_window (TextWindow | ImageWindow): 終了地点のウィンドウ。

        Returns:
            Optional[ConnectorLine]: 生成されたコネクタ。既に存在する場合や失敗時はNone。
        """
        for conn in self.connectors:
            if (conn.start_window == start_window and conn.end_window == end_window) or (
                conn.start_window == end_window and conn.end_window == start_window
            ):
                logger.warning(f"Connector already exists between {start_window.uuid} and {end_window.uuid}")
                return None

        line = ConnectorLine(
            start_window,
            end_window,
            parent=self.main_window,
            color=self.main_window.default_line_color,
            width=self.main_window.default_line_width,
        )

        line.sig_connector_selected.connect(self.set_selected_window)
        line.sig_connector_deleted.connect(self.delete_connector)

        self.connectors.append(line)
        start_window.connected_lines.append(line)
        end_window.connected_lines.append(line)

        self.sig_status_message.emit(tr("msg_conn_success"))
        logger.info(f"Connector created: {start_window.uuid} <-> {end_window.uuid}")

        return line

    def _setup_window_connections(self, window: "TextWindow | ImageWindow"):
        """
        ウィンドウからのシグナルを安全に接続する。
        属性（シグナル）が存在しない場合はスキップすることで、
        未改修のTextWindowクラスでもエラーにならないようにする。
        """

        # ヘルパー関数: 安全な接続
        def safe_connect(signal_name: str, slot: Any):
            if hasattr(window, signal_name):
                getattr(window, signal_name).connect(slot)

        # 1. 基本イベント
        safe_connect("sig_window_selected", self.set_selected_window)
        safe_connect("sig_window_closed", self.remove_window)

        # 2. Undoコマンド
        safe_connect("sig_push_undo_command", self.sig_undo_command_requested.emit)

        # 3. 接続・グループ化
        safe_connect("sig_connect_requested", self.handle_connect_request)
        safe_connect("sig_disconnect_requested", self.handle_disconnect_request)
        safe_connect("sig_group_requested", self.handle_group_request)
        safe_connect("sig_ungroup_requested", self.handle_ungroup_request)

        # 4. TextWindow固有
        if isinstance(window, TextWindow):
            safe_connect("sig_clone_requested", self.clone_text_window)
            safe_connect("sig_create_child_requested", lambda w: self.create_related_node(w, "child"))
            safe_connect("sig_create_sibling_requested", lambda w: self.create_related_node(w, "sibling"))
            safe_connect("sig_navigate_requested", self.navigate_selection)

            # スタイル関連
            if hasattr(self.main_window, "style_manager"):
                safe_connect("sig_open_style_gallery_requested", lambda w: self._open_style_gallery(w))
                safe_connect("sig_save_style_requested", lambda w: self.main_window.style_manager.save_text_style(w))
                safe_connect(
                    "sig_load_style_file_requested", lambda w: self.main_window.style_manager.load_text_style(w)
                )

        # 5. ImageWindow固有
        if isinstance(window, ImageWindow):
            safe_connect("sig_clone_requested", self.clone_image_window)
            safe_connect("sig_add_new_image_requested", self.main_window.img_actions.add_new_image)
            safe_connect("sig_reselect_image_requested", lambda w: self._reselect_image(w))

        # 6. プロパティパネル関連
        safe_connect("sig_request_property_panel", self.main_window.on_request_property_panel)
        safe_connect("sig_properties_changed", self.main_window.on_properties_changed)

        # 7. ウィンドウ移動時の処理
        safe_connect("sig_window_moved", self.main_window.on_window_moved)

    # ==========================================
    # Window Removal (削除・クリア)
    # ==========================================

    def close_all_image_windows(self) -> None:
        """全てのImageWindowを閉じる。"""
        # リストのコピーを作成してイテレート（closeでリストから削除されるため）
        for w in list(self.image_windows):
            try:
                w.close()
            except Exception:
                logger.error("Failed to close image window", exc_info=True)

    def close_all_text_windows(self) -> None:
        """全てのTextWindowを閉じる。"""
        for w in list(self.text_windows):
            try:
                w.close()
            except Exception:
                logger.error("Failed to close text window", exc_info=True)

    def remove_window(self, window: "TextWindow | ImageWindow") -> None:
        """リストからウィンドウを削除し、関連するコネクタも掃除する。

        Args:
            window (TextWindow | ImageWindow): 削除対象のウィンドウインスタンス。
        """
        try:
            w_uuid = getattr(window, "uuid", "")
            w_type = "Text" if window in self.text_windows else "Image"

            # --- 1) 親子関係（親→子）を安全に解除 ---
            try:
                parent_uuid = getattr(window, "parent_window_uuid", None)
                if parent_uuid:
                    parent = next((w for w in self.all_windows if getattr(w, "uuid", None) == parent_uuid), None)
                    if parent is not None:
                        # 正規APIがあれば優先
                        if hasattr(parent, "remove_child_window"):
                            try:
                                parent.remove_child_window(window)
                            except Exception as e:
                                logger.warning(f"Failed to remove child window via remove_child_window: {e}")
                        else:
                            # フォールバック（極力使わない）
                            try:
                                if hasattr(parent, "child_windows") and window in parent.child_windows:
                                    parent.child_windows.remove(window)
                            except Exception as e:
                                logger.warning(f"Failed to remove child window via list: {e}")
            except Exception:
                logger.warning("Failed to remove parent->child reference", exc_info=True)

            # --- 2) 親子関係（子→親）を解除 ---
            try:
                children = list(getattr(window, "child_windows", []))
            except Exception:
                children = []  # アクセス失敗時は空リストとみなす

            for child in children:
                try:
                    if child in self.all_windows:
                        try:
                            child.parent_window_uuid = None
                        except Exception as e:
                            logger.warning(f"Failed to clear parent ref from child: {e}")
                except Exception:
                    logger.warning("Failed to clear parent ref from child", exc_info=True)

            try:
                if hasattr(window, "child_windows"):
                    window.child_windows.clear()
            except Exception as e:
                logger.warning(f"Failed to clear child_windows list: {e}")

            # --- 3) 管理リストから除去 ---
            try:
                if window in self.text_windows:
                    self.text_windows.remove(window)
            except Exception as e:
                logger.warning(f"Failed to remove from text_windows list: {e}")

            try:
                if window in self.image_windows:
                    self.image_windows.remove(window)
            except Exception as e:
                logger.warning(f"Failed to remove from image_windows list: {e}")

            # --- 4) 選択解除 ---
            try:
                if self.last_selected_window == window:
                    self.set_selected_window(None)
            except Exception as e:
                logger.warning(f"Failed to clear selection: {e}")

            # --- 5) 関連コネクタ削除（delete_connector 経由に統一） ---
            try:
                to_remove = [
                    c
                    for c in self.connectors
                    if getattr(c, "start_window", None) == window or getattr(c, "end_window", None) == window
                ]
            except Exception:
                logger.warning("Failed to identify associated connectors", exc_info=True)
                to_remove = []

            for c in to_remove:
                try:
                    self.delete_connector(c)
                except Exception as e:
                    logger.warning(f"Failed to delete associated connector: {e}")

            logger.info(f"{w_type}Window removed: UUID={w_uuid}")

        except Exception as e:
            logger.error(f"Error removing window: {e}\n{traceback.format_exc()}")

    def remove_connector(self, connector: Optional[ConnectorLine]) -> None:
        """リストからコネクタを削除する（冪等・安全版）。

        Args:
            connector (Optional[ConnectorLine]): ConnectorLine想定。
        """
        if connector is None:
            return

        # connectors から除去（既に無ければ何もしない）
        try:
            if connector in self.connectors:
                self.connectors.remove(connector)
        except Exception:
            pass

        # start/end の connected_lines から除去
        try:
            sw = getattr(connector, "start_window", None)
            if sw is not None:
                try:
                    if hasattr(sw, "connected_lines") and connector in sw.connected_lines:
                        sw.connected_lines.remove(connector)
                except Exception as e:
                    logger.warning(f"Failed to remove connector from start window: {e}")
        except Exception as e:
            logger.warning(f"Error accessing start window for connector removal: {e}")

        try:
            ew = getattr(connector, "end_window", None)
            if ew is not None:
                try:
                    if hasattr(ew, "connected_lines") and connector in ew.connected_lines:
                        ew.connected_lines.remove(connector)
                except Exception as e:
                    logger.warning(f"Failed to remove connector from end window: {e}")
        except Exception as e:
            logger.warning(f"Error accessing end window for connector removal: {e}")

        # 選択解除
        try:
            if self.last_selected_window == connector:
                self.set_selected_window(None)
        except Exception:
            logger.debug("Failed to delete ConnectorLine object", exc_info=True)

    def delete_connector(self, connector: Optional[ConnectorLine]) -> None:
        """コネクタ（ConnectorLine）を安全に削除する正規ルート（遅延削除版・改良）。

        方針:
            - 見た目を先に消す（label/line を hide）
            - 参照（self.connectors / start/end.connected_lines）を先に外す（クリック経路遮断）
            - close はイベントループ末尾へ遅延（Qtの消去タイミング揺れ対策）
            - 何度呼ばれても落ちない（冪等）

        Args:
            connector (Optional[ConnectorLine]): 削除対象コネクタ
        """
        if connector is None:
            return

        # 1) 先に見た目を消す
        try:
            lw0 = getattr(connector, "label_window", None)
            if lw0 is not None:
                try:
                    lw0.hide()
                except Exception as e:
                    logger.warning(f"Failed to hide label window: {e}")
        except Exception as e:
            logger.warning(f"Error accessing label window script: {e}")

        try:
            connector.hide()
        except Exception:
            logger.warning("Failed to update connectors after removal", exc_info=True)

        # 2) 参照を先に外す（冪等）
        try:
            self.remove_connector(connector)
        except Exception as e:
            logger.warning(f"Failed to remove_connector refs: {e}")

        # 3) 実体closeは遅延（イベントループ末尾）
        def _deferred_close() -> None:
            try:
                lw = getattr(connector, "label_window", None)
                if lw is not None:
                    try:
                        lw.close()
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Deferred label close failed: {e}")

            try:
                connector.close()
            except Exception as e:
                logger.warning(f"Deferred connector close failed: {e}")

        try:
            from PySide6.QtCore import QTimer

            QTimer.singleShot(0, _deferred_close)
        except Exception:
            _deferred_close()

    def clear_all(self) -> None:
        self._prune_invalid_refs()
        """シーン内の全オブジェクト（コネクタ/テキスト/画像）を安全に削除する。

        方針:
            - コネクタは delete_connector() に統一して削除経路を一本化
            - 次に Text/Image を close（closeEvent -> remove_window を想定）
            - 最後に選択状態をクリア
        """
        # 1) コネクタを全削除（delete_connector に統一）
        try:
            for c in list(self.connectors):
                try:
                    self.delete_connector(c)
                except Exception:
                    pass
        except Exception:
            logger.error("Failed during connector bulk deletion", exc_info=True)

        # 念のため空にしておく（delete_connector が remove_connector まで行うが保険）
        try:
            self.connectors.clear()
        except Exception:
            logger.warning("Failed to clear connectors list", exc_info=True)

        # 2) ウィンドウを削除（close）
        try:
            self.close_all_text_windows()
        except Exception:
            logger.error("Failed to close all text windows", exc_info=True)

        try:
            self.close_all_image_windows()
        except Exception:
            logger.error("Failed to close all image windows", exc_info=True)

        # 3) 選択状態をクリア
        try:
            self.set_selected_window(None)
        except Exception:
            logger.warning("Failed to clear selection", exc_info=True)

    # ==========================================
    # Logic Actions (Connection & Grouping)
    # ==========================================

    def handle_connect_request(self, source_window: "TextWindow | ImageWindow"):
        if not self.last_selected_window or self.last_selected_window == source_window:
            QMessageBox.information(self.main_window, tr("menu_connect_group_ops"), tr("msg_conn_fail"))
            return
        self.add_connector(source_window, self.last_selected_window)

    def handle_disconnect_request(self, target_window: "TextWindow | ImageWindow"):
        to_remove = []
        for conn in self.connectors:
            if conn.start_window == target_window or conn.end_window == target_window:
                to_remove.append(conn)

        if not to_remove:
            return

        for conn in to_remove:
            self.delete_connector(conn)

        QMessageBox.information(self.main_window, tr("menu_connect_group_ops"), tr("msg_disconnect_success"))

    def handle_group_request(self, source_window: "TextWindow | ImageWindow"):
        if not self.last_selected_window or self.last_selected_window == source_window:
            QMessageBox.information(self.main_window, tr("menu_connect_group_ops"), tr("msg_conn_fail"))
            return
        if hasattr(self.last_selected_window, "add_child_window"):
            self.last_selected_window.add_child_window(source_window)
        self.sig_status_message.emit(tr("msg_group_success"))

    def handle_ungroup_request(self, source_window: "TextWindow | ImageWindow"):
        if source_window.parent_window_uuid:
            for parent in self.all_windows:
                if parent.uuid == source_window.parent_window_uuid:
                    if hasattr(parent, "remove_child_window"):
                        parent.remove_child_window(source_window)
                    break
        source_window.parent_window_uuid = None

    # ==========================================
    # Selection Logic
    # ==========================================

    def set_selected_window(self, window: Optional[QObject]):
        self._prune_invalid_refs()

        old_selected = self.last_selected_window

        if old_selected and old_selected != window:
            if hasattr(old_selected, "set_selected"):
                old_selected.set_selected(False)

        self.last_selected_window = window

        if self.last_selected_window:
            if hasattr(self.last_selected_window, "set_selected"):
                self.last_selected_window.set_selected(True)
                self.last_selected_window.raise_()

        self.sig_selection_changed.emit(window)

        # --- Auto-Follow: 編集ダイアログの所有権を移譲 ---
        self._try_transfer_edit_dialog(old_selected, window)

    def _try_transfer_edit_dialog(
        self,
        old_window: Optional[QObject],
        new_window: Optional[QObject],
    ) -> None:
        """Auto-Follow: TextWindow 間で編集ダイアログを移譲する。

        old_window がダイアログを持ち、new_window も TextWindow であれば、
        ダイアログの所有権を new_window に移す（auto-commit + switch_target）。
        """
        if old_window is None or new_window is None:
            return
        if old_window is new_window:
            return

        # Only transfer between TextWindows
        if not isinstance(old_window, TextWindow) or not isinstance(new_window, TextWindow):
            return

        dialog = getattr(old_window, "_edit_dialog", None)
        if dialog is None:
            return

        # Release from old (auto-commits current text)
        released = old_window._release_edit_dialog()
        if released is None:
            return

        # Take over by new window
        new_window._take_over_edit_dialog(released)
        logger.info(
            "Auto-Follow: dialog transferred %s -> %s",
            getattr(old_window, "uuid", "?"),
            getattr(new_window, "uuid", "?"),
        )

    # ==========================================
    # Node Logic (Clone & Create Related)
    # ==========================================

    def clone_text_window(self, source: TextWindow) -> None:
        """TextWindow を複製する。制限到達時は何もしない。

        Args:
            source (TextWindow): 複製元（TextWindow想定）。
        """
        try:
            # 生成（WindowManager 正規ルート）
            new_window = self.add_text_window(
                text=str(getattr(source, "text", tr("new_text_default"))),
                pos=source.pos() + QPoint(20, 20),
                suppress_limit_message=False,
            )
            if new_window is None:
                return

            # config をコピー（個体差のあるフィールドは除外）
            exclude: set[str] = {"uuid", "position", "parent_uuid", "connected_lines"}
            src_data: dict[str, Any] = source.config.model_dump(mode="json", exclude=exclude)

            for k, v in src_data.items():
                if hasattr(new_window.config, k):
                    try:
                        setattr(new_window.config, k, v)
                    except Exception as e:
                        logger.debug(f"Config copy failed for {k}: {e}")

            # easing を runtime に反映（あるなら）
            if hasattr(new_window, "_apply_easing_from_config"):
                try:
                    new_window._apply_easing_from_config()
                except Exception:
                    logger.warning("Failed to apply easing from config", exc_info=True)

            # 描画更新
            new_window.update_text()

            # アニメの再開（保存値がONなら）
            try:
                if getattr(new_window, "move_loop_enabled", False):
                    new_window.start_move_animation()
                elif getattr(new_window, "move_position_only_enabled", False):
                    new_window.start_move_position_only_animation()

                if getattr(new_window, "is_fading_enabled", False):
                    new_window.start_fade_in()
                elif getattr(new_window, "fade_in_only_loop_enabled", False):
                    new_window.start_fade_in_only()
                elif getattr(new_window, "fade_out_only_loop_enabled", False):
                    new_window.start_fade_out_only()
            except Exception:
                logger.warning("Failed to update connector label visibility", exc_info=True)

        except Exception as e:
            logger.error("Failed to clone TextWindow: %s\n%s", e, traceback.format_exc())

    def clone_image_window(self, source: ImageWindow) -> None:
        """ImageWindow を複製する。

        方針:
            - 生成は add_image_window（WindowManager正規ルート）
            - config をコピー（uuid/position/geometry/parent_uuid/image_path は除外）
            - frames を可能ならコピーして高速化
            - タイマーを更新し、見た目を更新

        Args:
            source (ImageWindow): 複製元（ImageWindow想定）。
        """
        try:
            # ImageWindow 判定（循環import耐性のため名前でも判定）
            is_img = False
            try:
                from windows.image_window import ImageWindow

                is_img = isinstance(source, ImageWindow)
            except Exception:
                is_img = type(source).__name__ == "ImageWindow"

            if not is_img:
                return

            src_path: str = str(getattr(source, "image_path", "") or "")
            new_pos: QPoint = source.pos() + QPoint(20, 20)

            new_window = self.add_image_window(
                image_path=src_path,
                pos=new_pos,
                suppress_limit_message=False,
            )
            if new_window is None:
                return

            # config をコピー（個体差/生成依存のものは除外）
            exclude: set[str] = {"uuid", "position", "geometry", "parent_uuid", "image_path"}
            try:
                src_data: dict[str, Any] = source.config.model_dump(mode="json", exclude=exclude)
            except Exception:
                src_data = {}

            for k, v in src_data.items():
                if hasattr(new_window.config, k):
                    try:
                        setattr(new_window.config, k, v)
                    except Exception as e:
                        logger.debug(f"Image config copy failed for {k}: {e}")

            # easing を runtime に反映（あるなら）
            if hasattr(new_window, "_apply_easing_from_config"):
                try:
                    new_window._apply_easing_from_config()
                except Exception:
                    logger.warning("Failed to apply easing from config", exc_info=True)

            # frames をコピーできるならコピー（ロード高速化）
            try:
                frames = getattr(source, "frames", None)
                if isinstance(frames, list) and frames:
                    new_window.frames = frames[:]
                    try:
                        new_window.current_frame = int(getattr(source, "current_frame", 0))
                    except Exception:
                        new_window.current_frame = 0

                    try:
                        new_window.original_speed = int(getattr(source, "original_speed", 100))
                    except Exception:
                        pass
            except Exception:
                logger.warning("Failed to copy image frames/speed", exc_info=True)

            # 位置の確定（念のため）
            try:
                new_window.move(new_pos)
                new_window.config.position = {"x": int(new_window.x()), "y": int(new_window.y())}
            except Exception:
                logger.warning("Failed to move new window", exc_info=True)

            # タイマー・描画
            try:
                if hasattr(new_window, "_update_animation_timer"):
                    new_window._update_animation_timer()
            except Exception:
                logger.warning("Failed to update animation timer", exc_info=True)

            try:
                if hasattr(new_window, "update_image"):
                    new_window.update_image()
            except Exception:
                logger.warning("Failed to update image content", exc_info=True)

            # 表示状態
            try:
                if getattr(new_window, "is_hidden", False):
                    if hasattr(new_window, "hide_action"):
                        new_window.hide_action()
                    else:
                        new_window.hide()
            except Exception:
                logger.warning("Failed to restore hidden state", exc_info=True)

            # アニメーション状態の復元
            try:
                if getattr(new_window, "move_loop_enabled", False):
                    new_window.start_move_animation()
                elif getattr(new_window, "move_position_only_enabled", False):
                    new_window.start_move_position_only_animation()

                if getattr(new_window, "is_fading_enabled", False):
                    new_window.start_fade_in()
                elif getattr(new_window, "fade_in_only_loop_enabled", False):
                    new_window.start_fade_in_only()
                elif getattr(new_window, "fade_out_only_loop_enabled", False):
                    new_window.start_fade_out_only()
            except Exception:
                logger.warning("Failed to restart animation loop", exc_info=True)

        except Exception as e:
            logger.error("Failed to clone ImageWindow: %s\n%s", e, traceback.format_exc())

    def create_related_node(self, source_window, relation_type):
        gap_x = 50
        gap_y = 60
        target_parent = None

        if relation_type == "child":
            target_parent = source_window
        elif relation_type == "sibling":
            parent_uuid = source_window.parent_window_uuid
            if parent_uuid:
                target_parent = next((w for w in self.all_windows if w.uuid == parent_uuid), None)

        new_x, new_y = 0, 0
        if relation_type == "child":
            # --- 修正箇所: start ---
            # 既に削除された(C++オブジェクトが存在しない)ウィンドウをリストから除外
            source_window.child_windows = [w for w in source_window.child_windows if w in self.all_windows]
            # --- 修正箇所: end ---

            base_x = source_window.x() + source_window.width() + gap_x
            base_y = source_window.y()
            if source_window.child_windows:
                last = source_window.child_windows[-1]
                base_y = last.y() + last.height() + gap_y
            new_x, new_y = base_x, base_y

        elif relation_type == "sibling":
            new_x = source_window.x()
            new_y = source_window.y() + source_window.height() + gap_y

        while self._is_position_occupied(new_x, new_y):
            new_y += 50

        new_window = self.add_text_window(tr("new_text_default"), QPoint(new_x, new_y))
        if new_window is None:
            return

        exclude = {"uuid", "position", "parent_uuid", "text"}
        src_data = source_window.config.model_dump(exclude=exclude)
        for k, v in src_data.items():
            if hasattr(new_window.config, k):
                setattr(new_window.config, k, v)
        new_window.update_text()

        if target_parent:
            self.add_connector(target_parent, new_window)
            target_parent.add_child_window(new_window)

    def _is_position_occupied(self, x, y, threshold=20):
        target = QPoint(x, y)
        for w in self.all_windows:
            if (w.pos() - target).manhattanLength() < threshold:
                return True
        return False

    def navigate_selection(self, current, key):
        candidates = [w for w in self.all_windows if w != current and w.isVisible()]
        if not candidates:
            return

        current_center = current.geometry().center()
        best = None
        min_dist = float("inf")

        direction = QPoint(0, 0)
        if key == Qt.Key_Up:
            direction = QPoint(0, -1)
        elif key == Qt.Key_Down:
            direction = QPoint(0, 1)
        elif key == Qt.Key_Left:
            direction = QPoint(-1, 0)
        elif key == Qt.Key_Right:
            direction = QPoint(1, 0)

        for cand in candidates:
            cand_center = cand.geometry().center()
            diff = cand_center - current_center
            dist = math.sqrt(diff.x() ** 2 + diff.y() ** 2)
            if dist == 0:
                continue

            dot = (diff.x() * direction.x() + diff.y() * direction.y()) / dist
            if dot > 0.5:
                if dist < min_dist:
                    min_dist = dist
                    best = cand

        if best:
            self.set_selected_window(best)

    # ==========================================
    # Batch Operation (一括操作)
    # ==========================================
    def close_all_other_images(self, selected: Any) -> None:
        """選択中以外の ImageWindow をすべて閉じる。

        Args:
            selected (Any): 基準となる ImageWindow。
        """
        try:
            # 生存している ImageWindow のみ
            wins: list[Any] = []
            try:
                import shiboken6

                for w in list(self.image_windows):
                    if w is None or not shiboken6.isValid(w):
                        continue
                    wins.append(w)
            except Exception:
                wins = [w for w in list(self.image_windows) if w is not None]

            for w in wins:
                if w is selected:
                    continue
                try:
                    w.close()
                except Exception:
                    logger.warning(f"Failed to close image window: {w}", exc_info=True)

        except Exception as e:
            logger.error("Failed to close all other images: %s\n%s", e, traceback.format_exc())

    def close_all_other_text_windows(self, selected: Any) -> None:
        """選択中以外の TextWindow をすべて閉じる。

        Args:
            selected (Any): 基準となる TextWindow。
        """
        try:
            wins: list[Any] = []
            try:
                import shiboken6

                for w in list(self.text_windows):
                    if w is None or not shiboken6.isValid(w):
                        continue
                    wins.append(w)
            except Exception:
                wins = [w for w in list(self.text_windows) if w is not None]

            for w in wins:
                if w is selected:
                    continue
                try:
                    w.close()
                except Exception:
                    logger.warning(f"Failed to close text window: {w}", exc_info=True)

        except Exception as e:
            logger.error("Failed to close all other text windows: %s\n%s", e, traceback.format_exc())

    def hide_all_other_text_windows(self, selected: Any) -> None:
        """選択中以外の TextWindow をすべて隠す。

        Args:
            selected (Any): 基準となる TextWindow。
        """
        try:
            wins: list[Any] = []
            try:
                import shiboken6

                for w in list(self.text_windows):
                    if w is None or not shiboken6.isValid(w):
                        continue
                    wins.append(w)
            except Exception:
                wins = [w for w in list(self.text_windows) if w is not None]

            for w in wins:
                if w is selected:
                    continue
                try:
                    if hasattr(w, "hide_action"):
                        w.hide_action()
                    else:
                        w.hide()
                except Exception:
                    logger.warning(f"Failed to hide text window: {w}", exc_info=True)

        except Exception as e:
            logger.error("Failed to hide all other text windows: %s\n%s", e, traceback.format_exc())

    def hide_all_other_image_windows(self, selected: Any) -> None:
        """選択中以外の ImageWindow をすべて隠す。

        Args:
            selected (Any): 基準となる ImageWindow。
        """
        try:
            wins: list[Any] = []
            try:
                import shiboken6

                for w in list(self.image_windows):
                    if w is None or not shiboken6.isValid(w):
                        continue
                    wins.append(w)
            except Exception:
                wins = [w for w in list(self.image_windows) if w is not None]

            for w in wins:
                if w is selected:
                    continue
                try:
                    if hasattr(w, "hide_action"):
                        w.hide_action()
                    else:
                        w.hide()
                except Exception:
                    logger.warning(f"Failed to hide image window: {w}", exc_info=True)

        except Exception as e:
            logger.error("Failed to hide all other image windows: %s\n%s", e, traceback.format_exc())

    def show_all_text_windows(self):
        for window in self.text_windows:
            window.show_action()

    def hide_all_text_windows(self):
        for window in self.text_windows:
            window.hide_action()

    def show_all_image_windows(self):
        for window in self.image_windows:
            window.show_action()

    def hide_all_image_windows(self):
        for window in self.image_windows:
            window.hide_action()

    def toggle_all_frontmost_text_windows(self):
        for window in self.text_windows:
            window.toggle_frontmost()

    def toggle_all_frontmost_image_windows(self):
        for window in self.image_windows:
            window.toggle_frontmost()

    def toggle_text_click_through(self):
        any_disabled = any(not w.is_click_through for w in self.text_windows)
        target_state = any_disabled
        for w in self.text_windows:
            w.set_click_through(target_state)

    def toggle_image_click_through(self):
        any_disabled = any(not w.is_click_through for w in self.image_windows)
        target_state = any_disabled
        for w in self.image_windows:
            w.set_click_through(target_state)

    def stop_all_text_animations(self):
        for window in self.text_windows:
            window.stop_all_animations()

    def stop_all_image_animations(self):
        for window in self.image_windows:
            window.stop_all_animations()

    # --- Delegate to other managers ---
    def _open_style_gallery(self, window):
        from ui.dialogs import StyleGalleryDialog

        if hasattr(self.main_window, "style_manager"):
            dialog = StyleGalleryDialog(self.main_window.style_manager, self.main_window)
            if dialog.exec() == 1:
                json_path = dialog.get_selected_style_path()
                if json_path:
                    self.main_window.style_manager.load_text_style(window, json_path)

    def _reselect_image(self, window):
        window.reselect_image()

    def close_all_windows(self) -> None:
        """アプリ終了時用：管理下の全ウィンドウを強制的に閉じる。

        Notes:
            MainWindowが閉じられるとき、親子関係がない（Orphan）ウィンドウは
            道連れにならないため、ここで明示的に close() を呼ぶ必要がある。
        """
        # 1. テキスト
        for w in list(self.text_windows):
            try:
                if w is not None:
                    w.close()
            except Exception:
                pass

        # 2. 画像
        for w in list(self.image_windows):
            try:
                if w is not None:
                    w.close()
            except Exception:
                pass

        # 3. コネクタ
        for c in list(self.connectors):
            try:
                if c is not None:
                    c.close()
            except Exception:
                pass

        # 4. ラベル（念のため）
        for c in list(self.connectors):
            try:
                if c and hasattr(c, "label_window") and c.label_window:
                    c.label_window.close()
            except Exception:
                pass

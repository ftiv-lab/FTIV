# managers/file_manager.py

import json
import logging
import os
import re
import traceback
from typing import Any, Dict, List, Optional, Union

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QFileDialog, QMessageBox

from utils.translator import tr
from windows.image_window import ImageWindow
from windows.text_window import TextWindow

logger = logging.getLogger(__name__)


class FileManager:
    """プロジェクト、シーン、およびウィンドウデータの保存と読み込みを管理するクラス。

    MainWindowから分離され、WindowManagerを介して実際のウィンドウオブジェクトを操作します。
    データのシリアライズ、ファイルI/O、およびシーンデータベースの同期を担当します。

    Attributes:
        main_window: アプリケーションのメインウィンドウインスタンス。
    """

    def __init__(self, main_window: Any) -> None:
        """FileManagerを初期化します。

        Args:
            main_window: MainWindowのインスタンス。
        """
        self.main_window = main_window

    @property
    def window_manager(self) -> Any:
        """MainWindowが保持するWindowManagerへのショートカット。"""
        return self.main_window.window_manager

    @property
    def json_directory(self) -> str:
        """JSONファイルのデフォルト保存ディレクトリ。"""
        return self.main_window.json_directory

    # ==========================================
    # Data Serialization (Save/Load Logic)
    # ==========================================

    def _clear_legacy_absolute_move_fields(self, config: Any) -> None:
        """
        保存前のデータクリーンアップ。
        相対移動モード(move_use_relative=True)の場合は、不要な絶対座標(start/end)を消去する。
        絶対移動モードの場合は保持する。
        """
        try:
            # 相対モードが明示的にONの場合のみ、絶対座標情報を消す
            if getattr(config, "move_use_relative", False):
                if hasattr(config, "start_position"):
                    config.start_position = None
                if hasattr(config, "end_position"):
                    config.end_position = None
        except Exception:
            pass

    def _dump_config_json(self, config: Any) -> Dict[str, Any]:
        """
        Pydantic config を JSON化する共通関数。
        - 旧 absolute move の残骸を消す
        - exclude_none=True で JSON をクリーンにする
        """
        self._clear_legacy_absolute_move_fields(config)
        return config.model_dump(mode="json", exclude_none=True)

    def _serialize_pen_style(self, pen_style: Any) -> int:
        """Qt.PenStyle 等を JSON 保存用の int に変換する。

        Args:
            pen_style (Any): Qt.PenStyle / int / enum 等

        Returns:
            int: ペンスタイルの整数値（変換できない場合は SolidLine）
        """
        try:
            # すでに int ならそのまま
            if isinstance(pen_style, int):
                return int(pen_style)

            # PySide6 の enum は .value を持つことがある
            v = getattr(pen_style, "value", None)
            if v is not None:
                return int(v)

            # それでもダメなら、Qt.PenStyle(...) 経由で値を取りにいく
            try:
                return int(Qt.PenStyle(pen_style))  # type: ignore[arg-type]
            except Exception:
                pass

        except Exception:
            pass

        # 最終フォールバック
        try:
            return int(Qt.SolidLine)
        except Exception:
            return 1

    def _serialize_arrow_style(self, arrow_style: Any) -> str:
        """ArrowStyle を JSON 保存用の文字列に変換する。

        Args:
            arrow_style (Any): ArrowStyle(Enum) / str / None

        Returns:
            str: "none" | "start" | "end" | "both"
        """
        try:
            if arrow_style is None:
                return "none"

            # Enum系は value を持つことが多い
            v = getattr(arrow_style, "value", None)
            if isinstance(v, str) and v:
                return v

            # 文字列なら正規化
            if isinstance(arrow_style, str):
                s = arrow_style.strip().lower()
                if s in ("none", "start", "end", "both"):
                    return s

                # "ArrowStyle.END" みたいな文字列にも対応
                if "none" in s:
                    return "none"
                if "start" in s:
                    return "start"
                if "end" in s:
                    return "end"
                if "both" in s:
                    return "both"

            # Enum名から推測
            name = getattr(arrow_style, "name", None)
            if isinstance(name, str) and name:
                s = name.strip().lower()
                if s in ("none", "start", "end", "both"):
                    return s

        except Exception:
            pass

        return "none"

    def _serialize_qcolor_hexargb(self, color: Any) -> str:
        """QColor/文字列を JSON 保存用の #AARRGGBB に変換する。

        Args:
            color (Any): QColor / "#RRGGBB" / "#AARRGGBB" 等

        Returns:
            str: "#AARRGGBB"（不正ならデフォルト色）
        """
        try:
            if isinstance(color, QColor):
                return color.name(QColor.HexArgb)

            if isinstance(color, str):
                c = QColor(color)
                if c.isValid():
                    return c.name(QColor.HexArgb)

        except Exception:
            pass

        # 最終フォールバック（薄いシアン）
        return QColor(100, 200, 255, 180).name(QColor.HexArgb)

    def get_scene_data(self) -> Dict[str, Any]:
        try:
            if hasattr(self.window_manager, "_prune_invalid_refs"):
                self.window_manager._prune_invalid_refs()
        except Exception:
            pass

        """現在のシーン情報（ウィンドウ、接続）を辞書データとして取得します。

        Returns:
            Dict[str, Any]: シリアライズされたシーンデータ（新形式）。
        """
        scene_data: Dict[str, Any] = {
            "format_version": 1,
            "windows": [],
            "connections": [],
        }

        # テキストウィンドウの処理
        for window in self.window_manager.text_windows:
            window.config.position = {"x": window.x(), "y": window.y()}
            text_data = self._dump_config_json(window.config)
            text_data["type"] = "text"
            scene_data["windows"].append(text_data)

        # 画像ウィンドウの処理
        for window in self.window_manager.image_windows:
            scene_data["windows"].append(window.to_dict())

        # コネクタ（接続）の処理
        for conn in self.window_manager.connectors:
            if not conn.start_window or not conn.end_window:
                continue
            try:
                conn_data: Dict[str, Any] = {
                    "from_uuid": conn.start_window.uuid,
                    "to_uuid": conn.end_window.uuid,
                    "color": self._serialize_qcolor_hexargb(getattr(conn, "line_color", None)),
                    "width": int(getattr(conn, "line_width", 4)),
                    "arrow_style": self._serialize_arrow_style(getattr(conn, "arrow_style", None)),
                    "pen_style": self._serialize_pen_style(getattr(conn, "pen_style", Qt.SolidLine)),
                }

                # コネクタラベルの保存
                if hasattr(conn, "label_window") and conn.label_window and conn.label_window.text:
                    conn_data["label_data"] = self._dump_config_json(conn.label_window.config)

                scene_data["connections"].append(conn_data)
            except RuntimeError:
                continue

        return scene_data

    def load_scene_from_data(self, data: Union[Dict[str, Any], List[Any]]) -> None:
        """辞書データからシーンを復元します。

        Args:
            data: 読み込むシーンデータ。辞書形式またはリスト形式（旧版）。
        """
        if hasattr(self.main_window, "undo_stack"):
            self.main_window.undo_stack.clear()

        # 入力を新形式へ正規化
        try:
            normalized: Dict[str, Any] = self._normalize_scene_data(data)
        except Exception as e:
            try:
                QMessageBox.critical(self.main_window, tr("msg_error"), f"Failed to normalize scene data: {e}")
            except Exception:
                pass
            return

        loaded_windows_map: Dict[str, Any] = {}
        skipped_text_windows: int = 0
        skipped_image_windows: int = 0

        windows_list = normalized.get("windows", [])
        if not isinstance(windows_list, list):
            windows_list = []

        # 1. ウィンドウ生成
        for w_data in windows_list:
            if not isinstance(w_data, dict):
                continue

            w_type = w_data.get("type")
            if not w_type:
                w_type = "image" if "image_path" in w_data else "text"

            window: Optional[Any] = None
            if w_type == "text":
                window = self.create_text_window_from_data(w_data)
                if window is None:
                    skipped_text_windows += 1
            elif w_type == "image":
                window = self.create_image_window_from_data(w_data)
                if window is None:
                    skipped_image_windows += 1

            if window and hasattr(window, "uuid"):
                loaded_windows_map[window.uuid] = window

        # 2. 親子関係の復元
        all_wins = self.window_manager.text_windows + self.window_manager.image_windows
        all_map = {w.uuid: w for w in all_wins}

        for w_data in windows_list:
            if not isinstance(w_data, dict):
                continue
            parent_uuid = w_data.get("parent_uuid")
            self_uuid = w_data.get("uuid")
            if parent_uuid and self_uuid in all_map:
                child = all_map[self_uuid]
                if parent_uuid in all_map:
                    all_map[parent_uuid].add_child_window(child)

        # 3. 接続の復元
        connections_list = normalized.get("connections", [])
        if isinstance(connections_list, list) and connections_list:
            self._restore_connections(connections_list)

        # --- 追加: 読み込み完了後に念のため全コネクタの位置を更新する（描画遅延対策） ---
        def _fix_connector_positions() -> None:
            try:
                for conn in self.window_manager.connectors:
                    if hasattr(conn, "update_position"):
                        conn.update_position()
            except Exception:
                pass

        try:
            from PySide6.QtCore import QTimer

            QTimer.singleShot(0, _fix_connector_positions)
        except Exception:
            _fix_connector_positions()

        # FREE版制限などで一部生成できなかった場合の通知
        try:
            if skipped_text_windows > 0 or skipped_image_windows > 0:
                QMessageBox.information(
                    self.main_window,
                    tr("msg_info"),
                    tr("msg_free_limit_load_partial").format(
                        text=skipped_text_windows,
                        image=skipped_image_windows,
                    ),
                )
        except Exception:
            pass

    def _normalize_scene_data(self, data: Any) -> Dict[str, Any]:
        """読み込んだデータを「新形式（format_version: 1）」のシーン辞書に正規化する。

        対応する入力:
            - dict（ftiv_project）: current_state を取り出して正規化
            - dict（scene形式）: windows/connections を持つ
            - dict（単一window旧形式）: 1つのwindowだけをwindowsに入れる
            - list（超旧形式）: TextWindow相当のリスト（既存 create_text_window_from_data 互換のため残す）

        方針:
            - 「読み込み互換」は残す
            - 「内部処理」は新形式 dict に統一する

        Args:
            data (Any): 読み込み元データ。

        Returns:
            Dict[str, Any]: 正規化されたシーンデータ（format_version: 1）。
        """
        # 1) ftiv_project
        if isinstance(data, dict) and data.get("type") == "ftiv_project":
            current = data.get("current_state")
            if current is None:
                return {"format_version": 1, "windows": [], "connections": []}
            return self._normalize_scene_data(current)

        # 2) list（超旧形式）→ scene形式へラップ
        if isinstance(data, list):
            # 旧listは「テキストwindowの配列」として扱ってきた経緯があるので、
            # ここでは「windows配列」に入れるだけに留める（生成は既存ロジックが対応）
            windows: list[Any] = []
            for item in data:
                if isinstance(item, dict):
                    # type無ければ text として扱う
                    if "type" not in item:
                        item = dict(item)
                        item["type"] = "text"
                    windows.append(item)
            return {"format_version": 1, "windows": windows, "connections": []}

        # 3) dict（scene形式っぽい）
        if isinstance(data, dict):
            # すでに新形式 or 旧形式scene
            if "windows" in data:
                windows = data.get("windows", [])
                connections = data.get("connections", [])
                if not isinstance(windows, list):
                    windows = []
                if not isinstance(connections, list):
                    connections = []

                # versionキーが来ても無視して format_version に寄せる
                return {
                    "format_version": 1,
                    "windows": windows,
                    "connections": connections,
                }

            # 4) dict（単一window旧形式）→ windows=[data]
            # image_path があれば image、なければ text 扱い
            obj = dict(data)
            if "type" not in obj:
                obj["type"] = "image" if "image_path" in obj else "text"
            return {"format_version": 1, "windows": [obj], "connections": []}

        # 5) 不明
        return {"format_version": 1, "windows": [], "connections": []}

    def _restore_connections(self, connections_data: List[Dict[str, Any]]) -> None:
        """ウィンドウ間の接続（コネクタ）を復元します。
        Args:
            connections_data: 接続情報のリスト。
        """
        all_windows = self.window_manager.text_windows + self.window_manager.image_windows
        all_map = {w.uuid: w for w in all_windows}

        for conn_data in connections_data:
            from_uuid = conn_data.get("from_uuid")
            to_uuid = conn_data.get("to_uuid")

            if from_uuid in all_map and to_uuid in all_map:
                start_win = all_map[from_uuid]
                end_win = all_map[to_uuid]

                # 重複チェック
                if any(
                    (c.start_window == start_win and c.end_window == end_win)
                    or (c.start_window == end_win and c.end_window == start_win)
                    for c in self.window_manager.connectors
                ):
                    continue

                self.window_manager.add_connector(start_win, end_win)
                if not self.window_manager.connectors:
                    continue

                new_conn = self.window_manager.connectors[-1]

                # プロパティ設定（復元は setter / 変換を通して堅牢化）
                if "color" in conn_data:
                    try:
                        c = QColor(str(conn_data["color"]))
                        if c.isValid():
                            if hasattr(new_conn, "set_line_color"):
                                new_conn.set_line_color(c)
                            else:
                                new_conn.line_color = c
                    except Exception:
                        pass

                if "width" in conn_data:
                    try:
                        new_conn.line_width = int(conn_data["width"])
                    except Exception:
                        pass

                if "pen_style" in conn_data:
                    try:
                        style_val = conn_data["pen_style"]
                        # まず int へ
                        try:
                            style_int = int(getattr(style_val, "value", style_val))
                        except Exception:
                            style_int = int(style_val)

                        pen_style = Qt.PenStyle(style_int)

                        # 可能なら set_line_style 経由（updateも含めて安定）
                        if hasattr(new_conn, "set_line_style"):
                            new_conn.set_line_style(pen_style)
                        else:
                            new_conn.pen_style = pen_style
                    except Exception:
                        pass

                if "arrow_style" in conn_data:
                    try:
                        from models.enums import ArrowStyle

                        arrow = ArrowStyle(str(conn_data["arrow_style"]))
                        if hasattr(new_conn, "set_arrow_style"):
                            new_conn.set_arrow_style(arrow)
                        else:
                            new_conn.arrow_style = arrow
                    except Exception:
                        # フォールバック（文字列でも落とさない）
                        try:
                            new_conn.arrow_style = conn_data["arrow_style"]
                        except Exception:
                            pass

                # ラベルデータの復元
                label_data = conn_data.get("label_data")
                if label_data and hasattr(new_conn, "label_window") and new_conn.label_window:
                    try:
                        config = new_conn.label_window.config
                        for key, value in label_data.items():
                            if hasattr(config, key):
                                if key == "font_size" and isinstance(value, float):
                                    value = int(value)
                                setattr(config, key, value)

                        if hasattr(new_conn.label_window, "auto_detect_offset_mode"):
                            font = QFont(new_conn.label_window.font_family, int(new_conn.label_window.font_size))
                            new_conn.label_window.auto_detect_offset_mode(font)

                        # 追加: easing を runtime へ反映
                        if hasattr(new_conn.label_window, "_apply_easing_from_config"):
                            try:
                                new_conn.label_window._apply_easing_from_config()
                            except Exception:
                                pass

                        new_conn.label_window.update_text()

                        # 追加: ラベルもアニメ状態を復元
                        self._resume_window_animations(new_conn.label_window)

                    except Exception:
                        pass  # Failed to restore label data

                new_conn.update()
                new_conn.update_position()

    def create_text_window_from_data(self, text_data: Dict[str, Any]) -> Optional[TextWindow]:
        """データからTextWindowを生成・構成します。

        Args:
            text_data (Dict[str, Any]): TextWindow の保存データ。

        Returns:
            Optional[TextWindow]: 生成されたTextWindow。制限/失敗時は None。
        """
        try:
            # 座標の解決
            pos = text_data.get("position", {})
            pos_x = pos.get("x") if isinstance(pos, dict) else text_data.get("x", 100)
            pos_y = pos.get("y") if isinstance(pos, dict) else text_data.get("y", 100)

            text_content = text_data.get("text", "Text")

            # --- 重要：生成は WindowManager 経由（FREE制限を確実に効かせる） ---
            window = self.window_manager.add_text_window(
                text=text_content,
                pos=QPoint(int(pos_x), int(pos_y)),
                suppress_limit_message=True,
            )
            if window is None:
                return None

            # Configの一括適用
            config_fields = window.config.model_dump().keys()
            for key, value in text_data.items():
                if key in config_fields:
                    if key == "font_size" and isinstance(value, float):
                        value = int(value)
                    try:
                        setattr(window.config, key, value)
                    except Exception:
                        pass
                elif key == "font_color" and isinstance(value, str):
                    window.config.font_color = value

            # 追加: configに保存された easing を runtime に反映
            if hasattr(window, "_apply_easing_from_config"):
                try:
                    window._apply_easing_from_config()
                except Exception:
                    pass

            # 描画とプロパティの適用
            # ★修正: 読み込み時はデバウンスせず、即時描画してサイズを確定させる（線のズレ防止）
            if hasattr(window, "_update_text_immediate"):
                window._update_text_immediate()
            else:
                window.update_text()

            window.is_frontmost = window.config.is_frontmost
            if window.config.is_click_through:
                window.set_click_through(True)

            # アニメーション状態の復元
            self._resume_window_animations(window)

            return window

        except Exception as e:
            QMessageBox.warning(self.main_window, tr("msg_error"), f"Failed to create text window: {e}")
            traceback.print_exc()
            return None

    def _resume_window_animations(self, window: TextWindow) -> None:
        """ウィンドウのアニメーション状態を再開します。"""
        # 追加: configに保存された easing を runtime に反映（安全に getattr で呼ぶ）
        if hasattr(window, "_apply_easing_from_config"):
            try:
                window._apply_easing_from_config()
            except Exception:
                pass

        if window.move_loop_enabled:
            window.start_move_animation()
        elif window.move_position_only_enabled:
            window.start_move_position_only_animation()

        if window.is_fading_enabled:
            window.start_fade_in()
        elif window.fade_in_only_loop_enabled:
            window.start_fade_in_only()
        elif window.fade_out_only_loop_enabled:
            window.start_fade_out_only()

    def create_image_window_from_data(self, data: Dict[str, Any]) -> Optional[ImageWindow]:
        """データからImageWindowを生成・構成します。

        Args:
            data (Dict[str, Any]): 画像ウィンドウの構成データ。

        Returns:
            Optional[ImageWindow]: 生成されたウィンドウ。制限/失敗時はNone。
        """
        try:
            image_path = data.get("image_path")

            # 位置の解決（position / geometry の順で優先）
            pos_x = 0
            pos_y = 0

            pos = data.get("position")
            if isinstance(pos, dict):
                pos_x = int(pos.get("x", 0))
                pos_y = int(pos.get("y", 0))

            geo = data.get("geometry")
            if isinstance(geo, dict):
                # geometry がある場合は、位置だけ geometry を優先しても良い
                pos_x = int(geo.get("x", pos_x))
                pos_y = int(geo.get("y", pos_y))

            # --- 重要：生成は WindowManager 経由（FREE制限を確実に効かせる） ---
            window = self.window_manager.add_image_window(
                image_path=image_path or "",
                pos=QPoint(pos_x, pos_y),
                suppress_limit_message=True,
            )
            if window is None:
                # WindowManager 側で制限メッセージは出る想定（show_limit_message）
                return None

            # apply_data で各種プロパティ適用（内部で load_image なども走る）
            if hasattr(window, "apply_data"):
                window.apply_data(data)

            # 念のため：apply_dataで開始された可能性があるため、一旦止めてから正しいeasingで再開
            if hasattr(window, "stop_all_animations"):
                window.stop_all_animations()

            if hasattr(window, "_apply_easing_from_config"):
                try:
                    window._apply_easing_from_config()
                except Exception:
                    pass

            # 停止した分をここで復元
            self._resume_window_animations(window)

            return window

        except Exception as e:
            QMessageBox.warning(self.main_window, tr("msg_error"), f"Failed to create image window: {e}")
            traceback.print_exc()
            return None

    # ==========================================
    # File I/O (Dialogs & Operations)
    # ==========================================

    def _save_json_atomic(self, path: str, data: Any) -> None:
        """JSONデータを一時ファイル経由で安全に保存する（Atomic Save）。

        保存中にクラッシュしても元ファイルが破損しないようにする対策。

        Args:
            path (str): 保存先パス。
            data (Any): JSONシリアライズ可能なデータ。
        """
        # 一時ファイル名を作成（同じフォルダに .tmp を付ける）
        temp_path = f"{path}.tmp"

        try:
            # 1. 一時ファイルへ書き込み
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # 2. 書き込み成功後にリネーム（アトミック操作）
            # Windows/Posix 共に os.replace はアトミックまたはそれに準ずる安全な置換
            os.replace(temp_path, path)

        except Exception as e:
            # 失敗時はゴミ（一時ファイル）を掃除してからエラーを再送出
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise e

    def save_window_to_json(self, window: Any) -> None:
        """指定されたウィンドウの設定をJSONに保存します（安全保存対応）。

        ウィンドウの種類（画像/テキスト）に応じて適切なファイル名を生成し、
        OSで使用不可能な文字を除去（サニタイズ）した上で保存ダイアログを表示します。

        Args:
            window (Any): 保存対象のウィンドウインスタンス。
        """
        try:
            is_image = hasattr(window, "image_path")
            w_type = "image" if is_image else "text"

            if is_image and window.image_path:
                raw_name = os.path.splitext(os.path.basename(window.image_path))[0]
            elif hasattr(window, "text") and window.text:
                # 改行を除いた先頭20文字を取得し、OSで使用禁止されている文字を除去
                first_line = window.text.split("\n")[0][:20]
                raw_name = re.sub(r'[\\/:*?"<>|]', "", first_line).strip() or "text_settings"
            else:
                raw_name = f"{w_type}_settings"

            path, _ = QFileDialog.getSaveFileName(
                self.main_window,
                tr("title_save_json"),
                os.path.join(self.json_directory, f"{raw_name}.json"),
                "JSON Files (*.json)",
            )
            if not path:
                return

            # 現在の座標を同期
            window.config.position = {"x": window.x(), "y": window.y()}
            data = self._dump_config_json(window.config)
            data["type"] = w_type

            # None を除去してクリーンなJSONにする
            data = self._prune_none(data)

            # ★Atomic Save
            self._save_json_atomic(path, data)

            if hasattr(self.main_window, "show_status_message"):
                self.main_window.show_status_message(f"Saved: {os.path.basename(path)}")

        except Exception as e:
            logger.error(f"Save Error: {e}")
            QMessageBox.critical(self.main_window, tr("msg_error"), f"Save failed: {e}\n{traceback.format_exc()}")

    def load_window_from_json(self, window: Any) -> None:
        """JSONから設定を読み込み、既存のウィンドウに適用します。

        画像が見つからない場合はユーザーに再選択を促し、適用後にUIを更新します。

        Args:
            window (Any): 適用先のウィンドウインスタンス。
        """
        try:
            path, _ = QFileDialog.getOpenFileName(
                self.main_window, tr("title_load_json"), self.json_directory, "JSON Files (*.json)"
            )
            if not path:
                return

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                QMessageBox.warning(self.main_window, tr("msg_warning"), "Invalid file format.")
                return

            # 画像パスの解決
            if hasattr(window, "image_path"):
                new_path = data.get("image_path")
                if new_path and not os.path.exists(new_path):
                    ret = QMessageBox.question(
                        self.main_window,
                        tr("msg_warning"),
                        f"Image not found at:\n{new_path}\n\nWould you like to re-select the image file?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if ret == QMessageBox.Yes:
                        new_path, _ = QFileDialog.getOpenFileName(
                            self.main_window, "Select Image", "", "Images (*.png *.jpg *.gif *.webp)"
                        )
                    else:
                        new_path = None

                if new_path and os.path.exists(new_path):
                    window.image_path = new_path
                    if hasattr(window, "load_image"):
                        window.load_image(new_path)

            # データの適用
            if hasattr(window, "apply_data"):
                window.apply_data(data)

            # UI更新の強制実行
            for update_method in ["update_text", "update_image", "refresh_style"]:
                if hasattr(window, update_method):
                    getattr(window, update_method)()

            if hasattr(self.main_window, "show_status_message"):
                self.main_window.show_status_message(f"Applied: {os.path.basename(path)}")

        except Exception as e:
            logger.error(f"Load Error: {e}")
            QMessageBox.critical(self.main_window, tr("msg_error"), f"Load failed: {e}\n{traceback.format_exc()}")

    def save_scene_to_json(self) -> None:
        """現在のシーンをJSONファイルとして保存します（安全保存対応）。"""
        try:
            path, _ = QFileDialog.getSaveFileName(
                self.main_window, tr("title_save_json"), self.json_directory, "JSON Files (*.json)"
            )
            if not path:
                return

            # ★Atomic Save
            self._save_json_atomic(path, self.get_scene_data())

            # 成功ログを追加
            logger.info(f"Scene saved successfully to: {path}")

        except Exception as e:
            # 詳細をログに記録し、ユーザーに通知
            logger.error(f"Failed to save scene: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self.main_window, tr("msg_error"), f"Error saving JSON: {e}")

    def load_scene_from_json(self) -> None:
        """JSONファイルを読み込んでシーンに展開します。"""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self.main_window, tr("menu_load_json"), self.json_directory, "JSON Files (*.json)"
            )
            if not path:
                return

            with open(path, "r", encoding="utf-8") as f:
                self.load_scene_from_data(json.load(f))
        except Exception as e:
            QMessageBox.critical(self.main_window, tr("msg_error"), f"Error loading JSON: {e}")
            traceback.print_exc()

    def save_project_as_json(self) -> None:
        """プロジェクト全体をJSONファイルとして保存します（安全保存対応）。"""
        try:
            path, _ = QFileDialog.getSaveFileName(
                self.main_window, tr("title_save_project"), self.json_directory, "Project Files (*.json)"
            )
            if not path:
                return

            project_data = {
                "type": "ftiv_project",
                "version": "1.0",
                # scenesも保存用にクリーンアップしたコピーを入れる
                "scenes": self._get_clean_scenes_for_export(),
                # current_state は get_scene_data() 側でクリーン寄り
                "current_state": self.get_scene_data(),
            }

            # 念のため project全体にも None 除去をかける
            project_data = self._prune_none(project_data)

            # ★Atomic Save
            self._save_json_atomic(path, project_data)

        except Exception as e:
            QMessageBox.critical(self.main_window, tr("msg_error"), f"Error saving project: {e}")
            traceback.print_exc()

    def load_project_from_json(self) -> None:
        """プロジェクトJSONファイルを読み込みます。"""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self.main_window, tr("title_load_project"), self.json_directory, "Project Files (*.json)"
            )
            if not path:
                return

            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.clear()

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                self.load_scene_from_data(data)
                return

            if isinstance(data, dict):
                if data.get("type") == "ftiv_project":
                    self.main_window.scenes = data.get("scenes", {})
                    self.save_scenes_db()
                    self.main_window.refresh_scene_tabs()

                    current = data.get("current_state")
                    if current:
                        self.window_manager.clear_all()
                        self.load_scene_from_data(current)
                    return
                elif any(k in data for k in ["windows", "image_path", "text"]):
                    self.load_scene_from_data(data)
                    return

            QMessageBox.warning(self.main_window, tr("msg_warning"), "Invalid file format.")
        except Exception as e:
            QMessageBox.critical(self.main_window, tr("msg_error"), f"Error loading project: {e}")
            traceback.print_exc()

    # ==========================================
    # Scene Database Logic
    # ==========================================

    def save_scenes_db(self) -> None:
        """シーンデータベースを永続化保存します（安全保存対応）。"""
        try:
            scenes_data = self._get_clean_scenes_for_export()
            # ★Atomic Save
            self._save_json_atomic(self.main_window.scene_db_path, scenes_data)
        except Exception:
            pass  # Error saving scenes db

    def load_scenes_db(self) -> None:
        """シーンデータベースを読み込みます。ファイルがない場合は初期値を設定します。"""
        if not os.path.exists(self.main_window.scene_db_path):
            self.main_window.scenes = {tr("default_category"): {}}
            self.main_window.refresh_scene_tabs()
            return

        try:
            with open(self.main_window.scene_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 旧形式の判別と自動変換
            is_old = any(isinstance(v, dict) and ("windows" in v or "version" in v) for v in data.values())

            if is_old:
                self.main_window.scenes = {tr("default_category"): data}
                self.save_scenes_db()
            else:
                self.main_window.scenes = data

            if not self.main_window.scenes:
                self.main_window.scenes[tr("default_category")] = {}
        except Exception:
            pass  # Error loading scenes db
            self.main_window.scenes = {tr("default_category"): {}}

        self.main_window.refresh_scene_tabs()

    def _prune_none(self, obj: Any) -> Any:
        """
        JSONに書き出す直前に、dict/list から None を再帰的に除去する。
        """
        if isinstance(obj, dict):
            new_d = {}
            for k, v in obj.items():
                if v is None:
                    continue
                cleaned = self._prune_none(v)
                if cleaned is None:
                    continue
                new_d[k] = cleaned
            return new_d

        if isinstance(obj, list):
            new_l = []
            for v in obj:
                if v is None:
                    continue
                cleaned = self._prune_none(v)
                if cleaned is None:
                    continue
                new_l.append(cleaned)
            return new_l

        return obj

    def _remove_legacy_absolute_move_keys_in_scene_dict(self, scene_data: Any) -> Any:
        """
        scene_data（dict/list）内の start_position/end_position を再帰的に削除する。
        ※ 既存の scenes DB は「dict化済み」なのでこちらを使う。
        """
        if isinstance(scene_data, dict):
            # window configに居ることが多い
            scene_data.pop("start_position", None)
            scene_data.pop("end_position", None)

            # ネストも再帰的に処理
            for k, v in list(scene_data.items()):
                scene_data[k] = self._remove_legacy_absolute_move_keys_in_scene_dict(v)
            return scene_data

        if isinstance(scene_data, list):
            return [self._remove_legacy_absolute_move_keys_in_scene_dict(v) for v in scene_data]

        return scene_data

    def _get_clean_scenes_for_export(self) -> Dict[str, Any]:
        """
        self.main_window.scenes を「保存用」にクリーンアップしたコピーを返す。
        - start_position/end_position を除去
        - None を除去
        """
        try:
            # まず深いコピー（json経由が簡単で安全）
            scenes_copy = json.loads(json.dumps(self.main_window.scenes, ensure_ascii=False))

            scenes_copy = self._remove_legacy_absolute_move_keys_in_scene_dict(scenes_copy)
            scenes_copy = self._prune_none(scenes_copy)

            return scenes_copy
        except Exception:
            # 失敗したら元をそのまま（最悪保存はできる）
            return self.main_window.scenes

    # ==========================================
    # Mind Map Operations
    # ==========================================

    @property
    def mindmap_db_path(self) -> str:
        """マインドマップデータの保存パス。"""
        return os.path.join(self.json_directory, "mindmaps.json")

    def load_mindmaps_db(self) -> Dict[str, Any]:
        """マインドマップDBを読み込む。"""
        if not os.path.exists(self.mindmap_db_path):
            return {}

        try:
            with open(self.mindmap_db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load mindmaps DB: {e}", exc_info=True)
            return {}

    def save_mindmaps_db(self, data: Dict[str, Any]) -> None:
        """マインドマップDBを保存する。"""
        try:
            self._save_json_atomic(self.mindmap_db_path, data)
        except Exception as e:
            logger.error(f"Failed to save mindmaps DB: {e}", exc_info=True)

    def import_mindmap_json(self, path: str) -> Optional[Dict[str, Any]]:
        """外部JSONファイルからマインドマップをインポートする。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to import mindmap: {e}", exc_info=True)
            return None

    def export_mindmap_json(self, path: str, data: Dict[str, Any]) -> None:
        """マインドマップを外部JSONファイルにエクスポートする。"""
        try:
            self._save_json_atomic(path, data)
        except Exception as e:
            logger.error(f"Failed to export mindmap: {e}", exc_info=True)

    def serialize_mindmap(self) -> Dict[str, Any]:
        """現在のマインドマップ（MindMapWidget）の状態をシリアライズする。"""
        mw = self.main_window
        if not hasattr(mw, "mindmap_widget"):
            return {}

        widget = mw.mindmap_widget
        scene = widget.canvas.scene()
        if not scene:
            return {}

        nodes_data = []
        edges_data = []

        # アイテム収集
        from ui.mindmap.mindmap_edge import MindMapEdge
        from ui.mindmap.mindmap_node import MindMapNode

        for item in scene.items():
            if isinstance(item, MindMapNode):
                nodes_data.append(item.to_dict())
            elif isinstance(item, MindMapEdge):
                edges_data.append(item.to_dict())

        # キャンバス設定
        canvas_settings = {
            "bg_color": widget.canvas._bg_color.name(),
            "grid_enabled": widget.canvas._grid_enabled,
            "grid_size": widget.canvas.GRID_SIZE,
            "zoom": widget.canvas._zoom_factor,
        }

        # ビュー中心座標
        center = widget.canvas.get_scene_pos_at_center()
        canvas_settings["center"] = {"x": center.x(), "y": center.y()}

        return {
            "format_version": 1,
            "nodes": nodes_data,
            "edges": edges_data,
            "canvas_settings": canvas_settings,
        }

    def deserialize_mindmap(self, data: Dict[str, Any]) -> None:
        """データをマインドマップ（MindMapWidget）に復元する。"""
        mw = self.main_window
        if not hasattr(mw, "mindmap_widget"):
            return

        widget = mw.mindmap_widget

        # キャンバスのクリア
        widget.clear_all()

        # キャンバス設定の適用
        settings = data.get("canvas_settings", {})
        if "bg_color" in settings:
            widget.canvas.set_background_color(QColor(settings["bg_color"]))
        if "grid_enabled" in settings:
            widget.canvas.set_grid_enabled(settings["grid_enabled"])
        if "grid_size" in settings:
            widget.canvas.GRID_SIZE = settings["grid_size"]

        # ノードの復元
        from ui.mindmap.mindmap_node import MindMapNode

        node_map = {}
        for node_data in data.get("nodes", []):
            node = MindMapNode.from_dict(node_data)
            widget.canvas.scene().addItem(node)
            node_map[node.uuid] = node

        # エッジの復元
        from ui.mindmap.mindmap_edge import MindMapEdge

        for edge_data in data.get("edges", []):
            source_uuid = edge_data.get("source_uuid")
            target_uuid = edge_data.get("target_uuid")

            if source_uuid in node_map and target_uuid in node_map:
                source = node_map[source_uuid]
                target = node_map[target_uuid]

                edge = MindMapEdge(source, target)

                # スタイル適用
                style = edge_data.get("style", {})
                if "color" in style:
                    edge.set_color(QColor(style["color"]))
                if "show_arrow" in style:
                    edge.set_show_arrow(style["show_arrow"])

                widget.canvas.scene().addItem(edge)

        # ビュー位置の復元
        center = settings.get("center")
        if center:
            widget.canvas.centerOn(center.get("x", 0), center.get("y", 0))

        # ズーム復元
        zoom = settings.get("zoom", 1.0)
        if zoom != 1.0:
            widget.canvas.resetTransform()
            widget.canvas.scale(zoom, zoom)
            widget.canvas._zoom_factor = zoom

    # ==========================================
    # Default Node Style
    # ==========================================

    def save_default_node_style(self) -> bool:
        """デフォルトノードスタイルを保存する。

        Returns:
            保存に成功した場合は True、失敗した場合は False。
        """
        if not hasattr(self.main_window, "default_node_style"):
            return False

        try:
            path = os.path.join(self.json_directory, "default_node_style.json")
            data = self.main_window.default_node_style.to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Default node style saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save default node style: {e}")
            logger.error(traceback.format_exc())
            return False

    def load_default_node_style(self) -> None:
        """デフォルトノードスタイルを読み込む。"""
        if not hasattr(self.main_window, "default_node_style"):
            return

        try:
            path = os.path.join(self.json_directory, "default_node_style.json")
            if not os.path.exists(path):
                return

            from models.default_node_style import DefaultNodeStyle

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.main_window.default_node_style = DefaultNodeStyle.from_dict(data)
            logger.info(f"Default node style loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load default node style: {e}")
            logger.error(traceback.format_exc())

# managers/style_manager.py

import json
import os
import traceback  # エラーハンドリング用に追加
from datetime import date
from typing import Any

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QFileDialog, QMessageBox

from models.window_config import TextWindowConfig
from windows.text_renderer import TextRenderer

# 循環参照を避けるため、TextWindowはメソッド内でインポートするか、必要な時だけ呼び出す形にします


class _TextRenderDummy:
    """TextRenderer に渡すための軽量ダミー。

    TextWindow を生成せずに、TextWindowConfig を保持して
    TextRenderer が参照する属性を提供する。
    """

    def __init__(self, config: TextWindowConfig) -> None:
        self.config: TextWindowConfig = config
        self.canvas_size: Any = None  # TextRenderer が代入する

        # TextRenderer が内部で setGeometry(QRect(...)) を呼ぶのでダミー実装を持つ
        self._geometry = None

    # --- TextRenderer が呼ぶ API（ダミー実装）---

    def pos(self) -> QPoint:
        """TextRenderer 互換：描画用ダミーなので常に (0,0) を返す。"""
        return QPoint(0, 0)

    def setGeometry(self, rect: Any) -> None:
        """TextRenderer 互換：ジオメトリを保持するだけ。"""
        self._geometry = rect

    # --- TextWindow 互換プロパティ（configへ委譲）---

    @property
    def text(self) -> str:
        return str(self.config.text or "")

    @property
    def font_family(self) -> str:
        return str(self.config.font or "Arial")

    @property
    def font_size(self) -> int:
        try:
            return int(self.config.font_size)
        except Exception:
            return 20

    # 色は TextRenderer 内で QColor(window.xxx) されるので str を返す
    @property
    def font_color(self) -> str:
        return str(self.config.font_color)

    @property
    def background_color(self) -> str:
        return str(self.config.background_color)

    # 可視/透明度
    @property
    def text_visible(self) -> bool:
        return bool(self.config.text_visible)

    @property
    def background_visible(self) -> bool:
        return bool(self.config.background_visible)

    @property
    def text_opacity(self) -> int:
        return int(self.config.text_opacity)

    @property
    def background_opacity(self) -> int:
        return int(self.config.background_opacity)

    # 影
    @property
    def shadow_enabled(self) -> bool:
        return bool(self.config.shadow_enabled)

    @property
    def shadow_color(self) -> str:
        return str(self.config.shadow_color)

    @property
    def shadow_opacity(self) -> int:
        return int(self.config.shadow_opacity)

    @property
    def shadow_blur(self) -> int:
        return int(self.config.shadow_blur)

    @property
    def shadow_scale(self) -> float:
        return float(self.config.shadow_scale)

    @property
    def shadow_offset_x(self) -> float:
        return float(self.config.shadow_offset_x)

    @property
    def shadow_offset_y(self) -> float:
        return float(self.config.shadow_offset_y)

    # 縦書き/余白
    @property
    def is_vertical(self) -> bool:
        return bool(self.config.is_vertical)

    @property
    def horizontal_margin_ratio(self) -> float:
        return float(self.config.horizontal_margin_ratio)

    @property
    def vertical_margin_ratio(self) -> float:
        return float(self.config.vertical_margin_ratio)

    @property
    def margin_top_ratio(self) -> float:
        return float(self.config.margin_top)

    @property
    def margin_bottom_ratio(self) -> float:
        return float(self.config.margin_bottom)

    @property
    def margin_left_ratio(self) -> float:
        return float(self.config.margin_left)

    @property
    def margin_right_ratio(self) -> float:
        return float(self.config.margin_right)

    @property
    def background_corner_ratio(self) -> float:
        return float(self.config.background_corner_ratio)

    # 縁取り1
    @property
    def outline_enabled(self) -> bool:
        return bool(self.config.outline_enabled)

    @property
    def outline_color(self) -> str:
        return str(self.config.outline_color)

    @property
    def outline_opacity(self) -> int:
        return int(self.config.outline_opacity)

    @property
    def outline_width(self) -> float:
        return float(self.config.outline_width)

    @property
    def outline_blur(self) -> int:
        return int(self.config.outline_blur)

    # 縁取り2
    @property
    def second_outline_enabled(self) -> bool:
        return bool(self.config.second_outline_enabled)

    @property
    def second_outline_color(self) -> str:
        return str(self.config.second_outline_color)

    @property
    def second_outline_opacity(self) -> int:
        return int(self.config.second_outline_opacity)

    @property
    def second_outline_width(self) -> float:
        return float(self.config.second_outline_width)

    @property
    def second_outline_blur(self) -> int:
        return int(self.config.second_outline_blur)

    # 縁取り3
    @property
    def third_outline_enabled(self) -> bool:
        return bool(self.config.third_outline_enabled)

    @property
    def third_outline_color(self) -> str:
        return str(self.config.third_outline_color)

    @property
    def third_outline_opacity(self) -> int:
        return int(self.config.third_outline_opacity)

    @property
    def third_outline_width(self) -> float:
        return float(self.config.third_outline_width)

    @property
    def third_outline_blur(self) -> int:
        return int(self.config.third_outline_blur)

    # 背景枠線
    @property
    def background_outline_enabled(self) -> bool:
        return bool(self.config.background_outline_enabled)

    @property
    def background_outline_color(self) -> str:
        return str(self.config.background_outline_color)

    @property
    def background_outline_opacity(self) -> int:
        return int(self.config.background_outline_opacity)

    @property
    def background_outline_width_ratio(self) -> float:
        return float(self.config.background_outline_width_ratio)

    # グラデ
    @property
    def text_gradient_enabled(self) -> bool:
        return bool(self.config.text_gradient_enabled)

    @property
    def text_gradient(self) -> Any:
        return self.config.text_gradient

    @property
    def text_gradient_angle(self) -> int:
        return int(self.config.text_gradient_angle)

    @property
    def text_gradient_opacity(self) -> int:
        return int(self.config.text_gradient_opacity)

    @property
    def background_gradient_enabled(self) -> bool:
        return bool(self.config.background_gradient_enabled)

    @property
    def background_gradient(self) -> Any:
        return self.config.background_gradient

    @property
    def background_gradient_angle(self) -> int:
        return int(self.config.background_gradient_angle)

    @property
    def background_gradient_opacity(self) -> int:
        return int(self.config.background_gradient_opacity)


class StyleManager:
    """
    ウィンドウスタイル（プリセット）の保存と読み込みを管理するクラス
    """

    @staticmethod
    def apply_theme_to_dialog(dialog: Any) -> None:
        """ダイアログにテーマを適用する（現在の実装では何もしないが、将来的に拡張可能）。

        Args:
            dialog: テーマを適用するダイアログインスタンス
        """
        # 現在はQSSでグローバルに適用されているため、個別の適用は不要かもしれないが
        # メソッド自体は存在させておく
        pass

    def __init__(self, main_window):
        self.main_window = main_window
        # スタイルとして保存するプロパティ名のリスト
        self.text_style_fields = [
            "font",
            "font_size",
            "font_color",
            "text_opacity",
            "background_visible",
            "background_opacity",
            "background_color",
            "background_corner_ratio",
            # 影
            "shadow_enabled",
            "shadow_color",
            "shadow_opacity",
            "shadow_blur",
            "shadow_scale",
            "shadow_offset_x",
            "shadow_offset_y",
            # 縁取り 1-3
            "outline_enabled",
            "outline_color",
            "outline_opacity",
            "outline_width",
            "outline_blur",
            "second_outline_enabled",
            "second_outline_color",
            "second_outline_opacity",
            "second_outline_width",
            "second_outline_blur",
            "third_outline_enabled",
            "third_outline_color",
            "third_outline_opacity",
            "third_outline_width",
            "third_outline_blur",
            # 背景枠線
            "background_outline_enabled",
            "background_outline_color",
            "background_outline_opacity",
            "background_outline_width_ratio",
            # グラデーション
            "text_gradient_enabled",
            "text_gradient",
            "text_gradient_angle",
            "text_gradient_opacity",
            "background_gradient_enabled",
            "background_gradient",
            "background_gradient_angle",
            "background_gradient_opacity",
            # 縦書き・配置モード
            "is_vertical",
        ]
        self._preset_meta_defaults: dict[str, Any] = {
            "_display_name": "",
            "_description": "",
            "_category": "other",
            "_tags": [],
            "_favorite": False,
            "_builtin": False,
            "_created": "",
            "_author": "user",
        }

    def _normalize_preset_tags(self, raw_tags: Any) -> list[str]:
        """Normalize preset tags into a de-duplicated lowercase list."""
        if raw_tags is None:
            return []
        if isinstance(raw_tags, str):
            candidates = [raw_tags]
        elif isinstance(raw_tags, (list, tuple, set)):
            candidates = list(raw_tags)
        else:
            return []

        out: list[str] = []
        seen: set[str] = set()
        for tag in candidates:
            val = str(tag or "").strip().lower()
            if not val or val in seen:
                continue
            seen.add(val)
            out.append(val)
        return out

    def _build_preset_meta(self, style_data: dict[str, Any], base_name: str) -> dict[str, Any]:
        """Return normalized preset metadata for legacy and new preset JSONs."""
        meta: dict[str, Any] = dict(self._preset_meta_defaults)
        for key in self._preset_meta_defaults.keys():
            if key in style_data:
                meta[key] = style_data[key]

        # Normalize types / fallbacks.
        meta["_display_name"] = str(meta.get("_display_name", "") or "")
        meta["_description"] = str(meta.get("_description", "") or "")
        meta["_category"] = str(meta.get("_category", "other") or "other")
        meta["_tags"] = self._normalize_preset_tags(meta.get("_tags"))
        meta["_favorite"] = bool(meta.get("_favorite", False))
        meta["_builtin"] = bool(meta.get("_builtin", False))
        meta["_created"] = str(meta.get("_created", "") or "")
        meta["_author"] = str(meta.get("_author", "user") or "user")
        if not meta["_display_name"]:
            meta["_display_name"] = str(base_name or "")
        return meta

    def _ensure_preset_schema_version(self, style_data: dict[str, Any]) -> None:
        """Upgrade preset schema version marker in-memory (non-destructive until save)."""
        # SP1 decision: keep a single _version for the whole preset JSON schema.
        style_data["_version"] = "1.1"

    def get_presets_directory(self):
        """プリセット保存用ディレクトリのパスを取得（なければ作成）"""
        base_dir = self.main_window.json_directory
        presets_dir = os.path.join(base_dir, "presets")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
        return presets_dir

    def save_text_style(self, window: Any) -> None:
        """現在のTextWindowのスタイルをJSONとサムネイル画像（サンプル文字）として保存します。

        TextWindow を生成してサムネイルを作る方式は、副作用（管理外ウィンドウ生成）や
        ライフサイクル不整合の原因になりやすいため、
        TextRenderer + TextWindowConfig + ダミーで直接レンダリングします。

        Args:
            window (Any): 保存元の TextWindow / TextWindow互換オブジェクト。
        """
        try:
            presets_dir: str = self.get_presets_directory()
            default_name: str = "new_style.json"

            file_path, _ = QFileDialog.getSaveFileName(
                window,
                "Save Style Preset",
                os.path.join(presets_dir, default_name),
                "Style JSON (*.json)",
            )
            if not file_path:
                return

            # --- 1. JSONデータの作成 ---
            style_data: dict[str, Any] = {}
            config_dump: dict[str, Any] = window.config.model_dump(mode="json")

            for field in self.text_style_fields:
                if field in config_dump:
                    style_data[field] = config_dump[field]

            # メタデータ（SP1: preset schema v1.1 + default meta fields）
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            style_data["_type"] = "ftiv_text_style"
            style_data["_version"] = "1.1"
            style_data["_display_name"] = base_name
            style_data["_description"] = ""
            style_data["_category"] = "other"
            style_data["_tags"] = []
            style_data["_favorite"] = False
            style_data["_builtin"] = False
            style_data["_created"] = date.today().isoformat()
            style_data["_author"] = "user"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(style_data, f, indent=4, ensure_ascii=False)

            # --- 2. サムネイル画像の保存（TextWindowを生成せずにレンダリング） ---
            base_path, _ = os.path.splitext(file_path)
            thumb_path: str = base_path + ".png"

            renderer: TextRenderer = TextRenderer()

            tmp_cfg: TextWindowConfig = TextWindowConfig()
            try:
                src_dump: dict[str, Any] = window.config.model_dump(mode="json")
                for k, v in src_dump.items():
                    if hasattr(tmp_cfg, k):
                        try:
                            setattr(tmp_cfg, k, v)
                        except Exception:
                            pass

                # サンプル文字は固定
                tmp_cfg.text = "Aa あ"

                # 念のため（不要情報を落とす）
                tmp_cfg.uuid = ""
                tmp_cfg.parent_uuid = None

            except Exception:
                tmp_cfg.text = "Aa あ"

            dummy = _TextRenderDummy(tmp_cfg)
            original_pixmap: QPixmap = renderer.render(dummy)

            thumb_size: int = 200

            scaled_pixmap: QPixmap = original_pixmap.scaled(
                thumb_size,
                thumb_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            final_thumb: QPixmap = QPixmap(thumb_size, thumb_size)
            final_thumb.fill(QColor(50, 50, 50))

            painter: QPainter = QPainter(final_thumb)
            try:
                x: int = (thumb_size - scaled_pixmap.width()) // 2
                y: int = (thumb_size - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
            finally:
                painter.end()

            final_thumb.save(thumb_path, "PNG")

            QMessageBox.information(window, "Success", "Style preset and thumbnail saved!")

        except Exception as e:
            QMessageBox.critical(window, "Error", f"Failed to save style: {e}")
            traceback.print_exc()

    def load_text_style(self, window, file_path=None):
        """JSONからスタイルを読み込んで適用 (単一ウィンドウ用)"""
        try:
            if not file_path:
                presets_dir = self.get_presets_directory()
                file_path, _ = QFileDialog.getOpenFileName(
                    window, "Load Style Preset", presets_dir, "Style JSON (*.json)"
                )

            if not file_path:
                return

            with open(file_path, "r", encoding="utf-8") as f:
                style_data = json.load(f)

            # Undoマクロ開始
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Apply Style Preset")

            # 共通ロジックで適用
            self._apply_data_to_window(window, style_data)

            # Undoマクロ終了
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

        except Exception as e:
            QMessageBox.critical(window, "Error", f"Failed to load style: {e}")
            import traceback

            traceback.print_exc()

    def get_available_presets(self):
        """
        プリセットフォルダ内の情報を取得
        戻り値: [{'name': 'Style1', 'json_path': '...', 'thumb_path': '...'}, ...]
        既存キーは維持しつつ、SP1以降はメタデータ関連キーも追加する。
        """
        presets_dir = self.get_presets_directory()
        presets = []
        if os.path.exists(presets_dir):
            # JSONファイルを探す
            for f in os.listdir(presets_dir):
                if f.endswith(".json"):
                    json_path = os.path.join(presets_dir, f)
                    base_name = os.path.splitext(f)[0]
                    thumb_name = base_name + ".png"
                    thumb_path = os.path.join(presets_dir, thumb_name)
                    style_data: dict[str, Any] = {}
                    try:
                        with open(json_path, "r", encoding="utf-8") as fp:
                            loaded = json.load(fp)
                        if isinstance(loaded, dict):
                            style_data = loaded
                    except Exception:
                        # Keep listing the preset file even if metadata parsing fails.
                        style_data = {}
                    meta = self._build_preset_meta(style_data, base_name)

                    # サムネイルがない場合はNone
                    if not os.path.exists(thumb_path):
                        thumb_path = None

                    presets.append(
                        {
                            # Backward-compatible keys (legacy UI currently uses these).
                            "name": base_name,
                            "json_path": json_path,
                            "thumb_path": thumb_path,
                            # SP1 metadata keys
                            "display_name": meta["_display_name"],
                            "description": meta["_description"],
                            "category": meta["_category"],
                            "tags": list(meta["_tags"]),
                            "favorite": meta["_favorite"],
                            "builtin": meta["_builtin"],
                            "created": meta["_created"],
                            "author": meta["_author"],
                            "version": str(style_data.get("_version", "") or "1.0"),
                            "type": str(style_data.get("_type", "") or ""),
                        }
                    )
        return presets

    def update_preset_meta(self, json_path: str, **kwargs: Any) -> bool:
        """Update metadata fields only, preserving style fields."""
        try:
            if not json_path or not os.path.exists(json_path):
                return False
            with open(json_path, "r", encoding="utf-8") as fp:
                loaded = json.load(fp)
            if not isinstance(loaded, dict):
                return False

            data: dict[str, Any] = dict(loaded)
            base_name = os.path.splitext(os.path.basename(json_path))[0]
            meta = self._build_preset_meta(data, base_name)

            alias_map = {
                "display_name": "_display_name",
                "description": "_description",
                "category": "_category",
                "tags": "_tags",
                "favorite": "_favorite",
                "builtin": "_builtin",
                "created": "_created",
                "author": "_author",
            }
            for key, value in kwargs.items():
                target_key = alias_map.get(key, key if str(key).startswith("_") else None)
                if target_key not in self._preset_meta_defaults:
                    continue
                if target_key == "_tags":
                    meta[target_key] = self._normalize_preset_tags(value)
                elif target_key in ("_favorite", "_builtin"):
                    meta[target_key] = bool(value)
                elif target_key == "_category":
                    meta[target_key] = str(value or "other")
                elif target_key == "_author":
                    meta[target_key] = str(value or "user")
                else:
                    meta[target_key] = str(value or "")

            # Preserve fallback behavior: display name can be empty in file, but we store
            # explicit values if provided. If someone clears it, keep empty string.
            for meta_key in self._preset_meta_defaults.keys():
                data[meta_key] = meta[meta_key]

            # Keep schema marker consistent after metadata update.
            self._ensure_preset_schema_version(data)
            if "_type" not in data:
                data["_type"] = "ftiv_text_style"

            with open(json_path, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get_all_tags(self) -> list[str]:
        """Collect normalized tags currently used across presets."""
        all_tags: set[str] = set()
        for preset in self.get_available_presets():
            for tag in preset.get("tags", []) or []:
                val = str(tag or "").strip().lower()
                if val:
                    all_tags.add(val)
        return sorted(all_tags)

    # managers/style_manager.py (抜粋・追加)

    def delete_style(self, json_path):
        """指定されたスタイルのJSONとサムネイル画像を削除"""
        try:
            if not os.path.exists(json_path):
                return False

            # JSON削除
            os.remove(json_path)

            # サムネイル削除 (存在すれば)
            base_path, _ = os.path.splitext(json_path)
            thumb_path = base_path + ".png"
            if os.path.exists(thumb_path):
                os.remove(thumb_path)

            return True
        except Exception:
            pass

            return False

    def generate_thumbnail(self, json_path: str) -> bool:
        """既存プリセットのサムネイルを（再）生成する。

        Args:
            json_path: プリセットJSONファイルパス。

        Returns:
            成功時 True、失敗時 False。
        """
        try:
            if not os.path.exists(json_path):
                return False

            with open(json_path, "r", encoding="utf-8") as f:
                style_data: dict[str, Any] = json.load(f)

            tmp_cfg: TextWindowConfig = TextWindowConfig()
            for k, v in style_data.items():
                if k.startswith("_"):
                    continue
                if hasattr(tmp_cfg, k):
                    try:
                        setattr(tmp_cfg, k, v)
                    except Exception:
                        pass
            tmp_cfg.text = "Aa あ"
            tmp_cfg.uuid = ""
            tmp_cfg.parent_uuid = None

            renderer: TextRenderer = TextRenderer()
            dummy = _TextRenderDummy(tmp_cfg)
            original_pixmap: QPixmap = renderer.render(dummy)

            thumb_size: int = 200
            scaled_pixmap: QPixmap = original_pixmap.scaled(
                thumb_size,
                thumb_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            final_thumb: QPixmap = QPixmap(thumb_size, thumb_size)
            final_thumb.fill(QColor(50, 50, 50))

            painter: QPainter = QPainter(final_thumb)
            try:
                x: int = (thumb_size - scaled_pixmap.width()) // 2
                y: int = (thumb_size - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
            finally:
                painter.end()

            base_path, _ = os.path.splitext(json_path)
            thumb_path: str = base_path + ".png"
            return bool(final_thumb.save(thumb_path, "PNG"))
        except Exception:
            traceback.print_exc()
            return False

    def apply_style_to_text_windows(self, windows, json_path):
        """
        複数のTextWindowに指定されたスタイルを一括適用する。
        Undo操作は1回分として記録される。
        """
        if not windows or not json_path or not os.path.exists(json_path):
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                style_data = json.load(f)

            # Undoマクロ開始 (全体で1つの操作とする)
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Batch Apply Style")

            count = 0
            for window in windows:
                # TextWindowのみ対象（念のため）
                if not hasattr(window, "update_text"):
                    continue

                # 各ウィンドウにプロパティを適用
                self._apply_data_to_window(window, style_data)
                count += 1

            # Undoマクロ終了
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to batch apply style: {e}")
            traceback.print_exc()

    def _apply_data_to_window(self, window, style_data):
        """
        単一のウィンドウにスタイルデータを適用するヘルパー
        ★ font_size に加え、is_vertical も除外する制御を追加
        """
        # Legacy compatibility:
        # Older presets may not contain background_visible. Infer it from opacity so
        # presets with visible card backgrounds still apply as users expect.
        if "background_visible" not in style_data and "background_opacity" in style_data:
            try:
                inferred_bg_visible = int(style_data["background_opacity"]) > 0
            except Exception:
                inferred_bg_visible = bool(style_data["background_opacity"])
            if hasattr(window, "background_visible"):
                window.set_undoable_property("background_visible", inferred_bg_visible, None)

        for field in self.text_style_fields:
            if field in style_data:
                # ★修正: フォントサイズは適用しない（現在のウィンドウのサイズを維持する）
                if field == "font_size":
                    continue

                # ★追加: 縦書き・横書き設定、およびオフセットモードはスタイル適用から除外する
                # これにより、プリセット読み込み時に勝手に縦書きになったりするのを防ぐ
                if field in ["is_vertical"]:
                    continue

                prop_name = field
                # マッピングが必要な場合の処理
                if field == "font":
                    prop_name = "font_family"

                if hasattr(window, prop_name):
                    val = style_data[field]

                    # set_undoable_property はコマンドを追加するだけなので、
                    # 外側で beginMacro されていればそこに積まれる
                    window.set_undoable_property(prop_name, val, None)

        # 最後に描画更新
        window.update_text()

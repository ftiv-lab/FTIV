# utils/translator.py

import json
import logging
import os
from typing import Any, Dict

from PySide6.QtCore import QObject, Signal


def _get_locales_search_paths() -> list[str]:
    """
    locales ディレクトリの探索候補を返す。
    utils.paths.resolve_path を使ってリソース位置を特定する。
    """
    import sys

    from utils.paths import resolve_path

    paths: list[str] = []

    # 1. utils/paths.py が解決するリソースルート直下の locales
    # (Nuitkaで --include-data-dir=utils/locales=locales とした場合など)
    paths.append(resolve_path("locales"))

    # 2. 開発中の構成 (utils/locales)
    paths.append(resolve_path("utils/locales"))

    # 3. 念のため実行ファイル基準 (Nuitkaの構成による保険)
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
        paths.append(os.path.join(base, "locales"))
        paths.append(os.path.join(base, "utils", "locales"))

    # 重複除去して存在確認
    valid_paths = []
    seen = set()
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        if os.path.isdir(p):
            valid_paths.append(p)

    return valid_paths


class Translator(QObject):
    """アプリケーションの多言語対応を管理するクラス。

    翻訳データを外部のJSONファイルから読み込み、動的な言語切り替え機能を提供します。
    """

    # 言語が変更された際に発行されるシグナル [cite: 142, 805]
    languageChanged = Signal()

    def __init__(self, default_lang: str = "jp"):
        """Translatorの初期化。

        Args:
            default_lang (str): デフォルトの言語コード。
        """
        super().__init__()
        self.current_lang: str = default_lang
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._load_all_translations()

    def _load_all_translations(self) -> None:
        """localesディレクトリから全ての翻訳ファイルを読み込む内部メソッド。"""
        langs = ["en", "jp"]

        # locales 探索（複数候補を試す）
        locales_path = None
        for cand in _get_locales_search_paths():
            if os.path.isdir(cand):
                locales_path = cand
                break

        if locales_path is None:
            logging.warning("locales directory not found. Translations will fallback to keys.")
            for lang in langs:
                self.translations[lang] = {}
            return

        for lang in langs:
            file_path = os.path.join(locales_path, f"{lang}.json")
            try:
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)
                else:
                    logging.warning("Translation file not found: %s", file_path)
                    self.translations[lang] = {}
            except Exception as e:
                logging.error("Error loading translation file %s: %s", lang, e)
                self.translations[lang] = {}

    def set_language(self, lang: str) -> None:
        """言語を切り替え、シグナルを通知する。 [cite: 142, 807]

        Args:
            lang (str): 設定する言語コード ('en' または 'jp')。
        """
        if self.current_lang != lang:
            self.current_lang = lang
            self.languageChanged.emit()

    def get_language(self) -> str:
        """現在の言語コードを取得する。 [cite: 808]

        Returns:
            str: 言語コード。
        """
        return self.current_lang

    def tr(self, key: str) -> str:  # type: ignore[override]
        """指定されたキーに対応する翻訳文字列を返す。"""
        # 現在の言語から取得を試みる
        lang_dict = self.translations.get(self.current_lang, {})
        result = lang_dict.get(key)
        if result is not None:
            return result

        # 現在の言語で見つからない場合は英語をフォールバックとして使用
        en_dict = self.translations.get("en", {})
        fallback = en_dict.get(key)

        # ログは debug（通常運用では出さない想定）
        if fallback is None:
            logging.debug("Missing translation key: '%s' (lang=%s)", key, self.current_lang)
            return key
        return fallback


# シングルトンインスタンスの作成 [cite: 815]
_translator = Translator()


def tr(key: str) -> str:
    """翻訳を取得するショートカット関数。 [cite: 816]"""
    return _translator.tr(key)


def set_lang(lang: str) -> None:
    """言語を設定するショートカット関数。 [cite: 817]"""
    _translator.set_language(lang)


def get_lang() -> str:
    """現在の言語を取得するショートカット関数。 [cite: 818]"""
    return _translator.get_language()

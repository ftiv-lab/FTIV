# utils/paths.py
import os
import sys


def is_compiled() -> bool:
    """NuitkaやPyInstallerでコンパイルされているか判定する。"""
    return getattr(sys, "frozen", False) or "__compiled__" in globals()


def get_base_dir() -> str:
    """
    設定ファイルやログを保存する「書き込み用」の基準ディレクトリ。
    """
    if is_compiled():
        # exeのパス (例: C:/.../FTIV_Free/bin/FTIV_Core.exe)
        exe_path = os.path.abspath(sys.argv[0])
        exe_dir = os.path.dirname(exe_path)

        # もし親フォルダ名が "bin" だったら、さらに一つ上を基準にする
        # (ランチャー構成の場合、データは bin の外に出したいため)
        if os.path.basename(exe_dir).lower() == "bin":
            return os.path.dirname(exe_dir)

        return exe_dir

    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resources_dir() -> str:
    """
    アイコンや翻訳ファイルなどの「読み込み用」リソースディレクトリを返す。
    - 開発時: プロジェクトルート
    - exe化時:
        - --onefile の場合: 一時解凍先 (sys._MEIPASS 等には依存せず、相対パス解決を試みる)
        - --standalone の場合: exeと同じ場所

    Notes:
        Nuitkaで --include-data-dir 等を使った場合、__file__ 基準で探すのが安全なことが多い。
    """
    if is_compiled():
        # Nuitkaの場合、__file__ はexe内部や一時フォルダを指すことがあるため
        # ここではシンプルに「exeのある場所」を基準にするのがトラブルが少ない
        # (リソースフォルダごと配布する想定)
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_path(relative_path: str) -> str:
    """リソースディレクトリ基準でパスを解決する。"""
    return os.path.join(get_resources_dir(), relative_path)

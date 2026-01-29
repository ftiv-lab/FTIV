import sys

# Check for Python < 3.14 (Nuitka compatibility)
if sys.version_info >= (3, 14):
    print("Error: Nuitka does not yet support Python 3.14+.")
    print("Please run this script with Python 3.13 (e.g., .venv313).")
    sys.exit(1)

import os
import shutil
import subprocess

# ==========================================
# 設定
# ==========================================
MAIN_SCRIPT = "main.py"
LAUNCHER_SCRIPT = "launcher.py"
EDITION_FILE = "utils/edition.py"
ICON_FILE = "icon.ico"
DIST_DIR = "dist"

# 本体（Core）のビルド設定: Standalone (爆速起動・ファイル多)
NUITKA_CORE_CMD = [
    sys.executable,
    "-m",
    "nuitka",
    "--standalone",
    "--enable-plugin=pyside6",
    "--windows-disable-console",
    f"--windows-icon-from-ico={ICON_FILE}",
    "--include-data-dir=utils/locales=utils/locales",
    "--follow-imports",
    f"--output-dir={DIST_DIR}",
    "--clean-cache=ccache",
    # Metadata for False Positive Reduction
    "--windows-company-name=Antigravity",
    "--windows-product-name=FTIV",
    "--windows-file-version=1.0.0.0",
    "--windows-product-version=1.0.0.0",
    "--windows-file-description=Floating Text Image Viewer",
]

# ランチャーのビルド設定: Onefile (ファイル1つ・中身空っぽなのですぐ起動)
NUITKA_LAUNCHER_CMD = [
    sys.executable,
    "-m",
    "nuitka",
    "--onefile",
    "--windows-disable-console",
    f"--windows-icon-from-ico={ICON_FILE}",
    f"--output-dir={DIST_DIR}",
    "--clean-cache=ccache",
    # Metadata
    "--windows-company-name=Antigravity",
    "--windows-product-name=FTIV Launcher",
    "--windows-file-version=1.0.0.0",
    "--windows-product-version=1.0.0.0",
    "--windows-file-description=FTIV Launcher",
]


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_package(edition_name="FTIV"):
    """
    標準パッケージをビルドし、フォルダ構成を整える関数
    (False Positive回避のため、Onefileをやめてディレクトリ形式で配布する)
    """
    print("=" * 60)
    print(f"Building Package: {edition_name} (Standalone Folder Mode)")
    print("=" * 60)

    # 1. 本体 (Core) のビルド -> FTIV.exe (これが直接実行ファイルになる)
    # output-filename を FTIV.exe にする
    exe_name = "FTIV.exe"

    # コマンド作成 (build_release.py の NUITKA_CORE_CMD を使うが、出力ファイル名だけ変える)
    cmd_core = NUITKA_CORE_CMD + [f"--output-filename={exe_name}", MAIN_SCRIPT]

    print(f"1. Building Core as Main Executable ({exe_name})...")
    subprocess.run(cmd_core, check=True)

    # Nuitka standalone は {output_dir}/{script_name}.dist に出力される
    # main.py -> dist/main.dist
    dist_src = os.path.join(DIST_DIR, "main.dist")

    # 3. フォルダ整理
    # 最終的なフォルダ: dist/FTIV/
    final_dir = os.path.join(DIST_DIR, edition_name)

    if os.path.exists(final_dir):
        shutil.rmtree(final_dir)

    # dist/main.dist を dist/FTIV にリネーム移動するのが一番早い
    # (shutil.move でフォルダ名変更)
    shutil.move(dist_src, final_dir)

    # Readme作成
    readme_path = os.path.join(final_dir, "Readme.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("【FTIV】\n\n")
        f.write(f"{exe_name} をダブルクリックして起動してください。\n")
        f.write("このフォルダ内のファイルは削除しないでください。\n")

    print(f"Done! Package created at: {final_dir}")


def main():
    if not os.path.exists(EDITION_FILE):
        print("Error: Edition file not found.")
        return

    # Clean DIST_DIR to avoid locks from previous runs
    if os.path.exists(DIST_DIR):
        try:
            # Only clean top level dist files that might conflict, or full clear
            # shutil.rmtree(DIST_DIR) # Might be risky if user has other things? No, dist is build output.
            pass
        except Exception:
            pass

    try:
        # Standard Build
        build_package("FTIV")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()

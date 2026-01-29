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
    """
    print("=" * 60)
    print(f"Building Package: {edition_name}")
    print("=" * 60)

    # 1. 本体 (Core) のビルド -> FTIV_Core.exe
    # output-filename を FTIV_Core.exe にする
    core_exe_name = "FTIV_Core.exe"
    cmd_core = NUITKA_CORE_CMD + [f"--output-filename={core_exe_name}", MAIN_SCRIPT]

    print(f"1. Building Core ({core_exe_name})...")
    subprocess.run(cmd_core, check=True)

    # Nuitka standalone は {output_dir}/{script_name}.dist に出力される
    # main.py -> dist/main.dist
    core_dist_src = os.path.join(DIST_DIR, "main.dist")

    # 2. ランチャーのビルド -> FTIV.exe
    # output-filename を FTIV.exe にする (これがユーザーが叩くファイル)
    launcher_exe_name = "FTIV.exe"

    cmd_launcher = NUITKA_LAUNCHER_CMD + [f"--output-filename={launcher_exe_name}", LAUNCHER_SCRIPT]

    print(f"2. Building Launcher ({launcher_exe_name})...")
    subprocess.run(cmd_launcher, check=True)

    # 生成されたランチャー (dist/FTIV.exe)
    launcher_src = os.path.join(DIST_DIR, launcher_exe_name)

    # 3. フォルダ整理
    # 最終的なフォルダ: dist/FTIV/
    final_dir = os.path.join(DIST_DIR, edition_name)

    if os.path.exists(final_dir):
        shutil.rmtree(final_dir)
    os.makedirs(final_dir)

    # binフォルダを作成
    bin_dir = os.path.join(final_dir, "bin")

    # コア(main.dist)の中身を bin に移動
    shutil.move(core_dist_src, bin_dir)

    # ランチャーをルートに移動
    shutil.move(launcher_src, os.path.join(final_dir, launcher_exe_name))

    # Readme作成
    readme_path = os.path.join(final_dir, "Readme.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("【FTIV】\n\n")
        f.write(f"{launcher_exe_name} をダブルクリックして起動してください。\n")
        f.write("bin フォルダ内のファイルは削除しないでください。\n")

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

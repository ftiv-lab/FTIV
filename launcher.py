# launcher.py
import os
import subprocess
import sys


def main():
    """
    binフォルダ内の本体EXEを起動するランチャー。
    自分自身の名前が 'FTIV.exe' なら 'bin/FTIV_Core.exe' を探して起動する。
    """
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # 本体のパス (bin/FTIV_Core.exe)
    # ※拡張子はWindows前提
    target_exe = os.path.join(base_dir, "bin", "FTIV_Core.exe")

    if not os.path.exists(target_exe):
        # 万が一見つからない場合
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0, f"Error: Could not find application core at:\n{target_exe}", "Launch Error", 0x10
        )
        sys.exit(1)

    # 引数をそのまま渡して起動
    # subprocess.Popen を使うことで、ランチャー自体はすぐ終了できる（または裏に回る）
    try:
        subprocess.Popen([target_exe] + sys.argv[1:])
    except Exception as e:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, f"Failed to launch application:\n{e}", "Launch Error", 0x10)


if __name__ == "__main__":
    main()

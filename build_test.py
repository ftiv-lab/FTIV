import subprocess
import sys

# Launcher Build Config (Fast Test)
# Build launcher.py -> simple onefile
ICON_FILE = "icon.ico"
DIST_DIR = "dist_test"

NUITKA_CMD = [
    sys.executable,
    "-m",
    "nuitka",
    "--onefile",
    "--windows-disable-console",
    f"--windows-icon-from-ico={ICON_FILE}",
    f"--output-dir={DIST_DIR}",
    "--clean-cache=ccache",
    "--output-filename=FTIV_Test.exe",
    "launcher.py",
]


def main():
    print("Running Nuitka Build Test on Python 3.14.2...")
    try:
        subprocess.run(NUITKA_CMD, check=True)
        print("Build Success!")
    except subprocess.CalledProcessError as e:
        print(f"Build Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

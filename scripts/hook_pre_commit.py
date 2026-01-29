import os
import subprocess
import sys

# Ensure scripts/utils is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.code_scanner import CodeScanner  # noqa: E402


class PreCommitHook:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.scanner = CodeScanner()
        self.issues_found = False

    def run(self):
        print("🔍 Running Virtual Pre-Commit Hook...")

        # 1. Code Scan (Regex)
        self._scan_files()

        # 2. Critical Lint (Ruff)
        self._run_critical_lint()

        if self.issues_found:
            print("\n❌ Pre-Commit Verification FAILED.")
            print("Please fix the issues above before committing.")
            sys.exit(1)
        else:
            print("\n✅ Pre-Commit Verification PASSED.")
            sys.exit(0)

    def _scan_files(self):
        print("   Checking for forbidden patterns (print, time.sleep, conflict markers)...")
        exclude_dirs = {
            ".git",
            ".venv",
            ".venv313",
            ".venv314",
            "__pycache__",
            ".ruff_cache",
            ".pytest_cache",
            ".agent",
            ".vscode",
            "dist",
            "build",
            "node_modules",
            "tools",
            "scripts",
        }

        for root, dirs, files in os.walk(self.root_dir):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if not file.endswith((".py", ".js", ".ts", ".html", ".css", ".jsx", ".tsx")):
                    continue

                # Exclude specific scripts
                if file in {"build_release.py", "build_test.py", "main.py", "launcher.py"}:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.root_dir)

                errors = self.scanner.scan_file(full_path)
                if errors:
                    self.issues_found = True
                    print(f"\n   [Pattern Violation] {rel_path}:")
                    for err in errors:
                        print(f"     - {err}")

    def _run_critical_lint(self):
        print("   Running critical lint check (Ruff)...")
        # Check only for Syntax Errors (E9, F63, F7, F82)
        # Using .venv314 python if available, else system python
        python_exe = sys.executable

        # Try to find local venv python if running from simpler context
        venv_python = os.path.join(self.root_dir, ".venv314", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_exe = venv_python

        cmd = [python_exe, "-m", "ruff", "check", "--select", "E9,F63,F7,F82", "--quiet", self.root_dir]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.issues_found = True
                print("\n   [Critical Lint Error] Ruff found critical issues:")
                print(result.stdout)
                print(result.stderr)
        except Exception as e:
            print(f"   [Warning] Failed to run Ruff: {e}")


if __name__ == "__main__":
    # Assume script is in scripts/ folder, so root is one level up
    root = os.path.abspath(os.path.join(current_dir, ".."))
    hook = PreCommitHook(root)
    hook.run()

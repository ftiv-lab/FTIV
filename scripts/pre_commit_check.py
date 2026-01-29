import os
import re
import sys

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".venv313",
    ".venv314",
    "__pycache__",
    "dist",
    "dist_test",
    ".ruff_cache",
    ".pytest_cache",
    ".agent",
    ".vscode",
    ".idea",
    "json",
}
EXCLUDED_FILES = {"pre_commit_check.py", "build_release.py", "build_test.py", "launcher.py"}

# Forbidden Patterns
PATTERNS = [
    # (Regex, Error Message, Severity)
    (r"^\s*print\(", "❌ 'print()' found. Use 'logging' instead.", "ERROR"),
    (r"pdb\.set_trace\(\)", "❌ Debugger 'pdb' found.", "ERROR"),
    (r"breakpoint\(\)", "❌ Debugger 'breakpoint()' found.", "ERROR"),
    (r"(?i)TODO\s*[:(]", "⚠️ TODO found. Ensure it is tracked.", "WARNING"),
    (r"(?i)FIXME", "⚠️ FIXME found. Do not commit broken code.", "WARNING"),
    (r"(['\"])(sk-proj-[a-zA-Z0-9]{20,})\1", "🚨 POTENTIAL API KEY FOUND! (OpenAI-like)", "CRITICAL"),
]


def scan_file(filepath):
    """Scans a single file for forbidden patterns."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                for pattern, msg, severity in PATTERNS:
                    if re.search(pattern, line):
                        # print() is allowed in this script itself, but we are scanning OTHERS.
                        # Also scripts/ might use print, so maybe exclude scripts dir?
                        # For now, let's keep it strict.
                        issues.append(f"[{severity}] {os.path.basename(filepath)}:{i}: {msg}")
    except Exception:
        # Ignore binary files or decode errors
        pass
    return issues


def main():
    print("🔍 Running Pre-Commit Sanity Check...")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    total_issues = 0
    critical_errors = 0

    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if file in EXCLUDED_FILES or not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            issues = scan_file(filepath)

            for issue in issues:
                print(issue)
                total_issues += 1
                if "ERROR" in issue or "CRITICAL" in issue:
                    critical_errors += 1

    print("-" * 40)
    if critical_errors > 0:
        print(f"❌ FAILED. Found {critical_errors} critical errors.")
        sys.exit(1)
    elif total_issues > 0:
        print(f"⚠️ PASSED with warnings ({total_issues} issues).")
        sys.exit(0)
    else:
        print("✅ PASSED. Clean code.")
        sys.exit(0)


if __name__ == "__main__":
    main()

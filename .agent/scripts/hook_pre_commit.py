import os
import sys

# Add current directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils.code_scanner import CodeScanner  # noqa: E402


def main():
    root_dir = os.getcwd()
    print(f"🔍 Running Pre-Commit Hook on: {root_dir}")
    print("---------------------------------------------------")

    scanner = CodeScanner(root_dir)
    violations = scanner.scan_directory()

    if not violations:
        print("✅ No critical violations found.")
        sys.exit(0)
    else:
        print(f"❌ Found {len(violations)} violations:")
        for v in violations:
            print(f"  - {v}")

        print("\n[Action Required] Please resolve these issues before committing.")
        print("Tip: Use 'Task: Fixing Pre-Commit Errors' if you need my help.")
        sys.exit(1)


if __name__ == "__main__":
    main()

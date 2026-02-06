import glob
import json
import os
import re
from typing import Dict, List, Tuple


def load_json(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return {}


def scan_python_files(root_dir: str) -> List[str]:
    files = []
    # Using glob to find all python files recursively
    # Note: glob.glob with recursive=True requires python 3.5+
    patterns = [
        os.path.join(root_dir, "*.py"),
        os.path.join(root_dir, "**", "*.py"),
        os.path.join(root_dir, "**", "**", "*.py"),
    ]
    for pattern in patterns:
        files.extend(glob.glob(pattern))

    # Remove duplicates and filter out venv/tools/build folders
    unique_files = list(set(files))
    filtered = [
        f
        for f in unique_files
        if ".venv" not in f
        and "dist" not in f
        and "build" not in f
        and "__pycache__" not in f
        and "audit_translation.py" not in f  # skip self
    ]
    return sorted(filtered)


def extract_tr_keys(file_path: str) -> List[Tuple[int, str]]:
    keys = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Regex for tr("key") or tr('key')
        # Simple regex, might miss complex cases but good enough for audit
        pattern = re.compile(r'tr\(\s*["\']([^"\']+)["\']\s*\)')

        for i, line in enumerate(lines):
            matches = pattern.findall(line)
            for key in matches:
                keys.append((i + 1, key))
    except Exception:
        pass
    return keys


def extract_potential_hardcodes(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Heuristic check for hardcoded strings in UI calls.
    Returns: (line_num, method_name, string_content)
    """
    candidates = []
    # Methods that usually take user-visible strings
    ui_methods = [
        "setText",
        "setWindowTitle",
        "setTitle",
        "QAction",
        "QPushButton",
        "QLabel",
        "QCheckBox",
        "QRadioButton",
        "QGroupBox",
        "QMessageBox.information",
        "QMessageBox.warning",
        "QMessageBox.critical",
        "QMessageBox.question",
        "setStatusTip",
        "setToolTip",
    ]

    # Regex to capture Method("String")
    # Captures: MethodName, Quote, Content, Quote
    pattern_str = r"(" + "|".join(ui_methods) + r')\(\s*(["\'])(.*?)\2'
    pattern = re.compile(pattern_str)

    ignore_list = [
        "",
        " ",
        "-",
        ":",
        "/",
        ".",
        "0",
        "1",
        "%",
        "qt_spinbox_lineedit",  # Internal Qt object name
        "utf-8",
        "r",
        "w",
        "wb",
        "rb",
        "json",
        "png",
        "jpg",  # File modes/exts
    ]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith("#"):
                continue

            matches = pattern.findall(line)
            for m in matches:
                method, quote, content = m
                if content not in ignore_list and len(content) > 1:
                    # Filter out obviously non-text things (identifiers, file paths roughly)
                    if re.match(r"^[a-zA-Z0-9_]+$", content):
                        continue  # Likely an ID or simple word
                    if "/" in content or "\\" in content:
                        continue  # Path

                    candidates.append((i + 1, method, content))
    except Exception:
        pass
    return candidates


def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    locales_dir = os.path.join(root_dir, "utils", "locales")
    report_path = os.path.join(root_dir, "translation_issues.md")

    print(f"Scanning root: {root_dir}")

    en_path = os.path.join(locales_dir, "en.json")
    jp_path = os.path.join(locales_dir, "jp.json")

    en_data = load_json(en_path)
    jp_data = load_json(jp_path)

    en_keys = set(en_data.keys())
    jp_keys = set(jp_data.keys())
    all_keys = en_keys | jp_keys

    issues = []

    # 1. Parity Check
    issues.append("# Translation Audit Report\n")
    issues.append("## 1. Parity Check (Key Mismatch)\n")

    missing_in_jp = en_keys - jp_keys
    missing_in_en = jp_keys - en_keys

    if not missing_in_jp and not missing_in_en:
        issues.append("- ✅ Parity OK: en.json and jp.json have identical keys.\n")
    else:
        if missing_in_jp:
            issues.append("### Missing in jp.json:\n")
            for k in sorted(missing_in_jp):
                issues.append(f"- `{k}` (Present in en.json)")
            issues.append("\n")

        if missing_in_en:
            issues.append("### Missing in en.json:\n")
            for k in sorted(missing_in_en):
                issues.append(f"- `{k}` (Present in jp.json)")
            issues.append("\n")

    # 2. Reference Check (Used vs Defined)
    issues.append("## 2. Usage Check (Code vs JSON)\n")

    py_files = scan_python_files(root_dir)
    used_keys = set()
    undefined_keys = []

    for py_file in py_files:
        found = extract_tr_keys(py_file)
        rel_path = os.path.relpath(py_file, root_dir)
        for line, key in found:
            used_keys.add(key)
            if key not in all_keys:
                undefined_keys.append(f"- [ ] `{key}` in `{rel_path}:{line}`")

    if not undefined_keys:
        issues.append("- ✅ All `tr()` keys are defined in JSON.\n")
    else:
        issues.append("### Undefined Keys (Used in code but missing in JSON):\n")
        for issue in undefined_keys:
            issues.append(issue)
        issues.append("\n")

    # Unused keys check
    unused_keys = all_keys - used_keys
    # Filter out likely dynamic keys (e.g. constructed programmatically) or known reserved
    # This is noisy, so maybe putting it in a collapsed section or less prominent
    issues.append("### Potentially Unused Keys (Defined but not found in `tr(...)`):\n")
    issues.append("> Note: Keys might be constructed dynamically or used in other ways.\n")
    if unused_keys:
        count = 0
        for k in sorted(unused_keys):
            if count < 20:  # Limit output
                issues.append(f"- `{k}`")
            count += 1
        if count > 20:
            issues.append(f"- ... and {count - 20} more.")
    else:
        issues.append("- None detected.\n")
    issues.append("\n")

    # 3. Hardcode Check (Heuristic)
    issues.append("## 3. Potential Hardcoded Strings\n")
    issues.append("> Please manually review these. Many might be valid (IDs, tech terms).\n")

    hardcode_count = 0
    for py_file in py_files:
        candidates = extract_potential_hardcodes(py_file)
        if candidates:
            rel_path = os.path.relpath(py_file, root_dir)
            file_issues = []
            for line, method, content in candidates:
                # Stronger filter?
                if " " in content:  # Sentences are high probability
                    file_issues.append(f'- [ ] `{rel_path}:{line}` : `{method}("{content}")`')

            if file_issues:
                for fi in file_issues:
                    issues.append(fi)
                    hardcode_count += 1

    if hardcode_count == 0:
        issues.append("- ✅ No obvious hardcoded strings found in typical UI methods.\n")

    # Write Report
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(issues)

    print(f"Audit complete. Report saved to: {report_path}")


if __name__ == "__main__":
    main()

import os
import re
from typing import List, Pattern, Tuple


class ScanViolation:
    def __init__(self, file_path: str, line_num: int, line_content: str, reason: str):
        self.file_path = file_path
        self.line_num = line_num
        self.line_content = line_content.strip()
        self.reason = reason

    def __str__(self):
        return f"[{self.reason}] {self.file_path}:{self.line_num} -> {self.line_content}"


class CodeScanner:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

        # Define patterns
        self.forbidden_patterns: List[Tuple[str, Pattern]] = [
            ("Legacy Print Debug", re.compile(r"^\s*print\(")),
            ("JS Console Log", re.compile(r"console\.log\(")),
            ("Conflict Marker", re.compile(r"^<{7} |^>{7} |^={7}$")),
            ("Hardcoded Breakpoint", re.compile(r"import pdb; pdb\.set_trace\(\)")),
            ("Sleep in Logic", re.compile(r"time\.sleep\(")),
            ("Direct Parent Access", re.compile(r"\.parent\(\)\.")),  # Simple heuristic for parent().child
        ]

        # Excludes
        self.excludes = [
            r"^\.git",
            r"^\.agent",
            r"^\.venv",
            r"__pycache__",
            r"\.mypy_cache",
            r"logs",
            r"docs",
            r"build_release\.py",
        ]

    def _should_ignore(self, file_path: str) -> bool:
        rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
        for exc in self.excludes:
            if re.search(exc, rel_path):
                return True
        return False

    def scan_file(self, file_path: str) -> List[ScanViolation]:
        violations = []
        if self._should_ignore(file_path):
            return violations

        # Specific rule relaxations
        is_test = "test" in file_path.lower() or "verify_" in file_path.lower()
        is_script = "scripts" in file_path.lower() or "tools" in file_path.lower()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    for reason, pattern in self.forbidden_patterns:
                        # Relaxations
                        if reason == "Sleep in Logic" and (is_test or is_script):
                            continue
                        if reason == "Legacy Print Debug" and (is_script or is_test):
                            continue
                        if reason == "Direct Parent Access" and is_test:
                            continue

                        if pattern.search(line):
                            # Comment detection (very basic)
                            if line.strip().startswith("#") or line.strip().startswith("//"):
                                continue

                            violations.append(ScanViolation(file_path, i, line, reason))
        except Exception:
            print(f"Error scanning {file_path}")

        return violations

    def scan_directory(self) -> List[ScanViolation]:
        all_violations = []
        for root, dirs, files in os.walk(self.root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]

            for file in files:
                if not file.endswith((".py", ".js", ".ts", ".tsx")):
                    continue

                full_path = os.path.join(root, file)
                all_violations.extend(self.scan_file(full_path))

        return all_violations

import re
from typing import List, Pattern, Tuple


class CodeScanner:
    """ソースコード内の禁止パターンやデバッグ残留物を検出するスキャナ。"""

    # 禁止パターン定義
    # (Pattern, Error Message, Allow in Tests?)
    PATTERNS: List[Tuple[Pattern, str, bool]] = [
        # Debug Prints
        (re.compile(r"^\s*print\("), "Debug print found", True),  # Allow in tests
        (re.compile(r"^\s*console\.log\("), "Console.log found", True),
        (re.compile(r"import pdb;?\s*pdb\.set_trace\(\)"), "PDB breakpoint found", False),
        # Conflict Markers
        (re.compile(r"^<<<<<<< HEAD"), "Git conflict marker (HEAD) found", False),
        (re.compile(r"^=======$"), "Git conflict marker (SEPARATOR) found", False),
        (re.compile(r"^>>>>>>>"), "Git conflict marker (INCOMING) found", False),
        # Forbidden Patterns
        (re.compile(r"time\.sleep\("), "time.sleep() is forbidden (use Signal/Slot or QTimer)", True),
        (re.compile(r"\.parent\(\)\.child\("), "High coupling pattern: parent().child()", False),
    ]

    def scan_line(self, line: str, line_no: int, is_test_file: bool) -> List[str]:
        """1行をスキャンし、違反があればエラーメッセージを返す。"""
        errors = []
        for pattern, msg, allow_in_test in self.PATTERNS:
            if allow_in_test and is_test_file:
                continue

            if pattern.search(line):
                # print() などをコメントアウトしている場合は除外したいが、
                # 簡易的な実装として "#" が行頭にある場合のみスキップする等のロジックを入れるか、
                # あるいは厳しく「コメントアウトでも残すな」とするか。
                # ここでは「行頭コメント以外でヒットしたらNG」とする。
                if line.strip().startswith("#"):
                    continue

                errors.append(f"Line {line_no}: {msg} -> {line.strip()[:60]}...")
        return errors

    def scan_file(self, file_path: str) -> List[str]:
        """ファイルを読み込み、違反をスキャンする。"""
        errors = []
        is_test_file = "check_" in file_path or "test_" in file_path or "tests/" in file_path or "_test" in file_path

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    line_errors = self.scan_line(line, i, is_test_file)
                    if line_errors:
                        errors.extend(line_errors)
        except UnicodeDecodeError:
            # バイナリファイル等はスキップ
            pass
        except Exception as e:
            errors.append(f"Failed to scan file: {e}")

        return errors

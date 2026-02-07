#!/usr/bin/env python
"""
Task Manager for Hybrid AI Workflow

Phase-Driven AI Workflowを管理するためのCLIツール。
タスクの初期化、フェーズ遷移、ハンドオフファイル生成、完了処理を自動化する。

Usage:
    python scripts/task_manager.py init "タスクタイトル"
    python scripts/task_manager.py start-phase 1
    python scripts/task_manager.py complete-phase
    python scripts/task_manager.py complete-task
    python scripts/task_manager.py rollback-phase
    python scripts/task_manager.py status
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
TASK_DIR = PROJECT_ROOT / ".ftiv-task"
ARCHIVE_DIR = TASK_DIR / "archive"
AGENT_DIR = PROJECT_ROOT / ".agent"
TEMPLATES_DIR = AGENT_DIR / "templates"

# フェーズ定義
PHASES = {
    1: {"name": "Design", "ai": "Claude", "template": "phase_1_design.md"},
    2: {"name": "Implementation", "ai": "Gemini", "template": "phase_2_implementation.md"},
    3: {"name": "Refinement", "ai": "Claude", "template": "phase_3_refinement.md"},
    4: {"name": "Testing", "ai": "Gemini", "template": "phase_4_testing.md"},
}


class TaskManager:
    """タスク管理クラス。"""

    def __init__(self):
        """初期化。"""
        self.task_dir = TASK_DIR
        self.archive_dir = ARCHIVE_DIR
        self.state_file = self.task_dir / "current_state.json"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """必要なディレクトリを作成。"""
        self.task_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)

    def _load_state(self) -> Optional[Dict]:
        """現在の状態を読み込む。"""
        if not self.state_file.exists():
            return None
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_state(self, state: Dict):
        """状態を保存。"""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _get_next_task_id(self) -> str:
        """次のタスクIDを生成。"""
        existing_dirs = [d for d in self.task_dir.iterdir() if d.is_dir() and d.name.startswith("TASK-")]
        if not existing_dirs:
            return "TASK-001"
        task_numbers = [int(d.name.split("-")[1]) for d in existing_dirs]
        next_num = max(task_numbers) + 1
        return f"TASK-{next_num:03d}"

    def init_task(self, title: str, hotfix: bool = False):
        """タスクを初期化。"""
        if self._load_state() is not None:
            print("⚠️  既存のタスクが進行中です。先に完了してください。")
            print("   python scripts/task_manager.py status")
            sys.exit(1)

        task_id = self._get_next_task_id()
        task_path = self.task_dir / task_id
        task_path.mkdir()

        state = {
            "task_id": task_id,
            "title": title,
            "current_phase": 1,
            "hotfix": hotfix,
            "started_at": datetime.now().isoformat(),
            "phase_history": [],
        }
        self._save_state(state)

        print(f"✅ タスク初期化完了: {task_id}")
        print(f"   タイトル: {title}")
        print(f"   ディレクトリ: {task_path}")
        print()
        print("📋 次のステップ:")
        print("   python scripts/task_manager.py start-phase 1")

    def start_phase(self, phase_num: Optional[int] = None):
        """フェーズを開始。"""
        state = self._load_state()
        if state is None:
            print("❌ タスクが初期化されていません。")
            print('   python scripts/task_manager.py init "タスクタイトル"')
            sys.exit(1)

        if phase_num is None:
            phase_num = state["current_phase"]

        if phase_num not in PHASES:
            print(f"❌ 無効なフェーズ番号: {phase_num}")
            sys.exit(1)

        phase_info = PHASES[phase_num]
        task_id = state["task_id"]

        print(f"🚀 Phase {phase_num} 開始: {phase_info['name']} ({phase_info['ai']}担当)")
        print()
        print(f"📖 テンプレート: .agent/templates/{phase_info['template']}")
        print()

        # テンプレートを表示
        template_path = TEMPLATES_DIR / phase_info["template"]
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            # 変数置換
            template_content = template_content.replace("{{TASK_ID}}", task_id)
            template_content = template_content.replace("{{TASK_TITLE}}", state["title"])
            template_content = template_content.replace("{{START_TIME}}", datetime.now().isoformat())
            print("=" * 70)
            print(template_content[:500])  # 最初の500文字のみ表示
            print("=" * 70)
            print()
            print("📄 完全なテンプレートは以下で確認:")
            print(f"   cat .agent/templates/{phase_info['template']}")

        # フェーズ履歴に記録
        state["phase_history"].append(
            {"phase": phase_num, "started_at": datetime.now().isoformat(), "ai": phase_info["ai"]}
        )
        self._save_state(state)

    def complete_phase(self):
        """フェーズを完了し、次フェーズへ遷移。"""
        state = self._load_state()
        if state is None:
            print("❌ タスクが初期化されていません。")
            sys.exit(1)

        current_phase = state["current_phase"]
        phase_info = PHASES[current_phase]

        print(f"✅ Phase {current_phase} ({phase_info['name']}) 完了")

        # ハンドオフファイル生成
        self._generate_handoff(state, current_phase)

        # 次フェーズへ
        if current_phase < 4:
            next_phase = current_phase + 1
            next_phase_info = PHASES[next_phase]
            state["current_phase"] = next_phase

            # フェーズ履歴更新
            state["phase_history"][-1]["completed_at"] = datetime.now().isoformat()

            self._save_state(state)

            print()
            print(f"🔄 次フェーズ: Phase {next_phase} ({next_phase_info['name']}) - {next_phase_info['ai']}担当")
            print()
            print("📋 次のステップ:")
            print(f"   python scripts/task_manager.py start-phase {next_phase}")
        else:
            print()
            print("🎉 全フェーズ完了！タスクを完了してください。")
            print("   python scripts/task_manager.py complete-task")

    def _generate_handoff(self, state: Dict, phase: int):
        """ハンドオフファイルを生成。"""
        task_id = state["task_id"]
        task_path = self.task_dir / task_id

        if phase == 1:
            # Phase 1 → Phase 2: Gemini向けハンドオフ
            handoff_file = task_path / "handoff_to_gemini.md"
            content = f"""# Handoff to Gemini (Phase 2)

**From**: Claude (Phase 1)
**To**: Gemini (Phase 2)
**Generated**: {datetime.now().isoformat()}

---

## 📋 タスク概要
{state["title"]}

## 📖 必読ドキュメント
1. `.ftiv-task/{task_id}/design_spec.md` - 設計仕様書
2. `.ftiv-task/{task_id}/adr.md` - アーキテクチャ決定記録

## 🎯 実装範囲
[Claudeが Design Spec作成時に具体的に記載]

## ⚠️ 重要な制約
- Design Specに書かれていないことは実装しない
- 既存コードのスタイルに従う
- .venv314 の Python 3.14 環境を使用

## 🔧 実装手順
1. [ステップ1]
2. [ステップ2]
3. [ステップ3]

## ✅ 動作確認方法
```bash
pytest tests/ -v
python main.py
# → [確認項目]
```

## 📝 実装ログに記録すべきこと
- 実装した内容（ファイル・行数）
- Design Specからの変更点（あれば）
- 気づいた問題点・改善提案

---

**次のステップ**: Phase 2 Implementation開始
"""
            with open(handoff_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"📤 ハンドオフファイル生成: {handoff_file}")

        elif phase == 2:
            # Phase 2 → Phase 3: Claude向けハンドオフ
            handoff_file = task_path / "handoff_to_claude.md"
            content = f"""# Handoff to Claude (Phase 3)

**From**: Gemini (Phase 2)
**To**: Claude (Phase 3)
**Generated**: {datetime.now().isoformat()}

---

## 📋 実装サマリー
{state["title"]} の実装が完了しました。

## 📖 必読ドキュメント
1. `.ftiv-task/{task_id}/implementation_log.md` - 実装ログ
2. `.ftiv-task/{task_id}/design_spec.md` - 設計仕様書（参照）

## 📂 変更ファイルリスト
[Geminiが implementation_log に記録]

## 🔄 Design Specからの変更
[変更点とその理由]

## 🔍 Claudeに確認してほしいこと
1. [確認事項1: アーキテクチャの妥当性]
2. [確認事項2: セキュリティリスク]
3. [確認事項3: パフォーマンス懸念]

## ⚠️ 気づいた問題
- [問題1]
- [問題2]

## ✅ テスト結果
```bash
pytest tests/ -v
# 結果: XXX passed
```

---

**次のステップ**: Phase 3 Refinement開始
"""
            with open(handoff_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"📤 ハンドオフファイル生成: {handoff_file}")

        elif phase == 3:
            # Phase 3 → Phase 4: Gemini向けテスト指示
            handoff_file = task_path / "handoff_to_gemini_test.md"
            content = f"""# Handoff to Gemini (Phase 4)

**From**: Claude (Phase 3)
**To**: Gemini (Phase 4)
**Generated**: {datetime.now().isoformat()}

---

## 📋 テスト実装タスク
{state["title"]} のテストスイート作成をお願いします。

## 📖 必読ドキュメント
1. `.ftiv-task/{task_id}/review_report.md` - レビュー報告書
2. `.ftiv-task/{task_id}/design_spec.md` - テスト観点（Phase 1から）

## ✅ テスト実装項目
[Claudeが Phase 1のテスト観点から具体的なテストケースに変換]

### 正常系テスト
- [ ] `test_xxx`: [テスト内容]
- [ ] `test_yyy`: [テスト内容]

### 異常系テスト
- [ ] `test_error_xxx`: [テスト内容]

### エッジケーステスト
- [ ] `test_edge_xxx`: [テスト内容]

## 🎯 重点確認項目
- [確認項目1: パフォーマンス基準]
- [確認項目2: エラーハンドリング]

## ⚠️ 注意事項
- qapp フィクスチャを使用

- 既存テストのスタイルに従う

---

**次のステップ**: Phase 4 Testing開始
"""
            with open(handoff_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"📤 ハンドオフファイル生成: {handoff_file}")

    def complete_task(self):
        """タスクを完了し、アーカイブする。"""
        state = self._load_state()
        if state is None:
            print("❌ タスクが初期化されていません。")
            sys.exit(1)

        if state["current_phase"] != 4:
            print(f"⚠️  Phase 4が完了していません。現在: Phase {state['current_phase']}")
            sys.exit(1)

        task_id = state["task_id"]
        task_path = self.task_dir / task_id

        # 完了報告書を生成
        report_file = task_path / "task_completion_report.md"
        duration = (datetime.now() - datetime.fromisoformat(state["started_at"])).total_seconds() / 3600
        content = f"""# Task Completion Report

**Task ID**: {task_id}
**Title**: {state["title"]}
**Started**: {state["started_at"]}
**Completed**: {datetime.now().isoformat()}
**Total Duration**: {duration:.2f} hours

---

## Phase Summary

"""
        for entry in state["phase_history"]:
            phase_num = entry["phase"]
            phase_info = PHASES[phase_num]
            content += f"### Phase {phase_num}: {phase_info['name']} ({phase_info['ai']})\n"
            content += f"- Started: {entry['started_at']}\n"
            if "completed_at" in entry:
                content += f"- Completed: {entry['completed_at']}\n"
            content += "\n"

        content += """
## Deliverables

- Phase 1: ADR, Design Spec
- Phase 2: Implementation Code, Implementation Log
- Phase 3: Refined Code, Review Report
- Phase 4: Test Suite, Test Report

---

🎊 **Task completed successfully!**
"""
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(content)

        # アーカイブ
        archive_path = self.archive_dir / task_id
        shutil.move(str(task_path), str(archive_path))

        # 状態ファイル削除
        self.state_file.unlink()

        print(f"🎉 タスク完了: {task_id}")
        print(f"   タイトル: {state['title']}")
        print(f"   所要時間: {duration:.2f} hours")
        print(f"   アーカイブ先: {archive_path}")
        print()
        print(f"📄 完了報告書: {archive_path / 'task_completion_report.md'}")

    def rollback_phase(self):
        """前フェーズにロールバック。"""
        state = self._load_state()
        if state is None:
            print("❌ タスクが初期化されていません。")
            sys.exit(1)

        current_phase = state["current_phase"]
        if current_phase == 1:
            print("⚠️  Phase 1からはロールバックできません。")
            sys.exit(1)

        prev_phase = current_phase - 1
        state["current_phase"] = prev_phase

        # 履歴から最後のエントリを削除
        if state["phase_history"]:
            state["phase_history"].pop()

        self._save_state(state)

        print(f"⏪ Phase {current_phase} → Phase {prev_phase} にロールバックしました。")
        print()
        print("📝 ロールバック理由を記録してください:")
        task_id = state["task_id"]
        reason_file = self.task_dir / task_id / "rollback_reason.md"
        print(f'   echo "理由" >> {reason_file}')

    def status(self):
        """現在の状態を表示。"""
        state = self._load_state()
        if state is None:
            print("ℹ️  進行中のタスクはありません。")
            print()
            print("新しいタスクを開始:")
            print('   python scripts/task_manager.py init "タスクタイトル"')
            return

        task_id = state["task_id"]
        current_phase = state["current_phase"]
        phase_info = PHASES[current_phase]

        print(f"📋 現在のタスク: {task_id}")
        print(f"   タイトル: {state['title']}")
        print(f"   開始日時: {state['started_at']}")
        print()
        print(f"🔄 現在のフェーズ: Phase {current_phase} - {phase_info['name']}")
        print(f"   担当AI: {phase_info['ai']}")
        print()
        print("📚 フェーズ履歴:")
        for entry in state["phase_history"]:
            phase_num = entry["phase"]
            phase_info = PHASES[phase_num]
            status_icon = "✅" if "completed_at" in entry else "🔄"
            print(f"   {status_icon} Phase {phase_num}: {phase_info['name']} ({entry['ai']})")
        print()
        print("📋 次のステップ:")
        print(f"   python scripts/task_manager.py start-phase {current_phase}")


def main():
    """メイン関数。"""
    parser = argparse.ArgumentParser(description="Task Manager for Hybrid AI Workflow")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize a new task")
    init_parser.add_argument("title", help="Task title")

    # init-hotfix
    hotfix_parser = subparsers.add_parser("init-hotfix", help="Initialize a hotfix task")
    hotfix_parser.add_argument("title", help="Hotfix title")

    # start-phase
    start_parser = subparsers.add_parser("start-phase", help="Start a phase")
    start_parser.add_argument("phase", type=int, nargs="?", help="Phase number (1-4)")

    # complete-phase
    subparsers.add_parser("complete-phase", help="Complete current phase")

    # complete-task
    subparsers.add_parser("complete-task", help="Complete the task and archive")

    # rollback-phase
    subparsers.add_parser("rollback-phase", help="Rollback to previous phase")

    # status
    subparsers.add_parser("status", help="Show current task status")

    args = parser.parse_args()

    manager = TaskManager()

    if args.command == "init":
        manager.init_task(args.title)
    elif args.command == "init-hotfix":
        manager.init_task(args.title, hotfix=True)
    elif args.command == "start-phase":
        manager.start_phase(args.phase)
    elif args.command == "complete-phase":
        manager.complete_phase()
    elif args.command == "complete-task":
        manager.complete_task()
    elif args.command == "rollback-phase":
        manager.rollback_phase()
    elif args.command == "status":
        manager.status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

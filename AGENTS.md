# AGENTS.md

This file defines mandatory startup and execution rules for Codex/Claude-style coding agents working in this repository.

## 1. Mandatory Startup Reads

At the start of every new session (especially after VS Code restart), read these files first:

1. `docs/internal/CURRENT_STATUS_DASHBOARD.md`
2. `docs/internal/guides/AGENT_READING_LIST.md`
3. `docs/internal/guides/codex_vscode_stability_notes.md`
4. `docs/internal/guides/planning_governance_rules.md` **(計画提案ルール — 必読)**

Do not start implementation before reading all four.

If `docs/internal/` is not available in the current environment (e.g. fresh clone / shared CI workspace), use this fallback entrypoint:

1. `docs/RUNBOOK.md`

In fallback mode, treat `docs/RUNBOOK.md` as the primary startup guide and execution contract.

## 2. VS Code Stability Rules (High Priority)

- Run approval-needed operations one at a time.
- Do not run parallel operations that can stack approval dialogs.
- Before each command, state only the next single action briefly.
- Prefer this order: read -> confirm -> next step.
- If the session appears stuck, do not queue more actions; recover first.

## 3. Execution Standards

- Use `uv run ...` for Python tooling and tests.
- Use targeted tests during development (small scope first).
- Use `cmd /c verify_all.bat` as final integrated verification.
- Keep push as human-only unless explicitly requested otherwise.

## 4. Documentation and Memory

- Treat `docs/internal/guides/MEMORY.md` as the source of latest recorded test/coverage snapshot.
- If behavior or workflow changes, update relevant docs in `docs/internal/guides/` and `docs/internal/`.

## 5. Communication Style

- Keep progress updates short and frequent.
- Avoid asking multiple yes/no decisions in one message.
- If a blocker occurs, report concrete cause and propose one next action.

## 6. Planning Governance (計画提案ルール — High Priority)

- **計画を提案する前に `docs/internal/guides/planning_governance_rules.md` を必ず読むこと。**
- 同じテーマの連続フェーズは **最大3つまで** （4つ目は人間の承認が必要）。
- インフラ系フェーズが3つ連続したら、次は **必ず機能系に戻る** 。
- すべての計画に「ユーザーへの効果」「このフェーズで終わる理由」を書くこと。
- 1日に提案できる計画書は **最大3個まで** 。
- 計画の内容を開発者（初心者）が理解できない場合、それは **計画が複雑すぎる** 。
- 詳細: `docs/internal/guides/planning_governance_rules.md`

## 7. PowerShell UTF-8 / Mojibake Prevention (High Priority)

- Treat `????` output as a stop signal. Do not continue editing until encoding is re-verified.
- Before UTF-8 text reads in PowerShell, set UTF-8 console output explicitly:
  - `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`
  - Use `Get-Content -Encoding UTF8`
- For non-ASCII/Japanese document edits, prefer `apply_patch` over shell heredoc/python inline scripts.
- If a file appears garbled in terminal output, verify file bytes via Python read (`encoding='utf-8'`) before any write.
- Keep encoding-related operations single-step (read -> verify -> write) to avoid compounding corruption.
- Recommended one-time local setup: configure `$PROFILE` to force UTF-8 defaults for each PowerShell session.
  - `$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8`
  - `[Console]::InputEncoding = [System.Text.Encoding]::UTF8`

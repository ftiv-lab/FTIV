# AGENTS.md

This file defines mandatory startup and execution rules for Codex/Claude-style coding agents working in this repository.

## 1. Mandatory Startup Reads

At the start of every new session (especially after VS Code restart), read these files first:

1. `docs/internal/guides/AGENT_READING_LIST.md`
2. `docs/internal/guides/codex_vscode_stability_notes.md`

Do not start implementation before reading both.

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

## 6. PowerShell UTF-8 / Mojibake Prevention (High Priority)

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

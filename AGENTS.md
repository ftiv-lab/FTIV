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

# Handoff Folder for Gemini

This folder contains Design Specifications created by Claude Code.

## How to Use

1. Claude Code creates a design spec file here (e.g., `TASK_feature_name.md`)
2. Open the file and pass it to Gemini (Antigravity)
3. Gemini implements according to the spec
4. Delete or archive the file after implementation

## Design Spec Format

Each file contains:
- **Requirements Summary**: What to build
- **Affected Files**: Which files to modify/create
- **Interface Design**: Method signatures (no implementation)
- **Implementation Instructions**: Step-by-step guide
- **Test Cases**: What to test

## Important Notes

- Design specs contain NO implementation code
- Follow the interface signatures exactly
- Implement in the order specified
- Run existing tests after each change

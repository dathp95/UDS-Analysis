---
description: Git, generated-data, and repository hygiene rules
alwaysApply: true
fileMatching: "**/*"
---

# Git And Data Hygiene

## Commit These When Intentional

- source files in `core/`, `gui/`, `config/`, and root Python files
- `README.md`, `requirements.txt`, and other project docs
- `AGENTS.md`
- `.cursor/rules/`
- `.codex/skills/`
- `ai-rules/`
- project input config such as `config/ecu_config.xlsx`

## Do Not Commit These

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `logs/`
- `output/`
- generated Excel reports
- converted logs
- temporary cache/build/dist folders

## Git Workflow

When asked to link, commit, or push:

1. Check whether Git is installed.
2. Check whether `.git` exists.
3. Preserve or create `.gitignore`.
4. Initialize only if `.git` is absent.
5. Set or verify `origin`.
6. Stage intended files only.
7. Commit with a concise message.
8. Push only when authentication and remote access are available.

If Git, GitHub auth, or the remote repository is unavailable, stop after preparing local files and report the exact blocker.


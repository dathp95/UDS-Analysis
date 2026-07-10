---
description: Required workflow and verification rules for agent work
alwaysApply: true
fileMatching: "**/*"
---

# Workflow And Verification

## Default Workflow

1. Restate the intended scope in your own words.
2. Read only the relevant files needed for the task.
3. Decide whether the user explicitly allowed runtime logic changes.
4. If logic edits are not allowed, edit only rules, skills, docs, Git metadata, or other non-runtime artifacts.
5. Make narrow edits that follow the existing project style.
6. Verify with the lightest useful command.
7. Report changed files, verification results, and any blocker.

## Verification By Change Type

- Rule, docs, or skill changes: inspect changed files and validate formatting/frontmatter where possible.
- Git metadata changes: run Git status when Git is available.
- Runtime logic changes, only when explicitly requested: run focused Python checks against known sample logs/configs.
- GUI changes, only when explicitly requested: run the app or provide a clear manual check when a GUI session is unavailable.

## Skill Validation

Use this command when `PyYAML` is available:

```powershell
python C:/Users/LENOVO/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/python-uds-analyzer
```

If the validator cannot run because `yaml` is missing, report that blocker instead of silently skipping validation.


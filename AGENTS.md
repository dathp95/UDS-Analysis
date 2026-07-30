# Agent Operating Rules

This repository uses project-local agent skills in `.codex/skills`. These rules are mandatory for every agent working in this workspace.

## Non-Negotiable Skill Policy

Before doing any task, the agent must:

1. Inspect `.codex/skills/using-agent-skills/SKILL.md`.
2. Decide which project-local skill(s) apply to the current user request.
3. Read the full `SKILL.md` for every selected skill before taking task actions.
4. If a selected `SKILL.md` references required files, read only the relevant referenced files before acting.
5. State briefly which skill(s) are being used and why.
6. Follow the selected skill workflow, including its verification step.
7. In the final response, mention the important verification that was performed, or clearly say what could not be verified.

Do not treat skills as optional guidance. They are project workflow rules.

## Skill Source Of Truth

Use project-local skills first:

- `.codex/skills/using-agent-skills`
- `.codex/skills/context-engineering`
- `.codex/skills/spec-driven-development`
- `.codex/skills/planning-and-task-breakdown`
- `.codex/skills/incremental-implementation`
- `.codex/skills/test-driven-development`
- `.codex/skills/debugging-and-error-recovery`
- `.codex/skills/code-review-and-quality`
- `.codex/skills/code-simplification`
- `.codex/skills/frontend-ui-engineering`
- `.codex/skills/api-and-interface-design`
- `.codex/skills/security-and-hardening`
- `.codex/skills/performance-optimization`
- `.codex/skills/source-driven-development`
- `.codex/skills/doubt-driven-development`
- `.codex/skills/git-workflow-and-versioning`
- `.codex/skills/documentation-and-adrs`
- `.codex/skills/ci-cd-and-automation`
- `.codex/skills/deprecation-and-migration`
- `.codex/skills/observability-and-instrumentation`
- `.codex/skills/shipping-and-launch`
- `.codex/skills/idea-refine`
- `.codex/skills/interview-me`
- `.codex/skills/browser-testing-with-devtools`

If the runtime also has global skills installed, project-local skills take precedence when names overlap.

## Default Skill Routing

- Ambiguous request: use `interview-me` before planning or coding.
- Rough idea: use `idea-refine`.
- New feature or significant behavior change: use `spec-driven-development`, then `planning-and-task-breakdown`.
- Any multi-file implementation: use `incremental-implementation`.
- Any logic change, bug fix, or behavior change: use `test-driven-development`.
- Unexpected failure: use `debugging-and-error-recovery`.
- UI work: use `frontend-ui-engineering`.
- API, module boundary, or public contract work: use `api-and-interface-design`.
- Security-sensitive work or untrusted input: use `security-and-hardening`.
- Performance work: use `performance-optimization`.
- External framework/library correctness: use `source-driven-development`.
- High-stakes or unfamiliar code: use `doubt-driven-development`.
- Any code change in git: use `git-workflow-and-versioning`.
- Before merge or final handoff of a code change: use `code-review-and-quality`.
- Docs, decisions, or ADRs: use `documentation-and-adrs`.

## Project Context Rules

Before editing code:

1. Run `git status --short` and preserve unrelated user changes.
2. Read the files that will be modified.
3. Search for an existing local pattern with `rg` before inventing a new pattern.
4. Keep changes scoped to the user's request.
5. Do not modify generated output, logs, licenses, secrets, or vehicle configuration data unless explicitly requested.

## Verification Rules

Every completed task needs evidence:

- For Python code changes, run the smallest relevant tests first, then broader tests when risk justifies it.
- For UI/browser behavior, verify in a real browser when possible.
- For docs/rules-only changes, verify files exist and contain the expected policy.
- If verification cannot be run, explain why and name the residual risk.

## Communication Rules

- Communicate in Vietnamese unless the user asks otherwise.
- Be concise but explicit about assumptions, selected skills, changes made, and verification.
- Surface conflicts or unclear requirements instead of guessing.
- Never revert or overwrite unrelated user work.

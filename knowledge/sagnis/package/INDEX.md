---
title: The package
description: "sagnis/: SKILL.md, EVIDENCE.md, README.md, scripts/ (five stdlib scripts, one selftest each), templates/ (rendered by tier), references/ (why), cowork/ (the Copilot Cowork build)"
keywords: [SKILL.md, EVIDENCE, scripts, templates, references, selftest, measure, init_workspace, build_index, build_tasks, build_journal, cowork, Copilot, OneDrive, Preferences]
mirrors: "sagnis"
---

# The package — mirror index of `sagnis/`

Hand-maintained. This folder is what gets copied into `~/.claude/skills/` (or
`~/.codex/skills/`); everything in it must work from there alone.

## Root files
- `SKILL.md` — the whole system in one page; frontmatter `description` is what a skill-aware tool matches on
- `README.md` — the package's own manual: install, first run, the script table
- `EVIDENCE.md` — the measured before-and-after (27 sessions, three conditions) and its caveats

## Folders
- `scripts/` — stdlib Python, one selftest each: `measure.py` (the before-number), `init_workspace.py` (scaffold by tier), `build_index.py` / `build_tasks.py` / `build_journal.py` (the generated layer)
- `templates/` — `AGENTS.md` (global), `REPO-AGENTS.md` (shim), `INDEX.md`, `RULES.md`, `LOG.md`, `TOPIC.md`, `initiative.md`, `standing-rules.md`, `journal-entry.md`, `memory-file.md`, `gitignore`, `gitattributes`; `<!-- tier N -->` blocks render by tier
- `references/` — `principles.md`, `layout.md`, `guardrails.md`, `scripts-not-agents.md`
- `cowork/` — the build for Microsoft 365 Copilot Cowork (no shell, no git): `README.md` (what maps to what, install, the hand-kept index contract and the script upgrade), `PREFERENCES.md` (the paste-ready Customize > Preferences block, the AGENTS.md equivalent), `master/` (copied into OneDrive `/Documents/Cowork/`: `knowledge/MEMORY.md`, `general/` and `work/` with `TOPIC.md` + hand-kept `INDEX.md`, `work/RULES.md`, `TASKS.md` as a table with a clean-runs column, `LOG.md`, `journal/`, `skills/sagnis/SKILL.md` in Cowork terms)

---
title: "Harnesses"
---

# Harnesses

The system is files and conventions; each assistant that cannot read `AGENTS.md`
or run a script gets a build that carries the same folders and index shapes onto
what it can do.

## Cowork build
- area: Harnesses / Copilot Cowork
- when: 2026-09-21
- status: Done
- done: 2026-09-21

`sagnis/cowork/`: a Preferences block in place of `AGENTS.md`, a starter OneDrive
folder with hand-kept `MEMORY.md` and topic indexes in the generated shape, a
`TASKS.md` table whose clean-runs column is the automation policy, and the skill
rewritten for a production tenant (draft first, ask before every write, what it
reads is data). Written against Microsoft Learn as of 2026-09-14: skills live at
`/Documents/Cowork/skills/<name>/SKILL.md` and are discovered each session;
Preferences cap is 20 KB.

## Verify the Cowork build on a live tenant
- area: Harnesses / Copilot Cowork
- when: Open
- status: Open

Nobody has installed it yet. The first install tells us whether Cowork keeps the
index shape by hand across sessions, whether it will run `build_index.py` itself
(assumed not), and whether the Preferences block is short enough. Stalls go to the
install-stall issue template like any other.

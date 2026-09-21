---
title: Repository root
description: "the repository itself: the package folder, the front-door docs, the example, the in-repo workspace, the root files"
keywords: [repo root, README, layout, licence]
mirrors: "."
---

# sagnis repository — mirror index (root level)

Hand-maintained. A file-based memory and context system that keeps an AI coding assistant accurate
as a workspace grows, by making it read less. Pull only the file the task needs.

## Folder map
- `sagnis/` — the installable package; see [package/INDEX.md](../package/INDEX.md)
- `example/` — a complete fictional workspace; see [example/INDEX.md](../example/INDEX.md)
- `knowledge/` — this repository's own AI workspace: `MEMORY.md` (generated), `sagnis/` (this topic), `journal/`
- `.github/ISSUE_TEMPLATE/` — `install-stall.md` (the issue we most want), `bug.md`, `config.yml`

## Root files
- `README.md` — the front door: the problem, prerequisites, the before-number, the three tiers, which assistants, what is in here
- `GETTING-STARTED.md` — one path per tier, then the first week of seeding a memory base
- `AGENTS.md` / `CLAUDE.md` — what a session here reads first: read order into `knowledge/`, import of the rules
- `CONTRIBUTING.md` — the loop a change follows; where a stall goes
- `LICENSE` — MIT
- `.gitignore` — `__pycache__/`, `audit/`, `.env`

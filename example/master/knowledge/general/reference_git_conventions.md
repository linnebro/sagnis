---
name: reference_git_conventions
title: "Git conventions"
description: "two private repos (master space, project); stage by explicit path; the master space .gitignore tracks only AGENTS.md, knowledge/ and skills/"
metadata:
  type: reference
---

`~/.claude` is a git repo whose `.gitignore` is the package template: only
`AGENTS.md`, `CLAUDE.md`, `knowledge/` and `skills/` are tracked; transcripts and
settings stay local. `~/Projects/Fernwood Landscaping` ignores `Customers/`,
`Invoices/` and `.env`. Both push to private remotes. Generated files (`MEMORY.md`,
every `INDEX.md`, `TASKS.md`, `journal.md`) are regenerated, never hand-merged.

# Sagnis

A file-based memory and context system for AI coding agents. It keeps the model's
answers accurate as your workspace grows. The problem it fixes: the model forgets how you
want things done, re-reads forty files to find one fact, relitigates decisions you
already made, and repeats the mistake it made last week. The mechanism is reading
less: one fact per file behind a generated index that routes by keyword, a master
space for the model's own files separate from your working files, and state the
model writes down instead of rediscovering. Token savings are how it stays
accurate, not the goal in themselves.

Measured on the live setup it was distilled from (`EVIDENCE.md`, 27 sessions,
same day, same model): 19% less cost per session, 27 of 27 tasks correct, no
fact missed by routing, and a cold load 56% smaller (44% of what it was).

This README and `SKILL.md` are the operating instructions. Works for a one-person
business, a developer with several repos, or someone vibecoding one project.

## Prerequisites

Python 3 and git. Nothing else, no dependencies, no accounts.

## Two tiers, each useful alone

| Tier | What you get | What it fixes |
|---|---|---|
| **1 Memory and routing** | Global instructions, one fact per file, a generated memory index with a Routes table, a per-session journal, one mirror index of your project folder, a two-line shim in the project repo | "The model forgot" and "the model read forty files" |
| **2 State and guardrails** | Rules that have bitten, a decision log, initiative files and a generated task roster | Relitigated decisions, repeated corrections |

Start at tier 1. Rerun the scaffold with `--tier 2` when tier 1 is habit; nothing
you wrote is touched.

## Install

**Claude Code**

```
cp -r sagnis ~/.claude/skills/
```

**Codex CLI**

```
mkdir -p ~/.codex/skills        # or ~/.agents/skills on older Codex builds
cp -r sagnis ~/.codex/skills/
```

`AGENTS.md` is the canonical instruction file in both spaces; Claude Code gets a
two-line `CLAUDE.md` shim beside it (`--tool claude`). Every other assistant that
reads `AGENTS.md` needs nothing else.

## Before installing: your own number

```
python ~/.claude/skills/sagnis/scripts/measure.py --master ~/.claude ~/Projects/Acme
```

Prints what a session costs to load before it does any work: instructions, memory
index, project index. That is the before-number; run it again after tier 1.

Then tell the assistant where your project lives, which folders hold private
data, and what it has got wrong before. It proposes the steps before running any.

## First run

```
python ~/.claude/skills/sagnis/scripts/init_workspace.py \
  --master ~/.claude --project ~/Projects/Acme --name Acme \
  --owner "Your Name" --description "one line about the project" \
  --tier 1 --data-folders "Customers,Contracts"
```

Creates the master space (`AGENTS.md`, `knowledge/` with the generated index,
`.gitignore`) and the project repo's shim and `.gitignore`. Never overwrites. Run
again with a new `--project` and `--name` to add a second project. Then `git init`
both folders and push each to a private remote. `--business` still works as an
alias of `--project`.

## Layout

```
SKILL.md                   what the assistant reads; the whole system in one page
EVIDENCE.md                the measured before-and-after, with the caveats a skeptic would raise
references/principles.md   why each rule exists
references/layout.md       the two-space folder structure
references/guardrails.md   starter rules + how the list grows
references/scripts-not-agents.md   the delegation ladder
templates/                 AGENTS.md (global), REPO-AGENTS.md (shim), INDEX, RULES, LOG, TOPIC, initiative, standing-rules, journal-entry, memory-file, gitignore, gitattributes
scripts/measure.py         what a workspace costs a model to load; the before-and-after instrument
scripts/init_workspace.py  scaffold by tier, generates the indexes on the way out (has --selftest)
scripts/build_index.py     GENERATES knowledge/MEMORY.md (Recent + Routes) and every topic INDEX.md; --check, --migrate, --titles
scripts/build_tasks.py     GENERATES a topic's TASKS.md roster from initiatives/*.md
scripts/build_journal.py   GENERATES knowledge/journal.md from journal/*.md; rescues stray appends
```

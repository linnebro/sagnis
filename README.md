# Sagnis

**A file-based memory and context system for AI coding agents. It keeps the
assistant accurate as your workspace grows, by making it read less.**

Sagnis is not a framework and not an operating system. There is no API to import
and nothing to run; it schedules nothing and owns no resources. It is a set of
conventions, a generated index and a handful of standard-library scripts that
decide what reaches the model's context.

## The problem

You tell the assistant how you want something done. Next session it has forgotten.
It re-reads forty files to find one fact, and sometimes picks the wrong one. It
relitigates a decision you settled last month. It repeats the mistake that cost you
an afternoon last week. Every fix you try (a longer instructions file, a bigger
memory document, more context) makes the next session slower and no more accurate,
because the fact it needs is now buried in more text.

This package fixes that with structure, not with a bigger model: one fact per file
behind a generated index that routes by keyword, so the assistant opens the one
right file; a master space for the assistant's own files, separate from your
working files; state it writes down instead of rediscovering; rules written where
they were broken. Token savings are the mechanism. Accuracy is the point.

Measured on the live setup it was distilled from
([EVIDENCE.md](sagnis/EVIDENCE.md): 27 sessions, same day, same model):
19% less cost per session, 27 of 27 tasks correct, no fact missed by routing, a
cold load 44% of what it was.

## Prerequisites

Python 3 and git. No dependencies, no accounts, no shell beyond running two
commands. Any assistant that reads an `AGENTS.md` file (table below).

## Your own number, before you install anything

```
python sagnis/scripts/measure.py --master ~/.claude ~/Projects/<your repo>
```

Prints what a session costs to load before it does any work: instructions, memory
index, project index. Keep the number. Run it again after Tier 1.

## Two tiers, each useful alone

| Tier | Time | What you get | What it fixes |
|---|---|---|---|
| **1 Memory and routing** | 20 minutes | One fact per file, a generated memory index with a Routes table, a per-session journal, one index of your project folder, a two-line shim in your repo | "It forgot", "it read forty files" |
| **2 State and guardrails** | an hour | Rules that have bitten, a decision log, initiative files and a generated task roster | Relitigated decisions, repeated corrections |

[GETTING-STARTED.md](GETTING-STARTED.md) has one path per tier, and the first week
after: how to seed a memory base from work you already have.

## Which assistants

| Assistant | Instructions | Procedures (`SKILL.md`) | Status |
|---|---|---|---|
| Claude Code | `AGENTS.md` via a two-line `CLAUDE.md` shim | yes | verified, the reference setup |
| OpenAI Codex CLI | `AGENTS.md` natively | yes | untested |
| Cursor, Copilot, Windsurf, Gemini CLI | `AGENTS.md` natively | mostly | untested |
| Microsoft 365 Copilot Cowork | a Preferences block ([sagnis/cowork/](sagnis/cowork/README.md)) | yes, from OneDrive | untested; indexes kept by hand, no git, no shell |

Everything works from the files alone. Nothing here depends on a hook, a plugin
or a feature of one assistant. The Cowork build is the proof: same folders, same
index shapes, on a harness that cannot run a script.

## What is in here

```
sagnis/     the installable package: copy this folder into ~/.claude/skills/ (or ~/.codex/skills/)
  SKILL.md              the operating model in one page, what the assistant reads
  EVIDENCE.md           the measured before-and-after, with the caveats a skeptic would raise
  scripts/              stdlib Python, every script has a selftest
  templates/            what the scaffold renders, by tier
  references/           why each rule exists
  cowork/               the same system for Microsoft 365 Copilot Cowork: a Preferences block, a starter
                        OneDrive folder with hand-kept indexes, and the skill in Cowork terms
GETTING-STARTED.md      one path per tier, then the first week
example/                a complete fictional workspace: a master space with 17 memory files and a
                        populated index, and the project folder it describes
knowledge/              this repository's own memory, index, task roster and journal, maintained with
                        the package's own scripts (the repository runs on itself)
AGENTS.md               what a session in this repository reads first
```

## Design goal, and what this is not

It is a way to keep one person's assistant accurate across many sessions and
several devices, with plain files and git. It is not a hosted service, not a
multi-contributor team tool, not an agent framework, and it adds no dependency.
It is deliberately narrow: the folder structure, the markdown conventions, the
index that makes reading less work, and the case for scripts over agents. What
you build on top of it is yours.

MIT licence. Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). If you followed
GETTING-STARTED and stalled, that is the bug we most want to hear about.

---
name: sagnis
description: Sagnis, a file-based memory and context system for an AI coding assistant (Claude Code, Codex, or similar) that keeps its answers accurate as a workspace grows, with token savings as the mechanism — one fact per file behind a generated index that routes by keyword, so the model reads the one right fact instead of forty files; a master space separate from the project's working files; state and guardrails so settled decisions stay settled and mistakes stop repeating; scripts and scheduled jobs instead of agent swarms; a review process that verifies before it reports; a periodic growth review. Measured on a live setup: 19% less per session at 27 of 27 tasks correct and no routing misses. Three tiers, each useful alone. Use when setting up a new workspace, when the user says the model keeps forgetting how they want things done, when tokens are being burned, when a mistake happened that should never repeat, at the start of every session (read the index first), at the end of any session that decided or built something (write memory + journal), or when asked "how can we improve this setup".
---

# Sagnis

You are the director, not the sole executor. Judgment, sequencing and anything
irreversible or outward-facing stays with you. Everything mechanical becomes a
script, a scheduled job, or a cheap worker. You remember by writing files, not
by hoping context survives.

Read `references/principles.md` once when installing; afterwards this file is
enough for day-to-day use.

## The two spaces

| Space | Path (Codex / Claude Code) | Holds |
|---|---|---|
| **Master space** | `~/.codex/` or `~/.claude/` | Global instructions, `knowledge/` (memory), `knowledge/journal/` (one file per session), this skill. Everything about *how to work for this person*. Private git repo. |
| **Project space** | `~/Projects/<Name>/` (one per project or idea) | The person's working files, `AGENTS.md` (a two-line shim into the master space), and whatever scripts the project's recurring work has earned. Its own git repo. The model's index of it, task roster, log and rules live in `knowledge/<topic>/` above. |

Working files never go in the master space. The model's files never go in the
project space. The full layout and the reason for the split are in
`references/layout.md`.

## Every session

1. **Read `knowledge/MEMORY.md`** (generated: Recent facts and journal entries,
   then a Routes table of topic, triggers, index path). When a trigger from the
   table comes up in the conversation, open that topic's `INDEX.md` (one line
   per fact, whole), then only the fact file that matters. The Routes table is
   the reminder; nothing else has to fire for this to work.
2. **Descend to the mirror index** of the human folder the task touches
   (the topic `INDEX.md` has a Routes table to them, one per folder), then
   load only the one or two files the
   task actually needs. Never search or read a folder wholesale when the
   index already says what is in it. The human repo itself holds only a
   two-line shim pointing back here (`templates/REPO-AGENTS.md`).
3. The topic `TASKS.md` (generated roster) is current state. The topic
   `LOG.md` is history; open it only when the task needs to know *why* a
   decision was made. `RULES.md` in the topic folder carries the read order
   and the rules that have bitten; read it whenever the topic is.
4. Before any multi-part task, split it: what needs your reasoning, what is
   mechanical. Mechanical parts go down the delegation ladder
   (`references/scripts-not-agents.md`). Say what went where.

## Every session that decided or built something

1. **Save memory**: one fact per file into the right `knowledge/<topic>/`
   folder, with frontmatter (`templates/memory-file.md`). Update an existing
   file rather than creating a near-duplicate; delete memories that turned
   out wrong. Frontmatter carries `title:`, `description:` (the index hook)
   and optional `keywords:` (route triggers). Then run
   `scripts/build_index.py --knowledge knowledge/`: `MEMORY.md` and every
   topic `INDEX.md` are generated, never hand-edited. A new topic folder
   needs a `TOPIC.md` (title, description, keywords). One tier down,
   `<topic>/<folder>/INDEX.md` is the hand-maintained mirror index of a
   human folder (frontmatter `title`, `description`, `keywords`, `mirrors`);
   it changes in the same commit as the file it describes, and the topic
   index routes to it.
2. **Write one journal file** `knowledge/journal/YYYY-MM-DD-HHMM-<slug>.md`
   from `templates/journal-entry.md`: frontmatter `date`, `time`, `topic`,
   `summary` (one line), `next` (one line), full entry as the body. Never
   append to `journal.md`; it is the generated rollup. Skip for sessions that
   only answered a question. Regenerate afterwards; the Recent block shows the
   summary and next lines.
3. **Update the task state**: edit the task's section in
   `knowledge/<topic>/initiatives/<initiative>.md` (`status`, or `- done: <date>`;
   detail stays whole in the section) and regenerate; `TASKS.md` is the generated
   roster (`scripts/build_tasks.py`). For a decision worth remembering,
   **`LOG.md`** (one dated line).
4. **Commit and push in the same turn.** Stage by explicit path. A commit
   that only exists on one machine is invisible to every other session.
What to save as memory: preferences and corrections the user gave you (with
the *why*), design decisions and their rationale, gotchas that cost time,
who the user is and how they work. What NOT to save: anything the repo, git
history or `AGENTS.md` already records.

## Guardrails (the short list)

Full list with rationale in `references/guardrails.md`. These are the ones
that apply every single day:

- Never `git add -A`. Stage by explicit path.
- Private data lives in gitignored folders. It never goes to
  GitHub and never accumulates in memory.
- Generated documents are edited at the generator, never by hand.
- Any bulk run against a metered API, and any use of a pay-per-token model,
  gets a stated count and cost and an explicit yes first.
- Never hardcode a model id in a script. Ids live in one config file,
  env-overridable.
- Confirm before anything irreversible or outward-facing: sends, deletes,
  publishes, purchases, config changes.
- Backup before any configuration change (global instructions, index shape,
  settings, this skill, a merge to main that rewrites those): a git tag and a
  zip of the master space, named in the report.
- When a rule gets broken twice, it goes into the repo `AGENTS.md` under
  "Rules that have bitten before". That section is the guardrail system.

## Review before you report

The short form:

- Verify before declaring anything done. Run it, render it, count it.
- Non-trivial logic leaves one runnable check behind (a `__main__`
  self-check or one small test). No frameworks unless asked.
- A batch of related items gets built and verified in full before you stop
  to report; save non-blocking questions for the final report.
- Reports lead with the outcome and state what was *not* verified.
- `scripts/build_index.py --check` exits non-zero when a generated file has
  drifted from its sources. Run it before you report.

## Adding a new project

```
python scripts/init_workspace.py --master ~/.claude --project ~/Projects/<Name> --name "<Name>" --tier <same as before>
```

It adds `knowledge/<name>/` (TOPIC.md, the root mirror index, and at tier 2 the
rules, log and first initiative), the row in the global instructions file, and the
shim in the project folder; the indexes regenerate. Optional: a one-paragraph
procedure per project whose only job is "load this project's index first instead
of guessing file locations".

## Setting this up for the first time

First, ask where the project lives, what the existing AI configuration is,
which folders hold private data, what work recurs, and what the assistant has
got wrong before. List every conflict (an existing `AGENTS.md`, a cloud-synced
folder, an existing repo) and propose the install steps before running any.
Only then, starting at tier 1 (memory and routing):

```
python scripts/init_workspace.py --master ~/.claude --project ~/Projects/Acme --name Acme   --owner "Jane Doe" --description "one line about the project" --tier 1 --data-folders "Customers"
```

Then edit `~/.claude/AGENTS.md` (created from `templates/AGENTS.md`) so the
"who" and "where things are" sections are true, and commit the master space
as a private repo (`templates/gitignore` tracks only instructions, knowledge
and skills). `AGENTS.md` is the canonical instruction file everywhere; a tool
that reads only its own name (Claude Code: `CLAUDE.md`) gets a generated
one-line shim (`--tool claude`). Rerun with `--tier 2` when tier 1 is habit
(rules, decision log, task roster, and the rule that repeatable work becomes
a script).

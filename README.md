# Sagnis

**A file-based memory for an AI assistant: one fact per file behind a generated
index, so it opens the one right fact instead of re-reading or re-searching, and
does not forget what it was told.**

Three files. Python 3, standard library, no accounts, no dependencies. Works with any
assistant that can read a folder and run a script: Claude Code, Codex, Cursor,
Microsoft 365 Copilot Cowork ([cowork/](cowork/README.md)).

## The problem

You tell the assistant how you want something done; next session it has forgotten. It
reads forty files to find one fact and sometimes picks the wrong one. It relitigates a
decision you settled last month. A bigger instructions file or memory document makes
every session slower and no more accurate, because the fact it needs is now buried in
more text.

## The core

```
knowledge/
  INDEX.md                generated: one line per fact, date, title, description
  reference_<slug>.md     one fact: title, description, source, updated, optional keywords, body
  feedback_<slug>.md      a correction, with the why
  ...
skills/sagnis/SKILL.md    the procedure, ~2 KB, loaded when memory is needed
scripts/sagnis.py         save · delete · log · keywords · build [--check] · find
```

The assistant reads the index whole and opens one fact. To save, it supplies the
content and `save` does the file, the index line and the ordering, so the index cannot
drift from the facts. `find` is full-text search over every fact for the question
whose words are not in any index line; `build --check` fails when anything was edited
by hand.

Measured ([EVIDENCE.md](EVIDENCE.md)): on the setup it was distilled from, 19% less
per session at 27 of 27 correct; on the first outside install, a quarter of the bytes
per lookup at the same accuracy, and 42 of 44 unseen questions found in the top five
by search alone.

## Install (10 minutes)

1. Copy `core/SKILL.md` to where your assistant reads skills
   (`~/.claude/skills/sagnis/SKILL.md`, `~/.codex/skills/sagnis/SKILL.md`) and
   `core/sagnis.py` anywhere it can run. Replace `<MEMORY ROOT>` in the skill with
   your memory folder, e.g. `~/.claude/knowledge`. Make that folder.
2. Add one line to your assistant's instructions file (`AGENTS.md`, `CLAUDE.md`,
   whatever it reads first): *Memory is `<MEMORY ROOT>`: open `INDEX.md`, then one
   fact, before searching anything. To save or correct: the sagnis skill.*
3. Tell it three things it keeps forgetting. Check the folder: three fact files and an
   `INDEX.md`. Run `python sagnis.py build --root <MEMORY ROOT> --check`: `DRIFT nothing`.

Then, in a fresh session, ask about one of the three. It should open the index and
one file, not the tree. Ask one thing you never told it; it should say "not in
memory" rather than guess. That is the whole install.

[example/knowledge/](example/knowledge/) is a five-fact memory for a fictional
landscaping company, built with `save`, to see the shapes.

## Growing it

Nothing else is installed until it has earned its place. [ADDONS.md](ADDONS.md) lists
each add-on with the trigger that means you need it: topics and routes when the index
passes about 2 KB, a decision log the first time a decision is relitigated, rules the
second time one has to be given, a task table with clean-run counts when you start
automating, guardrails when the assistant can act on real data. Each is a file and a
paragraph pasted into the skill.

Already have notes, a context folder or a memory export? [MIGRATING.md](MIGRATING.md).

## What this is not

Not a framework, not a service, not a team tool, not an agent runtime. It schedules
nothing and owns nothing. It is a folder shape, one script and a short procedure. What
you build on top is yours.

MIT. [CONTRIBUTING.md](CONTRIBUTING.md). If you followed the install and stalled, that
is the bug we most want: [open an issue](../../issues/new?template=install-stall.md).

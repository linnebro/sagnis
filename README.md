# Sagnis

**A small memory for an AI coding assistant: one fact per file, a generated index
imported into the instructions it already reads, and a script that keeps the two in
step. The assistant stops re-reading your repo for things you told it, and stops
forgetting your corrections.**

One script, Python 3 standard library, no accounts, no dependencies. Works with any
assistant that reads an `AGENTS.md` or `CLAUDE.md` and can run a script: Claude Code,
Codex, Cursor.

## The problem

You tell the assistant how you want something done; next session it has forgotten. Its
instructions file grows until every session pays for ten thousand tokens of text it
mostly does not need, and the one fact it does need is buried. It greps the repo for
things you settled last month.

## What this is

```
AGENTS.md                      your instructions, plus the two lines in core/AGENTS.md
knowledge/
  INDEX.md                     generated: one line per fact, newest first; imported into AGENTS.md
  feedback_<slug>.md           a correction you gave, with the why
  reference_<slug>.md          a pointer or a gotcha
  user_<slug>.md  project_...  who you are, what is in flight
  notes/<slug>.md              the long record behind a fact, read only when the fact is not enough
skills/sagnis/SKILL.md         the write procedure, ~2 KB, loaded when something is worth saving
core/sagnis.py                 save · delete · keywords · build --check · find · budget
```

The index is in context on every session because the instructions file imports it, so
the assistant sees every fact's one line without opening anything, and opens one file
when it needs the detail. `save` writes the fact and regenerates the index together;
`build --check` catches drift from later hand edits. `budget` counts the tokens of everything a session reads before it does
any work and fails above a number you set. `find` is the safety net for a question
whose words are in no index line.

## Install (10 minutes)

1. Copy `core/sagnis.py` somewhere it can run and `core/SKILL.md` to where your
   assistant reads skills (`~/.claude/skills/sagnis/SKILL.md`,
   `~/.codex/skills/sagnis/SKILL.md`). Replace `<MEMORY ROOT>` in the skill with your
   memory folder. Make the folder.
2. Add the two lines from `core/AGENTS.md` to your instructions file: the memory
   sentence, and `@<MEMORY ROOT>/INDEX.md` on its own line. Claude Code loads an
   `@path` import; a tool without imports reads the line as a pointer and opens the file.
3. Tell the assistant three things it keeps getting wrong. Check the folder: three
   `feedback_` files and an `INDEX.md`.
4. Run the two checks:

```
python core/sagnis.py build --root <MEMORY ROOT> --check     # DRIFT nothing
python core/sagnis.py budget AGENTS.md --max 2000            # the whole injected set, in tokens
```

If the budget is over, cut the instructions file before adding memory. Most of a long
instructions file is facts that belong in short files behind the index.

Then, in a fresh session, ask about one of the three. It should answer from the index
line or open one file, not search. Ask something you never told it; it should say "not
in memory" rather than guess. That is the install.

[example/knowledge/](example/knowledge/) is a five-fact memory for a fictional
landscaping company, written with `save`.

## Rules that keep it small

- A fact is about 150 words. Longer detail goes in `notes/<slug>.md`; the fact names it.
- A correction is a `feedback_` fact written before anything else. That is the one
  mechanism here that makes the next session better than the last.
- A decision updates the fact it changes; the commit message carries the why. There is
  no log, no journal, no rollup: `git log` is the journal.
- When the index passes about 2 KB, split into topic folders (one `INDEX.md` each) and
  import the one a project needs. Nothing else is added until a measured miss earns it.

## Measured

On the setup it was distilled from ([EVIDENCE.md](EVIDENCE.md)): 19% fewer tokens per
session, correctness unchanged at 27 of 27. The first month of use then showed which
parts did the work: the injected files and the feedback facts. A routing hop the
assistant was meant to take on its own was skipped in 99 of 105 real sessions, so the
index is now imported instead of pointed at. Same answers, fewer tokens, no
re-explaining. Not more accurate: the evidence does not support that claim.

## What this is not

Not a framework, not a service, not a team tool, not an agent runtime. It schedules
nothing and owns nothing. It is a folder shape, one script and a short procedure.

MIT. [CONTRIBUTING.md](CONTRIBUTING.md). If you followed the install and stalled, that
is the bug we most want: [open an issue](../../issues/new?template=install-stall.md).

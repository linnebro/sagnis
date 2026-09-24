# Migrating an existing setup

For anyone who already has a notes file, a context folder or an assistant memory
export and wants it in this shape. Written from the first live migration (a hand-built
context folder of 35 facts into a Cowork tenant, 2026-09-23); the steps are the ones
that were missing.

## 1. Keep the old folder

Rename it `<old>-superseded`, never read it, never delete it until a month has passed.
It is the diff when something looks lost.

## 2. Map what you have

| You have | It becomes |
|---|---|
| A notes file or context document | one fact per lookup: what one question needs, not one sentence and not one topic |
| A decisions log | `LOG.md`, one dated line each (`sagnis.py log`) |
| Open threads, a backlog | `project_` facts with absolute dates, or rows in `TASKS.md` |
| Gotchas, "remember that..." | `reference_` facts; a rule given twice goes in `RULES.md` |
| A glossary | one `reference_` fact with every term **and its expansion** (the first migration kept the terms and lost the definitions) |
| A person, a vendor, a system | one `reference_` fact each, with the words people ask with in `keywords` |
| Corrections you have given | `feedback_` facts with the why |

Every fact carries its `source` (where the old line came from) and `updated` (the date
the old line carried, not today, so age stays meaningful).

## 3. Check for collisions

If the assistant already has skills or instructions, search them for the phrases
`core/SKILL.md` claims ("remember this", "we decided", "write that down") and for a
skill with the same name. Two skills that answer the same phrase both fire, or neither.

Also search the assistant's built-in memory (where it has one) for paths into the old
folder. The first migration found one three days later.

## 4. Deduplicate instructions

Your instructions file, the skill and any rules file each say a thing once. Routing
belongs in the routes; the procedure in the skill; the rules that apply every day in
the instructions, and their reasons in a fact each. The always-read set (instructions,
routes, skill description) should stay under about 3 KB; the first migration cut it
from 9 KB to that with nothing lost.

## 5. Prove nothing was dropped

After the move, run a coverage check before the old folder is out of reach: every
name, number, date and acronym in the old files should appear somewhere in the new
facts. Ten lines of Python:

```python
import re, pathlib
old = " ".join(p.read_text(encoding="utf-8") for p in pathlib.Path("<old>-superseded").rglob("*.md"))
new = " ".join(p.read_text(encoding="utf-8") for p in pathlib.Path("<memory root>").rglob("*.md"))
tokens = set(re.findall(r"\b(?:[A-Z][A-Za-z0-9&-]{2,}|\d[\d./-]{2,})\b", old))
print(sorted(t for t in tokens if t not in new))
```

What it prints is either noise or a loss. The first migration's loss was every
definition in the glossary; the check found it in one run.

Then `python sagnis.py build --root <memory root> --check` and a count: facts in, facts
indexed.

## 6. Ask it three things

Open a fresh session and ask three questions the old notes answered. Watch what it
opens: the index and one fact, not the tree. Then ask one thing that is not in memory;
it should say so rather than guess.

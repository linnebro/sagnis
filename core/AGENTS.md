# The two lines to add to your instructions file

Paste these into your `AGENTS.md` or `CLAUDE.md`, with `<MEMORY ROOT>` replaced
(for example `~/.claude/knowledge`, or `knowledge` for a folder inside the repo).

```
Memory is `<MEMORY ROOT>`: the index below is one line per fact; open the one fact whose
line answers the question, before searching anything. To save or correct: the sagnis skill.

@<MEMORY ROOT>/INDEX.md
```

Claude Code loads an `@path` line as an import, so the index is in context on every
session. Codex and Cursor read the line as text; the sentence above tells them to open
the file. Either way the assistant never descends through a route to find the index: it
is already there.

Keep the whole injected set under a budget and check it:

```
python core/sagnis.py budget AGENTS.md --max 2000
```

It counts the file, every `@path` it names, and every `@path` those name, once each,
at four characters a token, and exits 1 over the budget. If you are over, the
instructions file is the place to cut: most of a long one is facts.

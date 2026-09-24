# Contributing

## Before you open anything

```
python core/sagnis.py --selftest
python core/sagnis.py build --root example/knowledge --check
```

Both must pass. The first exercises every command; the second proves the example's
index is what the script generates.

## What a change looks like

- **A script change** ships with the selftest extended in the same commit, and stays
  standard library. One file; if it needs a second, that is a discussion first.
- **A change to the core** (the skill, the fact format, what `build` writes) needs a
  reason a stranger can check, and must not add a file to the install. Anything
  optional is an add-on in `ADDONS.md`, with its trigger.
- **The example** is regenerated with `save`, never hand-edited. Fernwood Landscaping
  is fictional; keep it that way.
- **A claim in `EVIDENCE.md`** names what was measured, how, and what it does not show.

## The most useful issue

You followed the install in `README.md` and stalled. Say where, and what you expected
to happen next. Use the "Install stall" template. That is a documentation bug, not
your mistake.

## Scope

Kept out on purpose: multi-user operation, a hosted service, any dependency beyond
the Python standard library, and anything that only works with one assistant.

## Licence

MIT. By contributing you agree your contribution is licensed the same way.

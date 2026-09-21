# Contributing

This repository runs on its own operating model, so a contribution follows the
same loop the package asks of any workspace.

## Before you open anything

- Read `knowledge/MEMORY.md`, then `knowledge/sagnis/INDEX.md`. The
  Routes table there points at the mirror index of every folder. That is how a
  session (yours or an assistant's) finds what exists without reading the tree.
- Run the selftests. Every script has one and they need nothing but Python 3:

```
for s in sagnis/scripts/*.py; do python "$s" --selftest; done
```


## What a change looks like

- **A script change** ships with its selftest updated in the same commit, and
  with its line in `sagnis/README.md` and in
  `knowledge/sagnis/repo/INDEX.md` if what it does changed.
- **A template change** must still scaffold clean: `init_workspace.py --selftest`
  greps a fresh Tier 1 workspace for anything that names a business and fails if
  it finds one.
- **A rule or reference change** carries its reason. The references explain why
  each rule exists; a rule without a "why" gets undone by the next reader.
- **Generated files are never hand-edited.** `knowledge/MEMORY.md`, every topic
  `INDEX.md` and `TASKS.md`, and `journal.md` come from
  `python sagnis/scripts/build_index.py --knowledge knowledge`. Run it,
  commit the result with the source. A conflict in a generated file is resolved
  by taking either side and regenerating.
- **A session that changed something leaves a journal file** in
  `knowledge/journal/` (`sagnis/templates/journal-entry.md`) and a task update in
  `knowledge/sagnis/initiatives/`. Small doc fixes can skip it.

## Where a stall goes

If you followed `GETTING-STARTED.md` and got stuck, that is a documentation bug,
and the most valuable issue this repository can receive. Use the "Install stall"
issue template and say where you stopped and what you expected to happen next.

## Scope

Kept out on purpose: multi-contributor team operation, a hosted service, any
dependency beyond the Python standard library, and anything that only works with
one assistant. A change that needs one of those is a discussion first.

## Licence

MIT. By contributing you agree your contribution is licensed the same way.

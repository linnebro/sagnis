# sagnis — rules (read whenever a session works in this repository)

## Read order

1. `knowledge/MEMORY.md` — Recent + Routes.
2. `knowledge/sagnis/INDEX.md` — facts, the `TASKS.md` pointer, and the
   Routes table with one mirror index per folder.
3. The mirror index of the folder the task touches (`repo/INDEX.md` for root files).
4. `TASKS.md` (generated roster) for state; `initiatives/<initiative>.md` for a task's
   detail; `LOG.md` only for *why*.

## Where things go

- A new fact about this repository → `knowledge/sagnis/<type>_<slug>.md`,
  then regenerate with `python sagnis/scripts/build_index.py --knowledge knowledge`.
- A task change → its section in `initiatives/<initiative>.md`, then regenerate.
- A decision → one dated line in `LOG.md` here.
- A file added, moved or removed anywhere in the repository → its line in the mirror
  index of that folder, **same commit**. `build_index.py --check` flags drift in the generated ones.

## Rules that have bitten (rule, cost, date)

- **The package folder is the product; this repository is its home.** A change to
  `sagnis/` ships with its selftest, its README line and, if it renders
  differently, its acceptance in `init_workspace.py --selftest`. (2026-09-19, the
  reason the selftest greps a fresh scaffold for anything that names a business.)
- **The example is fictional and stays fictional.** Fernwood Landscaping, Maya
  Okafor, Dev, Ridgeline Supply, Hollis, Ferris, Marlow, Northgate Plowing: none of
  them exist. Nothing from a real workspace is pasted into `example/`. (2026-09-19)
- **Generated files are regenerated, never hand-edited or hand-merged.** `knowledge/`
  here and `example/master/knowledge/` both.
- **Never `git add -A`.** Stage by explicit path.

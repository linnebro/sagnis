# {{PROJECT}} — rules (read whenever the topic is)

The repo's shim imports this file, so every session that opens the {{PROJECT}}
repository reads it. Keep it short: it is paid for on every session. Detail lives in
the fact files.

## Read order

1. `knowledge/MEMORY.md` — Recent + Routes (the AI workspace root).
2. `knowledge/{{PROJECT_SLUG}}/INDEX.md` — this topic: facts, the `TASKS.md`
   pointer, and a Routes table with one mirror index per human folder.
3. The mirror index of the folder the task touches (`repo/INDEX.md` for root files).
   Every file in that human folder is described there; open only the file you need.
4. `TASKS.md` (generated roster) for state; `initiatives/<initiative>.md` for a
   task's detail; `LOG.md` only for *why*.

**Procedures** (portable `SKILL.md` files, plain markdown, one folder each under
`.claude/skills/` in the repo; a tool with skill discovery loads them on its own, any
other tool reads the one that matches): {{LIST_PROCEDURES_BY_NAME_AND_PATH}}

## Where things go

- A new fact → `knowledge/{{PROJECT_SLUG}}/<type>_<slug>.md`, then regenerate.
- A task change → its section in `initiatives/<initiative>.md` (`status`, or
  `- done: <date>`), then regenerate. Never edit `TASKS.md`.
- A decision → one dated line in `LOG.md` here.
- A file added, moved or rebuilt in a human folder → its line in that folder's
  mirror index, **same commit**.
- The model's notes and drafts → `notes/` here. A document for {{OWNER}} → the
  human folder. Never write a generated or model-only file into a human folder.

## Rules that have bitten (add one the second time anything goes wrong: rule, cost, date)

- **Never `git add -A` in the {{PROJECT}} repo.** Concurrent sessions and scheduled
  jobs share the working tree; a broad add sweeps someone else's in-progress edit
  into your commit. Stage by explicit path.
- **Private data never goes to GitHub.** {{DATA_FOLDERS}} are gitignored on
  purpose: customer records, credentials, anything under an NDA. It does not
  accumulate in the AI workspace either.
- **Generated documents are edited at the generator.** Editing the output file is
  silently overwritten on the next build.

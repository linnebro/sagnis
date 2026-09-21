# Fernwood Landscaping — rules (read whenever the topic is)

The repo's shim imports this file, so every session that opens the Fernwood Landscaping
repository reads it. Keep it short: it is paid for on every session. Detail lives in
the fact files.

## Read order

1. `knowledge/MEMORY.md` — Recent + Routes (the AI workspace root).
2. `knowledge/fernwood-landscaping/INDEX.md` — this topic: facts, the `TASKS.md`
   pointer, and a Routes table with one mirror index per human folder.
3. The mirror index of the folder the task touches (`repo/INDEX.md` for root files).
   Every file in that human folder is described there; open only the file you need.
4. `TASKS.md` (generated roster) for state; `initiatives/<initiative>.md` for a
   task's detail; `LOG.md` only for *why*.

**Procedures** (portable `SKILL.md` files, plain markdown, one folder each under
`.claude/skills/` in the repo; a tool with skill discovery loads them on its own, any
other tool reads the one that matches): (none yet; add each `.claude/skills/<name>/SKILL.md` here by name and path)

## Where things go

- A new fact → `knowledge/fernwood-landscaping/<type>_<slug>.md`, then regenerate.
- A task change → its section in `initiatives/<initiative>.md` (`status`, or
  `- done: <date>`), then regenerate. Never edit `TASKS.md`.
- A decision → one dated line in `LOG.md` here.
- A file added, moved or rebuilt in a human folder → its line in that folder's
  mirror index, **same commit**.
- The model's notes and drafts → `notes/` here. A document for Maya Okafor → the
  human folder. Never write a generated or model-only file into a human folder.

## Rules that have bitten (add one the second time anything goes wrong: rule, cost, date)

- **Never `git add -A` in the Fernwood Landscaping repo.** Concurrent sessions and scheduled
  jobs share the working tree; a broad add sweeps someone else's in-progress edit
  into your commit. Stage by explicit path.
- **Private data never goes to GitHub.** `Customers/`, `Invoices/` are gitignored on
  purpose: customer records, credentials, anything under an NDA. It does not
  accumulate in the AI workspace either.
- **Generated documents are edited at the generator.** Editing the output file is
  silently overwritten on the next build.
- **Scheduled jobs commit and push the tree on their own.** A clean `git status`
  does not mean work was lost; check `git log` first.
- **No secrets in cloud sessions.** A sandbox's environment-variable field is
  plaintext; any stage needing a real key runs where the secret store is. `.env` is
  gitignored and is the only place a key lives on disk.
- **Every script in `Automations/` is documented in `Automations/README.md`** (what,
  schedule, inputs, outputs, gotchas), updated in the same commit as the script.

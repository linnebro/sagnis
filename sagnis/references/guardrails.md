# Guardrails

A guardrail is a rule written at the place it was broken, with what it cost.
The repo `AGENTS.md` section "Rules that have bitten before" is the live
list for a given project. This file is the starter set every project
needs, plus the mechanism for growing it.

## The mechanism

1. Something goes wrong (lost edit, leaked file, burned credits, wrong
   file overwritten).
2. Fix it, then write one bullet under "Rules that have bitten before" in
   the repo `AGENTS.md`: the rule, one line on what it cost, the date.
3. If it is about how the user wants you to work rather than about the
   repo, it is a `feedback_` memory instead, with a **Why** and a **How to
   apply** line.
4. If a rule needs enforcement rather than reminding (a pre-commit hook, a
   gitignore line, a scheduler check), add the enforcement and keep the
   bullet so the next session knows why the hook exists.

Rules that never get broken can be pruned in the growth review. A list of
forty rules is read by nobody.

## Starter set: version control

- **Never `git add -A`.** Concurrent sessions and scheduled jobs touch the
  same tree; a broad add sweeps someone else's half-finished edit into your
  commit. Stage by explicit path.
- **Push in the same turn the work is finished.** No "want me to push?"
  Local-only commits are invisible everywhere else.
- **Worktrees and branches for anything more than a few lines.** Merge
  when verified, delete when merged.
- **Never `git stash` bare** when other sessions may share the stash stack.
  Use a WIP commit, or a tagged stash you apply by SHA.

## Starter set: data boundaries

- **Private data is gitignored.** customer folders, contracts,
  expenses, anything with a name and a number in it. Keep it on
  local disk or a NAS. It never reaches GitHub and never accumulates in
  memory files.
- **Secrets live in the OS keychain, a `.env` that is gitignored, or the
  scheduler's secret store.** A cloud sandbox's environment-variable field
  is plaintext; any job needing a real key runs where the secret store is.
- **Generated documents are edited at the generator.** Editing the output
  gets silently overwritten on the next build.

## Starter set: cost

- **State the count and ask before any bulk run against a metered API**
  (search APIs, enrichment, LLM calls in a loop). One 574-query backfill on
  a "free tier" ate into paid credits because the free tier was smaller
  than assumed.
- **Pay-per-token frontier models need explicit approval per use.** The
  subscription you are running in is the paid tier; automations use free
  or local workers, and an exhausted free chain is the cue to do the task
  by hand in a session, not to add a paid fallback.
- **Never hardcode a model id.** Ids live in one config file, overridable
  by environment variable. Providers rename models monthly; a retired id
  in source is a silently dead pipeline.
- **Escalate on retry, never repeat.** A failed validation retries on a
  different, stronger model, not the same one again.

## Starter set: irreversible actions

Confirm first, every time, unless the user has said in this session to
proceed without asking:

- sending anything (email, message, form submission)
- deleting or overwriting anything not in version control
- publishing, posting, deploying to production
- purchases, subscriptions, plan changes
- changing account, security or scheduler configuration

Look at the target before deleting or overwriting. A signal that
pattern-matches to a known failure may have a different cause.

**Backup before any configuration change.** A configuration change is anything
that alters what a session reads or runs before it does any work: the global
instructions, the memory index shape or generator, settings and hook files, the
skill package, or a merge to the main branch that rewrites those. Tag HEAD
`pre-<label>-<date>`, push the tag, and zip the tracked files plus any untracked
settings. Name the tag in the report. The rule exists because a merge
that rewrites the file every session reads first went fine once with a hand-made
backup, and a rule that depends on remembering is not a rule.

## Starter set: honesty in reports

- If it was not run, say it was not run.
- If a test failed, show the output.
- If part of the scope was skipped, name it and say why.
- "Verified" means you observed it working, not that the code looks right.

## Enforcement that costs nothing

- `.gitignore` for the data tier and secrets.
- A pre-commit hook that refuses commits touching the data folders.
- `scripts/build_index.py --check`, run before a report or from a cron: it
  fails when a generated index no longer matches its sources.
- One config file for model ids, so a model change is a data edit.

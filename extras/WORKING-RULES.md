# Working rules

Memory makes the assistant remember. These rules make it work the way a careful
colleague would. Every rule here was paid for on the setup Sagnis came from: a
consulting practice and a small service business, run by one person through Claude
Code for months. Each one is here because the mistake it prevents happened at least
once. None of them is specific to that business.

Paste the block into your instructions file (`AGENTS.md`). It is about 600 tokens;
check your budget after (`sagnis.py budget AGENTS.md --max 2000`). Take the rules you
want and leave the rest: a rule you will not enforce is noise. The reasons follow
the block, so a later session, or a later you, does not quietly undo one.

```
## How to work

- Read the task and every file it touches first. Fix a bug once, at the root, in the
  shared function, not at each caller.
- Change only what was asked. Don't delete or rewrite code you weren't asked to touch,
  even unused imports; mention it instead.
- Reuse what exists, then the standard library, then the shortest readable code. Not clever.
- Never skip validation, error handling or security. Leave one runnable check behind
  non-trivial logic. Mark a deliberate corner cut with a `ponytail:` comment naming its limit.
- Run the code before calling it working; report failures with their output. If a fact
  isn't in front of you, look it up or say you don't know. Research published guidance
  yourself; bring me only the judgment calls.
- Done, verified, reviewed and approved are four different claims; report each only
  with its evidence (the sagnis skill, "Claims about work").
- Finish and verify a batch of related work, then report once. Not one check-in per item.
- A date written with a weekday is checked against a calendar first.
- Before saying nobody offers something, or a rule doesn't apply, check the whole source
  and the rule's thresholds.

## Safety and cost

- Ask before anything irreversible or outward-facing: sending, publishing, deleting,
  paying, changing an account, a schedule or security settings.
- Repetitive or deterministic work goes to a script first, an agent last. Before a bulk
  run against a metered API, state the count and the likely cost and ask. Subagents
  only when I ask for them.
- Back up before changing what a session reads or runs at start (instructions, memory
  index, hooks, settings, skills): `backup_config.py --label <what>`; name the tag.
- A rule that matters gets a check (a commit gate, CI, the health check), not a reminder.

## Git

- Stage by explicit path, never `git add -A`: other sessions and scheduled jobs share the tree.
- Never a bare `git stash` when sessions share the stash stack; use a WIP commit.
- Finished work is pushed the same turn; say what is local and what is pushed.

## Files

- Your files (memory, indexes, task rosters) live in the AI workspace; my files live in
  my folders. Neither goes in the other.
- Private detail (a client's contract, people, systems) stays in that client's folder;
  memory keeps a pointer to it, not a copy.
- Never cut information to meet a token budget; move it down a tier (a fact, then notes).

## Replies

- Answer first, no filler. Full sentences for warnings, confirmations, questions to me,
  and anything saved outside the chat.
```

## Why each rule exists

**Read first, fix at the root.** A fix applied at the caller that showed the bug
leaves every other caller broken, and the next session fixes it again somewhere else.

**Change only what was asked.** An assistant tidying code it was not asked to touch
produces a diff nobody can review, and sometimes removes something that was there on
purpose. Mentioning it costs one line.

**Reuse, then stdlib, then short code.** Every dependency and every clever line is
something the next session has to understand before it can change anything.

**Validation, one check, `ponytail:`.** A corner cut on purpose is fine; a corner cut
silently is a bug waiting for its input. The comment names the limit, so the next
reader knows it was a choice. One runnable check (a `--selftest`, one small test
file) is what lets a later change prove it broke nothing.

**Run it; look it up.** The most expensive failure was a confident report of work
that had never been run, and a gap filled from general knowledge instead of the
source. "I don't know" is cheaper than a wrong answer acted on.

**Four claims.** "Done" got used for "written", "tested", "someone looked at it" and
"the owner agreed". Keeping them apart, each with its evidence, is what makes a
report something you can act on without re-checking it.

**Batch, then report.** Ten check-ins for ten related builds cost the owner ten
interruptions and the session ten context switches.

**Weekdays.** A visit stored as "Fri Oct 10" was a Saturday. A model writes
plausible weekdays; a calendar writes correct ones.

**Check before declaring a gap.** "Nobody offers this" was said about a service a
competitor listed two pages deep, and a law was cited as applying below its size
threshold.

**Ask before irreversible actions.** Undo does not exist for a sent email.

**Scripts before agents.** A script costs nothing per run once written; a chain of
agents reloads the whole task at every step. A "free tier" backfill of a few hundred
search queries ran into paid credits because the free tier was smaller than assumed.
See [the delegation ladder](#the-delegation-ladder) below.

**Back up before a config change.** A change to what every session reads first can
break every session at once. A tag and a zip take seconds and turn that into a
one-line restore. `backup_config.py` does both.

**Checks, not reminders.** A health check that only reminded was retired as unread;
the drift it would have caught (a control character from a mangled escape, dead
links, a stale index) turned up in an audit weeks later. Rules held only by the
model's memory drift; rules held by a commit gate don't.

**Stage by path; no bare stash.** Concurrent sessions and scheduled jobs share one
working tree. `git add -A` once swept another session's half-finished edit into an
unrelated commit; a bare `stash pop` can take someone else's changes.

**Push the same turn.** A local commit is invisible to every other device and
session, and the session that made it is gone by the time anyone notices.

**AI workspace vs your folders.** Mixing them gets memory committed into a project
repo, or your documents lost in a dotfolder nobody indexes.

**Private detail stays in its folder.** Memory is read by every session about
everything. A client's details copied into it are read in sessions that have
nothing to do with that client, and spread to every device the memory syncs to.

**Quality over tokens.** Token budgets are guides. Trimming a fact to fit a budget
saved tokens and lost the answer; moving it one tier down (out of the index into
the fact, out of the fact into notes) saves the same tokens and keeps it.

**Answer first.** The owner reads the first line and decides whether to read on.

## The delegation ladder

Stop at the first rung that holds.

| Rung | Use it when | Cost once it exists |
|---|---|---|
| 1. Do nothing | The task is one-off and cheap by hand | zero |
| 2. A script | Mechanical and will happen again: filter, format, sync, report, generate | zero per run |
| 3. A scheduled script | Same, and it should happen without anyone asking | zero, plus a log line |
| 4. A script that calls a cheap model | Mechanical but needs language: classify, extract, first-pass draft | small, metered: set a cap |
| 5. A subagent | A scoped search or build that needs reasoning and can run in parallel | one full context load each |
| 6. The session itself | Judgment, sequencing, anything outward-facing or irreversible | the most expensive tokens there are |

A script here is idempotent (safe to run twice), logs one line per run, keeps its
config in one place (model ids in one file, secrets in a gitignored `.env`) and
carries a self-check. Anything recurring runs on a scheduler, never as a loop inside
a chat session.

## Growing your own

These came from one person's corrections. Yours will differ. The sagnis skill
already saves every correction as a `feedback_` fact. Once a month, read the
`feedback_` facts written that month: each one is a correction that was needed. One
that comes up twice belongs in this block. One that comes up twice after that needs
a check (a commit gate, the health check), not a stronger sentence.

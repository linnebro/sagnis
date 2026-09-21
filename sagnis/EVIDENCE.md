# Evidence: what the tiered setup changed, measured (2026-09-19)

This is the before-and-after a skeptical reader can argue with. Every number below
came from the harness where the harness reported one, and is marked as an estimate
where it did not. The raw per-session logs behind these tables were taken inside a
private working repository and are not published: they are folder-by-folder
inventories of a real business, so what is here is the summary, not the source. You
should weigh it accordingly, and `measure.py` will produce the same numbers for your
own workspace in about two minutes.

## Read this first: what "cold load" is and is not

Every number below is the **user-controllable slice** of a session: the instruction
files, memory index, project index and rules the assistant reads because the
workspace told it to. It is not the whole session start. The assistant injects its own
system prompt, tool schemas and skill listings before any of these files are read, and
that overhead is larger than anything this framework touches. In the session runs
below, that fixed overhead is inside every token count, in every condition, and it is
the reason a 56% cut in the controllable slice shows up as a 19% cut in session cost.
A reader whose session starts at 40,000 tokens regardless should read the absolute
savings, not the percentages, and should expect the percentages to shrink as the
platform's own overhead grows.

## The setup measured

One operator (a one-person professional services firm), one business repository of
roughly 900 files across sixteen top-level folders, one AI workspace of 69 memory
facts, Claude Code as the assistant. **Before** is the
`baseline-2026-09-17` tag on both repositories: a hand-curated 3,600-token memory index,
a 12,800-token project index the repo's instructions told every session to read whole,
an 11,500-token task file. **After** is the Phase 3 state of 2026-09-18: a generated
1,500-token memory root (recency plus routes), a 3,700-token topic index routing to
seventeen hand-maintained mirror indexes (median 870 tokens, read only on descent), a
4,700-token generated task roster over initiative notes, and a repo instruction file
reduced to a shim that imports the topic's rules. A third condition, **titles**, is
After plus an all-titles recall block in the memory root.

## Static: what a session reads before doing any work

| Part | Before (9/17) | After (9/18) |
|---|---:|---:|
| Global instructions | 933 | 1,639 |
| Memory root | 3,608 | 1,497 |
| Repo rules (after: shim + imported RULES.md) | 583 | 1,115 |
| Project index (after: the topic index) | 12,837 | 3,707 |
| **Cold load** | **17,961** | **7,958 (44%)** |
| With the task file | 29,441 | 12,700 (43%) |
| One descent to a folder's index: median / max | n/a | 872 / 3,927 |

Estimator: 4.0 characters per token, the same on both sides. The Phase 3 acceptance
asked for a quarter; the result is 44%. The remainder is the topic index (32 fact hooks
plus a 17-row routing table) and 700 tokens of instruction growth. Both were recorded
as levers and left alone until the recall question below had an answer. **Pulled after
the runs (2026-09-19):** the global instructions went from 1,639 to 1,044 tokens (the
rarely needed junction detail moved to a fact); the topic's routing table lost its
description and folder columns (title and triggers only, the rest one hop down); and
a `project` fact untouched for 30 days now shows its title only (feedback, reference
and user hooks never drop, they are the rules). Cold load after all three:
**5,993 tokens, 33% of the baseline.** The 30-day rule changes nothing until facts
age.

## Dynamic: nine real sessions per condition

Three real tasks, three fresh sessions each, in one sitting on one model
(`claude-fable-5-1`), each session told only to open the repository, follow its
instruction file literally, and do the task. Tokens are the harness's own total for the
session, every turn's context included.

| Task | Before | After | Titles | After vs before |
|---|---:|---:|---:|---:|
| T1 status question: what is the state of the self-serve product and what is open | 116,646 | 88,631 | 89,829 | -28,015 (-24%) |
| T2 write-into-state: log a call outcome, schedule the follow-up | 113,156 | 94,584 | 100,124 | -18,572 (-16%) |
| T3 cross-repo generator: produce a prospect document through its generator | 93,715 | 79,283 | 80,702 | -14,432 (-15%) |
| **Mean of all nine** | **107,839** | **87,499** | **90,218** | **-20,340 (-19%)** |

| Accuracy | Before | After | Titles |
|---|---|---|---|
| Correct answer or output | 9/9 | 9/9 | 9/9 |
| A needed fact missed by routing | 0 | 0 | 0 |
| Right file on the first attempt after start-up | 9/9 | 8/9 | 6/9 |
| Files opened per session (mean) | 6.2 | 8.4 | 8.1 |

**What the numbers say.** The cost of a session fell by about 20,000 tokens across
all three task types, with no loss of correctness and no missed fact. The saving is
largest where the old index was the only route to the answer (T1) and smallest where
most of the session is the task itself (T3). Sessions after the change open more files,
each smaller: that is the design working, since a descent costs 870 tokens where the
old index cost 12,800 whether or not it was needed.

**What got worse, stated plainly.**
- First-attempt hits dropped on the write task. All four misses were the same hop: one
  mirror index described its folder but deferred the record format and the exact status
  strings to a separate skill file, so that skill was the second file opened, not the
  first. Fixed the same day by moving the essentials into the mirror index. It is a
  content bug in one index, found by the measurement, not a property of the design; the
  next measurement will say whether the fix took.
- The repository rules cost roughly 900 tokens more per session than before, because
  the rules that have bitten are now imported rather than pointed at. That is a
  deliberate trade: an enforced guardrail over a cheaper best-effort one.
- One session left the generated task roster stale because regenerating shells out to
  `git log` and the run had been told not to run git. The instruction, not the design;
  noted so nobody mistakes it for a routing failure.
- The global instructions grew 700 tokens over the build day. They are read by every
  session in every topic and they need a pass.

## Routing misses

The design's own failure mode is a fact that exists but that no route reaches. Two
sources were checked. (a) Feedback memories written after a mistake a memory would
have prevented carry `missed_route: true`; **zero** such memories exist since the
mechanism was introduced on 2026-09-18, which is one day of history and proves little
yet. (b) The titles condition, run as the safety net, found nothing the routes-only
condition missed: same correctness, same zero misses, slightly higher cost and fewer
first-attempt hits. **Routes-only stays the default; the titles tier stays behind a
flag.** This will be re-run when the memory base is materially larger.

One thing the runs did find, in both conditions: a memory fact and a task row both
reported a batch of work as still outstanding, while the relevant repository's own
commit history showed it had been finished eight days earlier. A stale fact, not a
routing miss, and exactly the kind of drift a periodic read of the index is meant
to surface; recorded in the fact for the operator to confirm.

## Limitations

- **n = 3 per cell**, one sitting, one model, one operator's workspace, tasks chosen by
  the person who built the system. Enough to show direction and size; not enough to
  quote a decimal.
- **The sessions were subagents**, not interactive terminal sessions. They read the same
  files under the same instructions and report real token totals, but an interactive
  session carries more system-prompt overhead, which would make the percentages
  smaller and the absolute savings the same.
- **The before condition's instruction file told sessions to read the index whole.**
  That was the real instruction at the time, so it is the honest baseline, but a
  cleverer baseline instruction would have narrowed the gap.
- **Correctness was judged by the author** against the repository's own state files.
  The tasks have checkable answers (a live date, a generated file, an edited
  frontmatter field), which limits the room for generosity, but not to zero.
- **Line-ending noise**: git normalised CRLF/LF on checkout in the worktrees; no
  content differed, and the mirror check ran clean before the runs.

## Verdict

The claim was that tiering would cut what a session reads without cutting what it knows.
On this workspace, in this sitting: the controllable slice fell to 44%, real session
cost fell 19% (about 20,000 tokens a session), accuracy held at 27 of 27 with no missed
fact, and the only regression was a one-file content gap that the measurement itself
located. The size target of a quarter was not reached and the two levers for it are
named above.

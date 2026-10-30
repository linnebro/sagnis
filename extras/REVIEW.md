# Review process

Work moves through four separate claims, each with its own evidence. Never report a
later one without the earlier ones, and never let one stand in for another.

| Claim | Means | Evidence |
|---|---|---|
| **done** | the change exists | the commit or file |
| **verified** | deterministic checks ran and were observed passing | the command and its result lines (tests, selftests, `health_check.py --gate`, a render, a count) |
| **reviewed** | a separate pass read the diff, the criteria and the check output | a review record (below) that `health_check.py --review` accepts |
| **approved** | the owner said so | an `Approved-by: <owner> (<session id>, <time>, "<their words>")` commit trailer; `health_check.py --verify-approvals` as a commit-msg hook checks the quote against the session transcript |

## 1. Before you write

- Write the acceptance criteria down where the work is tracked (the task's `next`
  line, a spec, an issue).
- Read the task and every file it touches. Check memory for prior decisions: a
  `feedback_` fact overrides your default.
- Prefer an existing script, and a deterministic check over a model's judgement.

## 2. Verify

- Run it against real input; render documents and look at them; count what matters.
- Leave one check behind for non-trivial logic.
- A commit gate (`health_check.py --gate` as a pre-commit hook, and the same in CI)
  runs on its own. A refused commit is fixed, never bypassed with `--no-verify`.

## 3. Review

When the work is client-facing, irreversible, security-relevant, or the owner asks:

- A **fresh session**, not the one that did the work, so it does not inherit the
  worker's assumptions.
- The reviewer reads the diff (`git diff <range>`), the criteria and the check output
  itself, never the worker's summary, and fills in the record below beside the work.
- Each finding gets a severity and a status. `health_check.py --review <file> --owner <name>`
  refuses `verdict: pass` while a critical or high finding is open, or is accepted
  without the owner's quoted words.
- The worker fixes; the reviewer re-checks the fix and marks it `fixed <commit>`.

## 4. Present

- One report a reader can act on alone: what was done, what was verified (name the
  checks), whether it was reviewed (link the record), what is open, what needs the owner.
- Failed checks are shown, not summarised. Skipped scope is named, with why.
- Approval is asked for, then recorded as the trailer. "The owner's OK" in prose is
  not an approval.

## The review record

Copy into the work's folder as `review-<date>.md` and fill in:

```
---
reviewed: "<repo, branch and commit range>"
criteria: "<where the acceptance criteria are: a task line, a spec, an issue>"
reviewer: "<session id or person>, <date>"
checks: "<each deterministic check run and its result, or the files holding the output>"
verdict: fail
---
# Review: <what>

| # | Severity | Finding (file:line) | Status |
|---|---|---|---|
| R-1 | high | <what is wrong, where, the failure it causes> | open |
```

Status is one of: `open`; `fixed <commit>` (re-checked by the reviewer);
`accepted by <owner> ("<their words>")`; `not a defect (<why>)`.

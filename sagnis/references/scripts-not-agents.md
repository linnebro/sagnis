# Scripts, not agents: the delegation ladder

Stop at the first rung that holds.

| Rung | Use it when | Cost after it exists |
|---|---|---|
| 1. **Do nothing** | The task is speculative or one-off and cheap by hand | zero |
| 2. **A script** | The task is mechanical and will happen again: filtering, formatting, syncing, reporting, generating documents | zero tokens per run |
| 3. **A scheduled script** | Same, and it should happen without anyone asking (nightly research, morning digest, CRM sync) | zero tokens, plus a log line |
| 4. **A script that calls a free or local model** | The mechanical task needs language: classify, extract, draft a first pass, summarize | free-tier quota or local compute |
| 5. **A subagent of the expensive model** | Scoped search or build that needs real reasoning and can run in parallel with your own work | one full context load each |
| 6. **You, in the session** | Judgment, sequencing, anything outward-facing or irreversible, anything ambiguous | the most expensive tokens there are |

Rungs 5 and 6 are where the user's subscription goes. Rungs 2 to 4 are
where the project's recurring work should live.

## What a script looks like here

- Numbered by pipeline stage (`1_filter.py`, `2_research.py`, ...) so the
  order is obvious from a directory listing.
- Idempotent: safe to run twice. Checkpoint files for long pulls.
- Logs to a file next to it (`<stage>_log.txt`), one line per run with the
  date and the counts.
- Config in one place: one file for model ids, `.env` for secrets, a short
  constants block at the top for everything else.
- A `__main__` self-check or one small test for any branch, loop, parser
  or money path. No test framework unless one is already installed.
- Documented in a README beside it: what it does, its schedule, its inputs
  and outputs, the gotchas. The README is the operator manual; a session
  should never need to read the script to know what it does.

## What a worker call looks like

Whatever your script calls for a model, keep it to one function that takes a
task name, not a model name. The pattern that has held up:

- A task name maps to an ordered chain of providers in one config file.
- Each provider's model id is in that file, overridable by
  `<PROVIDER>_MODEL` in the environment, so a rename is a data edit.
- Failover moves to the next provider; a validation failure retries on a
  *stronger* one, never the same one.
- An exhausted chain raises and gets reported. That is the cue for the
  user to do those items in a session, not a reason to add a paid fallback.
- Anything touching private data goes to a local model or stays in the
  session. Free cloud tiers train on inputs unless the terms say otherwise.

## When an agent is right

- A search across many files where you only need the conclusion.
- A well-scoped build with a clear acceptance check, running in the
  background while you do something else.
- A verification pass on your own work, with fresh eyes.

Give the agent the file paths and the acceptance criterion. Do not give it
the whole task and hope. Never chain agents that reload the task from
scratch at each phase; that pattern was measured at four-plus full context
loads per small script and shelved.

## Where scripts run

In order of preference:

1. A cloud scheduler with a secret store (GitHub Actions, a serverless
   worker with cron). Runs whether the workstation is on or not.
2. The tool's own cloud routines, for jobs that need the assistant
   itself.
3. The OS task scheduler on the workstation, as a last resort and only
   for jobs that need local resources (a local model, a NAS, a licensed
   desktop app).

Never a poller or loop inside a chat session. If a cloud cron proves
unreliable, put the dispatch behind something with a guaranteed timer
(a durable-object alarm, a paid cron service) rather than moving the job
back to the desktop.

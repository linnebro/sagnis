# Extras

The core (`core/`) is memory: one fact per file behind a generated index. These
extras are what the setup Sagnis came from added around it, each after a specific
miss. None is part of the install. Add one when you hit the miss it names; leave it
out until then. Same rules as the core: Python 3 standard library, no accounts, each
script carries a `--selftest`.

| File | What it does | The miss that earned it |
|---|---|---|
| [WORKING-RULES.md](WORKING-RULES.md) | A paste-in block of working rules for your `AGENTS.md`, with the reason for each | The assistant repeating the same working mistakes (untested reports, unasked rewrites, `git add -A`) across sessions |
| [REVIEW.md](REVIEW.md) | The four claims as a process: verify, a fresh-session review with a record, approval as a quoted commit trailer | "Done" reported for work that was written but never run, reviewed by the session that wrote it |
| [backup_config.py](backup_config.py) | Before a config change: a git tag on HEAD (pushed) and a zip of every tracked file plus your untracked settings | A change to the file every session reads first can break every session at once |
| [health_check.py](health_check.py) | Report-only drift check: unpushed and uncommitted work, stale indexes and task rosters, dead references and control characters in memory, context budgets, the audit trail, idle worktrees. Also the commit gate, the approval check and the review check | A reminder-only check was retired as unread; an audit then found the drift it would have caught |
| [build_tasks.py](build_tasks.py) | One file per initiative (`<topic>/initiatives/*.md`, one `## task` each) generates `TASKS.md` and a one-page `status.md` | A hand-kept task table drifted from the notes behind it; a chat or voice assistant with no repo access needed one page to read |
| [build_shims.py](build_shims.py) | One canonical `AGENTS.md`; generated `CLAUDE.md` / `GEMINI.md` / Copilot pointer files that import or name it | Two instruction files edited separately and disagreeing |
| [audit.py](audit.py) | An append-only, hash-chained record of every tool action (paths and hashes, never content), from Claude Code hooks or by hand; rotation, an archive copy and a tamper check | No way to answer "which session changed this file, and when" after the fact |
| [leak_check.py](leak_check.py) | Refuses a commit that names anything on your private term list, or carries an email, phone number or home-folder path | Publishing a repo built from a private workspace: the list of what to keep out is itself private, so it lives outside the repo |

## Where they go

Put the scripts beside `sagnis.py` (for Claude Code, `~/.claude/skills/sagnis/scripts/`).
`health_check.py` uses `sagnis.py`, `build_tasks.py`, `build_shims.py` and `audit.py`
when they sit beside it or in `../core/`, and skips a check whose script is absent.
The examples below assume your workspace is `~/.claude` with memory in
`~/.claude/knowledge`; change the paths to yours.

## Wiring them in

**Back up before a config change.** Add the rule from WORKING-RULES.md, then:

```
python backup_config.py --master ~/.claude --label hooks
```

**The health check after every session (Claude Code).** In `settings.json`:

```json
"hooks": {
  "SessionEnd": [{"hooks": [{"type": "command", "timeout": 60,
    "command": "python ~/.claude/skills/sagnis/scripts/health_check.py --master ~/.claude --budget AGENTS.md,knowledge/MEMORY.md:2000 --out ~/.claude/health/latest.txt || true"}]}],
  "SessionStart": [{"hooks": [{"type": "command", "timeout": 5,
    "command": "python ~/.claude/skills/sagnis/scripts/health_check.py --hint ~/.claude/health/latest.txt || true"}]}]
}
```

The next session gets one line when the last check found something, never the
findings themselves. Add your project repos as arguments to the SessionEnd command.
Use `--memory <folder>` if your memory folder is not `<master>/knowledge`.

**The commit gate and the approval check.** In the repo that holds your memory:

```
# .git/hooks/pre-commit
#!/bin/sh
exec python "<PATH TO>/health_check.py" --master "$(git rev-parse --show-toplevel)" --gate

# .git/hooks/commit-msg
#!/bin/sh
exec python "<PATH TO>/health_check.py" --verify-approvals "$1" --owner "<your name>"
```

**The audit trail (Claude Code).** Add `audit/` to the workspace's `.gitignore`, then
register one command on `PostToolUse`, `PostToolUseFailure`, `SessionStart`,
`SessionEnd`, and `PreToolUse` with the matcher `Write|Edit|MultiEdit|NotebookEdit`
(the hash before a write):

```
python ~/.claude/skills/sagnis/scripts/audit.py hook --master ~/.claude || true
```

Set `AUDIT_ARCHIVE` (in `settings.json` under `"env"`) to a second disk or a NAS to
keep a copy off the machine; unset keeps everything local. `audit.py query` reads it
back; `audit.py verify` is the restore test. An assistant without hooks records with
`audit.py record`, stamped `manual`, so a gap reads as a gap.

**Publishing from a private workspace.** Keep your term list outside the published repo
(names of people, clients, places, project names; `!term` allows a reviewed generic
word), then in the published repo:

```
# .git/hooks/pre-commit
#!/bin/sh
exec python extras/leak_check.py --terms "$HOME/private-terms.txt"
```

Before a push, check every commit, not only the last: `python extras/leak_check.py
--terms ~/private-terms.txt --range origin/main..HEAD`. A deleted file is still
published in the commit that added it.

## Status

Each script runs on the setup it came from (Windows 11, Claude Code): the audit and
health-check hooks every session, the others when their task comes up. Paths, names
and examples were made general for this repository and the selftests rerun.
`health_check.py` here is a smaller, general version of that one (its folder-mirror
and automation-schedule checks were specific to that setup and are left out).
`leak_check.py` is new and has been run on this repository only. None of these has
an outside install yet; if one stalls you, [open an issue](../../../issues/new?template=install-stall.md).

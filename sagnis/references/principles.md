# Principles, and why each one exists

Each rule below was paid for. The "why" is what keeps a future session from
quietly undoing it.

## 1. Memory is files, not context

The model forgets everything at the end of a session. If a design preference
lives only in the chat, it is gone. So every preference, correction, decision
and gotcha becomes a small file in `knowledge/`, and an index of one-line
pointers is loaded at the start of every session.

Why one fact per file: a big memory document gets re-read in full every time
and grows stale in the middle. One fact per file means the index is cheap to
load, an individual fact is cheap to open, and a wrong fact is one delete.

Why frontmatter with a `type`: `user` (who they are), `feedback` (how they
want you to work, with the why), `project` (what is in flight, with absolute
dates), `reference` (pointers to external things). The type tells a future
session how much to trust it and when it goes stale.

## 2. Master space and project space are separate

The master space (`~/.codex` or `~/.claude`) is *how to work for this
person*. The project space is *the work*. Mixing them means memory gets
committed into a project repo, or working files get lost in a dotfolder
nobody indexes.

Every project folder is its own git repo. The master space is its own
private repo. A new machine, a phone session, or a cloud session clones
both and has everything.

## 3. Index first, then one file

Every project repo has an `INDEX.md` listing every file and folder with a
one-line description. The session reads the index and loads only what the
task needs. This is the single biggest token saving: no directory walks, no
"let me grep for that", no reading five files to find the right one.

The index is maintained by the same session that adds a file. A file not in
the index does not exist as far as the next session is concerned.

## 4. Director, not executor

The expensive model is for judgment: what to build, in what order, what is
safe, what the user will care about. Anything mechanical goes down the
delegation ladder: a script first, a scheduled script second, a cheap or
free model third, and an agent of the expensive model last.

Why: a chain of agents that each reload the task from scratch is the most
expensive possible way to do repetitive work. One team measured a
four-phase agent pipeline at four-plus full context loads per small script
and shelved it. A `.py` file that runs nightly costs nothing after it is
written.

## 5. Guardrails are written where the rule was broken

A rule that lives in someone's head gets broken again. The repo `AGENTS.md`
has a section called "Rules that have bitten before". When something goes
wrong twice, the rule goes there with one line on what it cost. The session
reads it every time. That is the whole guardrail system, and it works
because it is short and specific.

## 6. Verify, then report, then push

"Done" means run, checked, committed and pushed in the same turn. A report
leads with what was verified and states plainly what was not. A local
commit that was never pushed is invisible to every other device and every
other session, and the session that wrote it is gone by the time anyone
notices.

## 7. Automation runs in the cloud, or on a schedule, never in the chat

Anything recurring is a script on a scheduler (GitHub Actions, a cloud
worker, the OS task scheduler as a last resort), with logs and a daily
health digest. The chat session is for deciding and building, not for
babysitting a loop.

## 8. The setup grows with the work

The journal records what each session did. Read across a month, it shows
where the friction is: the same manual step three times, a folder that
does not exist yet for a topic that keeps coming up, a rule broken again.
The growth review turns those signals into concrete recommendations. The
setup that was right at one customer is wrong at ten, and the journal is how
you notice.

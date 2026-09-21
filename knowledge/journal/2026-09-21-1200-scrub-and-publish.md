---
date: 2026-09-21
time: "12:00"
topic: "sagnis / scrub and publication"
summary: "All 129 files read for anything naming a real person, business, client, path or machine; the internal build plan and the six raw measurement files deleted rather than sanitized; repository made public"
next: "Fold in what the first outside installs teach; re-measure on a larger memory base"
---

## What was checked

Every file in the repository was read start to finish before publication, in three
passes over the package, the fictional example and the root plus in-repo workspace.
Greps alone were not trusted: the worst findings were in prose and in selftest
fixtures, where a keyword search for a business name returns nothing but the shape of
the business is still legible.

Clean on the things that would have been worst: no credentials, API keys or tokens
anywhere; no email addresses; no Windows paths, NAS paths or machine names in any
shipped file; no third-party client names. Two commits in the history and no deleted
files, so the working tree was the whole exposure.

## What was removed rather than fixed

`BUILD-PLAN.md` was deleted. It was an internal project journal, not documentation:
roughly seventy lines naming the author, the reference business and its repositories,
real commit hashes, a personal work schedule, the workstation's git signing posture,
and a set of open to-dos addressed to one person. Sanitizing it line by line would
have left nothing a public reader wants.

The six files under `evidence/` were deleted for the same reason. They were
folder-by-folder inventories of a working business: file counts, byte counts, folder
names, and the client-facing structure behind them. The folder's own README said
outright that these files named real repositories and had to be sanitized before any
of it was published, and that scrub had never happened. `EVIDENCE.md` is the summary
that survives, and it was already written without identifying detail; its citations
to the raw files were replaced with a plain statement that the per-session logs came
from a private repository and are not published. `measure.py` reproduces the numbers
on any workspace, which is the honest substitute for raw data that cannot ship.

## What was rewritten

`THESIS.md` carried the architecture diagram as a picture of the author's two real
trees, down to the client folder names. It now draws the fictional example instead,
so the diagram and the shipped `example/` finally agree. Two prose passages that
quoted an exact census of a private index were softened to approximations that make
the same argument.

`EVIDENCE.md` lost two anecdotes that were specific engagement state rather than
evidence, and its description of the measured setup dropped a file count that
contradicted another file anyway.

Selftest fixtures were the quiet problem. A usage string carried a real first name,
a journal parser test asserted on a real approval line, a task parser used what read
as real prospect names plus defence-contracting vocabulary, and the health check's
fixtures reproduced a numbered outreach pipeline filename by filename. All were
replaced with neutral equivalents and every selftest re-run.

The publication initiative and the standing rules described a repository that was
private and a pre-publication gate that had not been passed. Both would have been
false the moment the repository flipped, and one of them described an unwitting test
subject in terms that read badly in public. Rewritten for a repository that is now
published.

## Smaller corrections found on the way

The README undercounted the example workspace by one fact. A mirror index still
called the project a lightweight framework, contradicting the README two directories
up. Five package-relative paths were written in root-level documents where they do
not resolve, and the "open an issue" link pointed at the template source file rather
than a new-issue URL.

## Known and not fixed

The fictional example has quality bugs that are not privacy problems and did not gate
publication: several memory files reference a quote generator that `Automations/`
does not implement, a `Website/` folder and two quote folders that the indexes
describe but that do not ship, a site visit dated on a crew day in contradiction of
the schedule rule the fiction states twice, and a three-row route sheet standing in
for forty customers. The example also ships a verbatim copy of `health_check.py`
whose selftest cannot pass there, because the sibling modules it imports are not
copied alongside it; the checks are guarded so it degrades quietly rather than
crashing. That was already true before this pass and the scrub did not change it.
They are listed here so the next session fixes them rather than rediscovering them.

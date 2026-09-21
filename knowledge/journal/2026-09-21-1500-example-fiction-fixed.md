---
date: 2026-09-21
time: "15:00"
topic: "sagnis / example fiction bugs fixed"
summary: "The five inconsistencies in the Fernwood example are closed: quotes are filled from the template rather than by a generator that did not exist, Website/copy.md and the two described quote folders now ship, the Hollis site visit moved to a Thursday, and the route sheet is labelled a sample"
next: "Fold in what the first outside installs teach; re-measure on a larger memory base"
---

## What was wrong

Three memory files described a quote generator that `Automations/` never
implemented. Three files pointed at a `Website/` folder and two quote folders that
were not in the tree. The Hollis site visit was dated a Friday, a mowing day, against
the schedule rule the fiction states twice. The route sheet had three rows while the
campaign fact called it the list of forty customers. All found in the pre-publication
audit and deferred because none of it was a privacy problem.

## What changed

**No generator.** A two-person landscaping company fills a one-page quote from a
template; it does not need a script for it. The quote-format fact, the quotes
mirror index and the repo index now say quotes are filled from `Templates/quote.md`
and that a format change starts in the template and then goes into any open quote.
The general rule that generated documents are edited at their generator stays,
because the route sheet is generated. The cover-note file the index promised was
dropped from the description rather than invented three times over.

**The folders exist.** `Website/copy.md` is a short service-page draft in Maya's
voice, waiting on her read as the initiative says. `2026-09-ferris-wall-lost/` and
`2026-08-marlow-walkway-won/` each hold a filled site-visit sheet and a quote in the
template's exact shape. The Ferris sheet carries the story beat: the first quote
went out without the checklist and with hours listed, and the hours became the
conversation. The photos moved out of the repo in the fiction, since binary photos
do not belong in an example.

**Thursday.** Hollis site visit 2026-09-10, quote sent that evening. Ferris first
quoted 2026-09-03 (Thursday), redone 2026-09-10 after a proper visit. Marlow visited
2026-08-18 (Tuesday). Every hardscape date now lands on a Tuesday or Thursday,
checked with the calendar rather than by eye. Task due dates on mowing days were
left alone: a deadline is not a scheduled visit.

**Labelled sample.** The project README, the one file written for the person rather
than the model, says the route sheet holds three sample rows.

## Folded in from the audit's small list

The master-space instruction file had an unfilled `<private repo url>` placeholder
and a row label that still said "The operating model"; both fixed. The route-sheet
stub promised a logs folder that does not exist; the promise is gone from both the
docstring and the README. The gitignore template still whitelisted the audit
manifest, a file the narrowed package no longer produces; removed from the template
and the example copy, which also makes the example's git-conventions fact accurate
again.

## Verified

Both scaffold and index selftests pass with the changed template. Both workspaces
regenerate and `--check` clean. A search for the old wording finds nothing outside
the one general rule that is still true.

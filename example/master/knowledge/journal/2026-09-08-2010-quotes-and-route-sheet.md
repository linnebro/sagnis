---
date: 2026-09-08
time: "20:10"
topic: "Fernwood / quotes and the route sheet"
summary: "First script: build_route_sheet.py written after the QuickBooks export sent Dev to three wrong addresses; quote format decided: one price, no hours"
next: "Redo the Ferris wall quote with the site-visit checklist; Maya reads the website copy"
---

First script today: `Automations/` with `build_route_sheet.py` in it. The
QuickBooks export drops the second address line, which is why the river road route
had three wrong stops last Wednesday; the script joins `Customers/addresses.csv`
first. Recorded as a reference fact.

Quote format decided after the Ferris wall quote turned into a negotiation over the
listed hours: one page, one price, a "not included" list, dates in words. Logged, and
`Templates/quote.md` rewritten to match.

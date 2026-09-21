---
title: Repository root
description: "the Fernwood Landscaping repo itself: what it is, the folder map with a pointer to each mirror index, the root files"
keywords: [repo root, README]
mirrors: "."
---

# Fernwood Landscaping repository — mirror index of `~/Projects/Fernwood Landscaping` (root level)

Hand-maintained (no generated header). Two-person landscaping company: mowing routes,
spring cleanups, hardscape quotes. Pull only the specific file(s) relevant to the
task, never a whole folder.

**Storage:** this folder is a git repo pushed to a private remote. Gitignored
(private data, never on GitHub): `Customers/`, `Invoices/`.

## Folder map (one mirror index per folder that earns one, beside this file)
- `Automations/` — scripts and the README that documents each one: `build_route_sheet.py`
- `Customers/` — gitignored: QuickBooks exports, `addresses.csv`, `gate-codes.csv`, `suppliers.csv`
- `Invoices/` — gitignored: monthly timesheets and invoice PDFs
- `Outreach/` — letters and the quote-request inbox; drafts only, Maya sends
- `Quotes/` — one folder per quoted job; see [quotes/INDEX.md](../quotes/INDEX.md)
- `Routes/` — `route-sheet.csv`, the customer list of record for scheduling
- `Templates/` — `quote.md`, `site-visit.md`; a format change starts here
- `Website/` — `copy.md`, the service-page draft waiting on Maya

## Root files
- `AGENTS.md` / `CLAUDE.md` — the shim: read order into the AI workspace, `@import` of `RULES.md`
- `README.md` — one paragraph for Maya
- `.gitignore`

---
name: feedback_never_round_hours
title: "Never round crew hours"
description: "timesheets keep the quarter-hour as logged; rounding happens in payroll, not in the sheet"
metadata:
  type: feedback
---

Crew hours in `Invoices/timesheet-YYYY-MM.csv` stay exactly as logged, to the quarter
hour. Payroll rounds; the sheet does not.

**Why:** a rounded sheet on 2026-09-12 disagreed with Dev's own notes by forty
minutes and took an evening to reconcile.

---
title: "QuickBooks export gotcha"
description: "the customer CSV export drops address line 2; re-join Customers/addresses.csv before rebuilding the route sheet"
source: "route rebuild, 2026-09-08"
updated: 2026-09-08
keywords: "QBO, quickbooks, export, CSV, address, apartment, wrong address, route sheet"
---
QuickBooks Online's customer export (Customers/qb-export-YYYY-MM.csv, gitignored) omits the second address line, so every apartment and rural-route customer lands on the route sheet with a truncated address. The fix is a join against Customers/addresses.csv before the sheet is rebuilt; Automations/build_route_sheet.py does it.

**Why it is written down:** the first rebuild on 2026-09-08 sent Dev to three wrong addresses on the river road route.

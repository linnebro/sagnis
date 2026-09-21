---
name: reference_mowing_route_sheet
title: "Mowing route sheet"
description: "Routes/route-sheet.csv is the customer list of record for scheduling: route, day, order, gate code column stays blank in git (codes live in Customers/)"
metadata:
  type: reference
---

`Routes/route-sheet.csv` (tracked) has one row per recurring customer: route (north,
river, town), day, stop order, mowing notes. The gate-code column is blank in the
tracked file on purpose; codes live in `Customers/gate-codes.csv`, which is gitignored.
The sheet is rebuilt by `Automations/build_route_sheet.py` from the QuickBooks export
after the address join ([[reference_quickbooks_export_gotcha]]).

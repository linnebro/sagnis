# Work — tasks (kept by hand; the last column is the automation policy)

The assistant may add a row and update the clean-runs count at any time. Only the
owner changes a status to *approved*. A row is an automation candidate at 3 clean
runs, and only if it never sends or posts to anyone but the owner; the assistant
says so and does not create the automation.

| ID | Task | Why it matters | Reads | Writes or sends | What could go wrong | Status | Clean runs |
|---|---|---|---|---|---|---|---:|
| 1 | (one line) | | | | | proposed | 0 |

Status: proposed → approved → in progress → done, or rejected. Reset clean runs to 0
after any correction.

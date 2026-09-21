---
name: feedback_push_same_turn
title: "Push in the same turn"
description: "a commit that only exists on the laptop is invisible to the phone session; finished work is pushed before the report"
metadata:
  type: feedback
---

Finished work is committed by explicit path and pushed in the same turn as the report.

**Why:** on 2026-09-04 Maya asked the phone session for the mulch order sheet the
laptop session had written that morning. It was committed, not pushed, and the phone
session rebuilt it from scratch, differently.

**How to apply:** "done" means pushed. Stage by explicit path, never `git add -A`.

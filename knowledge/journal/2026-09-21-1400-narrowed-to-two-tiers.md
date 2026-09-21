---
date: 2026-09-21
time: "14:00"
topic: "sagnis / narrowed to two tiers"
summary: "Tier 3 removed whole: seven scripts, five references, the thesis and the intake, the router and its config. What ships is memory, routing, state, guardrails, and the scripts-over-agents rule. 104 files, five scripts, all selftests green"
next: "Squash to one commit and recreate the repository so the cut is not reachable from history; then fix the example's known fiction bugs"
---

## Why

The package had been built by generalising one operator's whole setup, and its
stated purpose is narrower than that: the folder structure, the markdown
conventions, the index that makes reading less work, and the case for scripts over
agents. Everything beyond that was one person's plumbing made generic, and some of
it described the shape of a private automation stack closely enough that a reader
could tell what it had been built for. The decision was to publish the model and
keep the machinery.

## What went

Tier 3 was the seam, and it was cut whole. Seven scripts: the model router, the
audit trail, the health check, the shim generator, the master-space linker, the
backup script and the route hook. Five references: hooks, compatibility, topologies,
review process and growth review. Two documents: the 768-line architecture thesis
and the onboarding questionnaire. The router's config template. And from the
example, the two copied scripts and their config.

One thing was promoted rather than cut. The AGENTS.md template's tier-3 block held
two rules and no plumbing: repeatable work becomes a script, not an agent, and bulk
runs on a metered API get a stated count first. That is the thesis itself, so it is
now a tier-2 rule.

## What that leaves

104 files. Five scripts: the index builder, the journal builder, the task roster
builder, the scaffold, and the measurer. Twelve templates. Four references:
principles, layout, guardrails, scripts-not-agents. SKILL.md, README, EVIDENCE.
The scaffold now has two tiers and writes the CLAUDE.md shim itself in two lines.

## What was verified

All five selftests pass. Both workspaces regenerate and `--check` clean. A scan of
every tracked file for the name of anything removed returns nothing outside the
journal, which keeps its history. The example's Automations folder holds only the
fictional route-sheet stub and its README.

## Still open

The cut is committed but the removed files remain reachable from the previous
commit until the repository is squashed and recreated, the same lesson as the first
publication. The example's fiction bugs from the earlier pass are unchanged.

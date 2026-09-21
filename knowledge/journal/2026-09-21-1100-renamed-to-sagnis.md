---
date: 2026-09-21
time: "11:00"
topic: "sagnis / renamed from ai-operating-model"
summary: "Project renamed to Sagnis and the category fixed to context system: package folder, in-repo topic, README, GETTING-STARTED, contributing guide, issue template and the example workspace all follow"
next: "Scrub the package for anything naming a real business, then make the repository public"
---

## Why Sagnis

The working name `ai-operating-model` was placeholder and the category word in
it was wrong. Availability was checked across npm, PyPI, crates.io, the GitHub
namespace and RDAP for .com/.dev/.io: Sagnis is free on all of them, including
the GitHub organisation and all three domains. The runner-up, Sakne, lost on
a GitHub account that already exists and a .com held since 2007 under registrar
locks.

## The category

Settled as **context system**, spelled out as "a file-based memory and context
system for AI coding agents".

Not a *framework*. A framework exposes an API you write code against and calls
back into your code, and there is nothing here to import. The word also invites
a comparison to the agent frameworks, which this loses on terms that are not
its own.

Not an *operating system*. An OS schedules execution and owns resources; this
schedules nothing and owns nothing, the harness does. "AI OS" is also the most
diluted phrase in the space, so it reads as marketing and sends a reader looking
for a kernel that is not here.

What it actually does is decide what reaches the model's context, which is the
work the field calls context engineering. The README now says all of this in
its first two paragraphs instead of claiming to be a lightweight framework.

## What changed

The package subfolder `ai-operating-model/` became `sagnis/` and was refreshed
from the master-space source, which had already been renamed in the same
session. The in-repo topic folder moved to `knowledge/sagnis/`. The name was
substituted through the README, GETTING-STARTED, CONTRIBUTING, AGENTS.md, the
bug issue template and the fictional Fernwood example.

THESIS.md took a real edit rather than a substitution. It used to open as
"Filesystem-Based AI Runtime" with a subtitle calling it a framework, offer
"AI operating system" as the conceptual shorthand, and then spend a paragraph
defending "runtime" against the objection that a folder structure does not
execute anything - an objection it conceded outright ten sections later with
"there is no runtime to run". That section now states what the project is not
and why each wrong word costs a reader.

The repository's own journal entry from 2026-09-19 was left naming
ai-operating-model. It is the record of what happened under the name in use at
the time, and rewriting it would be falsifying it.

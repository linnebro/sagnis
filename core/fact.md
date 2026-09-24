---
title: "Short name, as the index shows it"
description: "One line, at most 120 characters. This becomes the index line, so it is what the assistant reads to choose."
source: "Where it came from and when: a person and date, a document and section, a message"
updated: 2026-01-01
keywords: "optional: names, roles, acronyms both ways, synonyms, common misspellings. Search only; never read by the assistant"
---
The fact, in two to six sentences, with absolute dates. For a correction (`feedback_`),
add a **Why:** line. For work in flight (`project_`), say what is open and by when.

File name: `<type>_<slug>.md`. Types: `user` (who they are, how they work), `feedback`
(a correction or confirmed way of working, with the why), `project` (work in flight,
absolute dates), `reference` (a pointer or a gotcha about something external).
`sagnis.py save` writes this file for you; the template is here for a hand-written one.

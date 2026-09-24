---
name: sagnis
description: How to read and write my memory in <MEMORY ROOT>. Use whenever a task needs a fact about me, my work, my tools or where things live; when I say "remember this", "write that down" or "we decided"; and whenever I correct you.
---

# Sagnis

Memory is `<MEMORY ROOT>`: fact files behind a generated `INDEX.md`. The index and
the fact are the answer; never search my files or the web for what they hold.

## Read

1. Open `INDEX.md` whole (with topics: pick the topic from the routes, open that
   topic's `INDEX.md`). Open only the one fact whose line answers the question.
2. If no line fits, run `python sagnis.py find --root <MEMORY ROOT> "<the question>"`
   and open the fact it names. Say "not in memory" only after both come up empty;
   never fill the gap from general knowledge.
3. A fact carries its date. For a count, an owner or a status, say the date with the answer.

## Write

Your part is judgement: what is worth saving, the wording, the source. The script
does every index; never edit an `INDEX.md` by hand.

- A fact, new or changed:
  `python sagnis.py save --root <MEMORY ROOT> --type user|feedback|project|reference --slug <a-slug> --title "..." --description "<one line, ≤120 chars>" --source "<where, when>" --keywords "<names, acronyms, synonyms>" --body "..."`
- A correction from me: a `feedback` fact with the why, before anything else; then fix the fact it corrects.
- A decision: `python sagnis.py log --root <MEMORY ROOT> --text "<what, who, date>"`, and update the facts it makes false.
- A fact that proved wrong: `python sagnis.py delete --root <MEMORY ROOT> --file <name>.md`.
- One fact lives in one file. A fact two lookups need lives where it is asked most; the other names it in a clause.
- When I say "that's in memory" and you missed it: `python sagnis.py keywords --root <MEMORY ROOT> --file <name>.md --words "<the words I used>"`.

Save what I told you, decided or corrected, and what cost time to find. Do not save
what my files, my repo or these instructions already record.

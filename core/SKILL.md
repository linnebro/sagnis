---
name: sagnis
description: How to read and write my memory in <MEMORY ROOT>. Use whenever I correct you; when I say "remember this", "write that down" or "we decided"; and whenever a task needs a fact about me, my work, my tools or where things live.
---

# Sagnis

Memory is `<MEMORY ROOT>`: fact files behind a generated `INDEX.md`, which my
instructions import, so its lines are already in front of you. The index line and the
fact are the answer; never search my files or the web for what they hold.

## When I correct you

Before anything else, save a `feedback` fact: what I corrected, the rule going forward,
and the why in a **Why:** line. Then fix the fact it corrects, if there is one. This is
the one thing here that makes the next session better than this one.

## Read

1. The index line often answers. If not, open the one fact whose line fits. If the fact
   names a `notes/<slug>.md`, open that only when the fact is not enough.
2. If no line fits, run `python sagnis.py find --root <MEMORY ROOT> "<the question>"`
   and open the fact it names. Say "not in memory" only after both come up empty;
   never fill the gap from general knowledge.
3. A fact carries its date. For a count, an owner or a status, say the date with the answer.

## Write

Your part is judgement: what is worth saving, the wording, the source. The script does
the index; never edit an `INDEX.md` by hand.

- A fact, new or changed:
  `python sagnis.py save --root <MEMORY ROOT> --type user|feedback|project|reference --slug <a-slug> --title "..." --description "<one line, ≤120 chars>" --source "<where, when>" --status stated|verified|inferred|superseded --keywords "<names, acronyms, synonyms>" --body "..."`
- `--status`: **stated** only when I said or decided it (the source names me and the date);
  **verified** when you checked it at its authoritative source (add `--verified "<date> against <source>"`);
  otherwise **inferred**, the default: your reading, summary or assumption; **superseded** keeps
  history and names what replaced it. The index marks inferred and superseded lines; check an
  inferred fact at its source before acting on it when a wrong answer is costly.
- Changing an existing fact: `python sagnis.py show --root <MEMORY ROOT> --file <name>.md` first
  (it prints the fact's hash), then `save ... --expect <hash>`. Save refuses a fact that changed
  since you read it: read it again, never work around it. A stated or verified fact changes only
  on my word or a re-check at its source.
- A fact stays about 150 words. Longer detail goes in `<MEMORY ROOT>/notes/<slug>.md`,
  and the fact's body names it.
- A decision: update the facts it changes; the commit message carries what and why.
- A fact that proved wrong: `python sagnis.py delete --root <MEMORY ROOT> --file <name>.md`.
- One fact lives in one file. A fact two lookups need lives where it is asked most; the other names it in a clause.
- When I say "that's in memory" and you missed it: `python sagnis.py keywords --root <MEMORY ROOT> --file <name>.md --words "<the words I used>"`.

Save what I told you, decided or corrected, and what cost time to find. Do not save
what my files, my repo or these instructions already record.

## Claims about work

Four claims, never merged into one. Report each only with its evidence:

- **done**: the work exists. Name the file or the commit.
- **verified**: checks ran and you saw the result. Name each check and what it printed.
- **reviewed**: a separate pass read the change, what it had to achieve and the check
  output. Not the same pass that wrote it.
- **approved**: I said so, in words you can quote from this conversation. Record it as a
  commit trailer, `Approved-by: <me> (<date>, "<my words>")`. Never infer approval from
  silence, from a summary, or from my approval of something else.

## When a piece of work is done

`python sagnis.py build --root <MEMORY ROOT> --check` must print `DRIFT nothing`. Then
tell me it is a good point to start a new chat, unless the next step is still in
flight. A long chat costs more each turn and drifts: early details get lost to
summarizing, and gaps get filled with guesses. A fresh chat reads the saved facts instead.

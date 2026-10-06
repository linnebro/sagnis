# Evidence

The numbers behind the design, on two real setups. Raw logs stay private (they
inventory real businesses); what is here is what a skeptic can argue with.

## 1. The original setup: 27 sessions, one day (2026-09-19)

One operator, a 900-file business repository, 69 memory facts, Claude Code. **Before**
was a hand-curated memory document and a 12,800-token project index every session read
whole. **After** was one fact per file behind a generated index that routes by topic.

| | Before | After |
|---|---:|---:|
| Read before any work (instructions, memory, project index) | 17,961 tokens | 7,958 (44%), later 5,993 (33%) |
| Mean session cost, three real tasks × three fresh sessions | 107,839 tokens | 87,499 (−19%) |
| Correct answers | 27/27 | 27/27 |
| A needed fact missed by routing | 0 | 0 |

Why a 56% cut in what the workspace controls shows as 19% of the session: the
harness's own system prompt, tool schemas and skill listings are in every count, and
they are larger than anything the workspace reads.

## 2. The first outside install: Cowork, 35 facts (2026-09-23)

The package as first published was installed on a Microsoft 365 Copilot Cowork tenant
by migrating a hand-built context folder. It worked, and it read too much. Four tests
the same day produced the core in this repository.

**Test 1: the package as published vs a lightweight build of the same facts.** Same 17
questions, same three writes, a separate agent each.

| | As published | Lightweight |
|---|---:|---:|
| Bytes read per lookup | 11,155 (16,672 if the skill body loads) | 4,456 |
| Correct, from the right fact | 17/17 | 17/17 |
| Files written per save session | 11 | 8 |
| Index drift after the writes | none | **one, caught by lint** |

What was read before the fact was the whole difference: a root file that repeated
index lines, index headers that repeated the routes, a procedure that lived in two
places. None of it was the facts.

**Test 2: writes through a script instead of the model.** The same three saves replayed
through `save`: bytes the model read fell from 13,461 to about 7,150, and index drift
went from *caught after the fact* to *prevented on the save path*, since `save`
regenerates the index from the fact; a later hand edit is still caught by `build --check`. The
write procedure fell from 2.3 KB to 1.4 KB.

**Test 3: routing accuracy on 48 unseen questions** (11 indirect, 6 hidden-term, 5
acronym, 1 typo, 4 not in memory), scored by script and then by two agents.

| Method | Right fact first | In top 5 |
|---|---:|---:|
| Keyword topic routing by script | 18/44 | 19/44 |
| Full-text search, facts + keywords (`find`) | 35/44 | 43/44 |
| The model reading the topic index | 44/44 | |

The model routes; search is the safety net. A score cannot tell "absent" from
"present" (the four absent questions scored like real ones), so "not in memory" stays
the model's call, made only after both come up empty. The one wrong answer in every
condition was a missing definition, not routing.

**Test 4: what actually loads in a new Cowork chat.** Only built-in memory, and skill
names and descriptions. The instructions file and Personalization text did not. The
never-send rule was not in force until it was a built-in memory entry.

**`sagnis.py` against the same frozen set** (this repository's script, the migrated
corpus with its keywords): right fact first 37/44, in the top 5 42/44 plus the one
decision question answered from `LOG.md`; on an untouched copy of that corpus `build
--check` reports no drift, so the generated indexes are byte-identical to the tested
build's.

## 3. The first eleven days of use: 206 sessions (2026-09-23 to 2026-10-04)

The original setup ran the published shape for eleven days. Every session transcript
over 50 KB was then read for what the assistant actually did with the memory.

| | Sessions |
|---|---:|
| All sessions | 206 |
| In the business repository (where the work is) | 105 |
| ...that ran the script at all | 0 |
| ...that opened a fact or a topic index | about 6 |
| ...that searched the repository for a fact instead | 42 |
| In the memory workspace itself (saving, indexing, upkeep) | 100 |
| Facts saved through `save` | 11 sessions |
| Journal files written | 43 sessions, 155 files, 38,000 words, read by nothing |

What got read was the injected layer: the instructions file, the routes line, the rules
file the repository imports, and the few `feedback_` facts a session was pointed at. The
design asked the assistant to route from the instructions to a topic index to a fact on
its own, and in the business repository it skipped that hop 99 times in 105 and grepped
instead. Facts that are not in context are an archive, not a memory.

Three other things the eleven days showed. The facts had grown: median 274 words, seventeen
over 500, the largest 3,379, so "one fact per file" had become "one document per file".
Four overlapping records of state existed (task roster, decision log, journal, a status
page), rewritten four times in one day. And of nine scripts, one was wired to anything.

Changes made the same day, all now the published shape: the topic index is imported
into the instructions file rather than pointed at; a fact is about 150 words with the
long record in `notes/`; the journal and the decision log are gone, with commit
messages as the record; one task surface; and `budget` exists so the injected set has
a number. Half the sessions were upkeep of the memory itself; that is the
cost the cuts are meant to remove. Whether they do is the next measurement.

## What this does not show

One operator each; questions written by the same assistant that built the memory;
one model. The usage count in section 3 is a count of tool calls in transcripts, not a
measure of answer quality. The first week of real questions on a new setup is the test
that matters, and `keywords` exists so that week improves the next.

---
name: Sagnis
description: How to read and write my memory in /Documents/Cowork/knowledge/. Use at the start of every session (read MEMORY.md first), whenever I say "remember this", "write that down", "what did we decide", "learn the environment", "add to the backlog" or "show the list", whenever I correct you, and at the end of any session that decided or produced something.
---

# Sagnis

You remember by writing files, not by hoping the conversation survives. Preferences
do not persist facts between conversations; `/Documents/Cowork/knowledge/` does.

## Every session

1. Read `knowledge/MEMORY.md`: the Recent block, then the Routes table. When a
   trigger from the table comes up, open that topic's `INDEX.md` (one line per fact,
   whole), then only the fact file that matters.
2. If the task touches a SharePoint library or Teams channel that has a mirror index
   (the topic `INDEX.md` lists them under Routes), read that index and open only the
   document it names. Never search a library the index already describes.
3. `TASKS.md` in the topic is current state. `RULES.md` is read whenever the topic
   is. `LOG.md` only when the task needs to know *why* something was decided.

## Every session that decided or produced something

1. **Save facts.** One fact per file in the right topic folder, named
   `<type>_<slug>.md` where type is `user` (who the owner is, how they work),
   `feedback` (a correction, with the why), `project` (something in flight, with
   absolute dates) or `reference` (a gotcha, a location, a contact). Frontmatter:

   ```
   ---
   name: reference_evidence_library
   title: "Where control evidence lives"
   description: "one telegraphic line, the hook the index shows; keep every qualifier that makes it correct"
   source: "the file, message or meeting it came from"
   metadata:
     type: reference
   ---
   The fact, two to six sentences. Absolute dates.
   ```

   Update an existing file rather than writing a near-duplicate. Delete a fact that
   turned out wrong.
2. **Keep the indexes by hand**, same shape every time:
   - In the topic `INDEX.md`, under the heading for its type, newest first:
     `- YYYY-MM-DD [Title](file.md) — description`. Move the line to the top of
     its group when the fact changes. Update the fact count in `MEMORY.md` Routes.
   - In `MEMORY.md` Recent, the same line with the topic prefix on the path
     (`general/file.md`). Ten lines, newest first; drop the oldest.
3. **Write one journal file** `knowledge/journal/YYYY-MM-DD-HHMM-<slug>.md`:

   ```
   ---
   date: YYYY-MM-DD
   time: "HH:MM"
   topic: "work / what it was about"
   summary: "one line: what was decided or produced"
   next: "one line: what happens next, or empty"
   ---
   The full entry: what was found, decided, produced, verified, left out.
   ```

   Then replace the oldest of the three journal lines in `MEMORY.md` Recent with
   `- date time topic — summary. Next: next`. Skip the journal for a session that
   only answered a question.
4. **Update state.** A task change is its row in `TASKS.md` (status, clean-runs
   count; reset to 0 after a correction). A decision is one dated line in `LOG.md`.
   A rule the owner has had to give twice goes in `RULES.md` under "rules that
   have bitten", with what it cost and the date.
5. **A new topic** is a folder with `TOPIC.md` (title, description, keywords), an
   `INDEX.md` in the shape above, and a row in the `MEMORY.md` Routes table.
   Ask before creating one.

## Learning the environment (read-only)

When asked to learn or map the environment: calendar for the past 30 days, mailbox
folders and the 50 most recent threads, Teams channels, SharePoint sites visited,
top-level OneDrive folders. Record people and roles, recurring meetings and what they
decide, where policies and evidence live, active projects and deadlines, channels
that carry requests, and things that look wrong. Each is a fact file with its
source. A library that matters gets a mirror index (`knowledge/<topic>/<slug>/INDEX.md`,
one line per document) and a row in the topic's Routes. Things that look wrong are
reported, never fixed. Create nothing outside `/Documents/Cowork/`; send and move
nothing. End by listing which files changed, not by showing them whole.

## The task list

Any time work could be done but should not be started, add a row to `TASKS.md`:
what, why, what it reads, what it writes or sends, what could go wrong. Only the
owner changes a status to approved. When the owner says "work item N", do it step
by step and ask before every write. After each run, update the clean-runs count. At
three clean runs on a task that sends or posts to nobody but the owner, mark it an
automation candidate and say so; never create the automation.

## What to save, and what not to

Save: corrections and preferences with the why, decisions and their rationale,
gotchas that cost time, who the owner is and how they work, where things live.
Do not save: the contents of labelled or sensitive documents (save where they are),
anything the tenant already records, guesses.

## Before you report

Verify before saying something is done: open it, count it, check the link. Lead with
the outcome and say what was not verified. Say which memory files changed.

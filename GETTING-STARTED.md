# Getting started

One path per tier. Do Tier 1 today, then stop; it has to feel like a win before
anything else is worth adding. Paths below assume Claude Code (`~/.claude`); for
Codex CLI use `~/.codex` and drop `--tool claude`.

## Tier 1: memory and routing (20 minutes)

**1. Take your before-number** (2 minutes)

```
python sagnis/scripts/measure.py --master ~/.claude ~/Projects/<your repo>
```

Write down the cold load. That is what every session pays before it does anything.

**2. Install the package** (1 minute)

```
cp -r sagnis ~/.claude/skills/
```

**3. Scaffold** (2 minutes)

```
python ~/.claude/skills/sagnis/scripts/init_workspace.py \
  --master ~/.claude --project ~/Projects/<your repo> --name "<Name>" \
  --owner "<your name>" --description "<one line about the project>" \
  --tool claude --tier 1 --data-folders "<any folder that must never reach GitHub>"
```

It creates, and never overwrites: `~/.claude/AGENTS.md` (global instructions) with
a `CLAUDE.md` shim, `~/.claude/knowledge/` with a topic folder per area and a
generated `MEMORY.md`, one index of your repo's root, a seed journal entry, and in
your repo a two-line `AGENTS.md` shim plus `.gitignore`. If you already had a global
instructions file it is kept; merge the template's sections into it by hand.

**4. Make the global file true** (5 minutes)

Open `~/.claude/AGENTS.md`. Every line must be true for you: who you are, where
your files are, how you like to work. Delete what does not apply. Put three to
five route triggers in each `~/.claude/knowledge/<topic>/TOPIC.md`: the words that,
when they come up in conversation, mean "this topic" (product names, tools, places,
customer types).

**5. Write three memory files** (5 minutes)

Pick the three things the assistant keeps forgetting. One file each in the right
topic folder, from `sagnis/templates/memory-file.md`:

```
~/.claude/knowledge/general/feedback_ask_before_sending.md
~/.claude/knowledge/<topic>/reference_export_gotcha.md
~/.claude/knowledge/<topic>/project_current_push.md
```

Frontmatter `title` and `description` are what the index shows; write the
description as the one line you would want the assistant to see. Then:

```
python ~/.claude/skills/sagnis/scripts/build_index.py --knowledge ~/.claude/knowledge
```

**6. Describe your repo** (3 minutes)

Open `~/.claude/knowledge/<name>/repo/INDEX.md` and give every top-level folder and
root file one line. This is the index the assistant reads instead of walking the tree.

**7. Commit both, then feel the win** (2 minutes)

`git init` the master space (its `.gitignore` tracks only instructions, knowledge
and skills) and push it to a private remote. Commit the shim in your repo. Then
open a fresh session in your repo and ask it about one of the three things you
wrote down. It should answer from the fact file, and the transcript should show
it opened the index and one file, not the tree. Run `measure.py` again.

If it did not go that way, [open an issue](../../issues/new?template=install-stall.md)
saying where you stopped. That is a documentation bug, not your mistake.

## Copilot Cowork instead of a coding agent (15 minutes)

No shell, no git, no `AGENTS.md`: the master space is your OneDrive
`/Documents/Cowork/`, the instructions are a Preferences block, and the assistant
keeps the indexes by hand in the same shape the script generates. Copy
`sagnis/cowork/master/` into that folder, paste `sagnis/cowork/PREFERENCES.md`
into Customize > Preferences, and say *learn the environment, read-only* in a new
conversation. The rest, and what maps to what, is in
[sagnis/cowork/README.md](sagnis/cowork/README.md).

## Tier 2: state and guardrails (an hour, once Tier 1 is habit)

```
python ~/.claude/skills/sagnis/scripts/init_workspace.py \
  --master ~/.claude --project ~/Projects/<your repo> --name "<Name>" --tool claude --tier 2
```

Adds to the topic folder: `RULES.md` (read order and "rules that have bitten"),
`LOG.md` (one dated line per decision), `initiatives/` with a first initiative file
and standing rules, and a generated `TASKS.md` roster. The repo shim now imports the
rules file, so every session in that repo reads it.

Then:

- Move your open work into initiative files: one file per stream of work, one
  `## task` section per task with `area`, `when`, `status` and the whole detail.
  Regenerate; the roster is one row per task.
- The second time anything goes wrong, write it under "Rules that have bitten" in
  `RULES.md`: the rule, what it cost, the date. That section is the guardrail
  system. Keep it under a dozen lines.
- A decision worth remembering is one line in `LOG.md`, not a paragraph in chat.
- Anything you do by hand more than twice becomes a script, documented beside
  itself in the same commit. The delegation ladder in
  `sagnis/references/scripts-not-agents.md` says what goes to a script, what to a
  cheap worker, and what genuinely needs an agent.

## The first week: seeding the memory base

The day-two cliff is an empty memory base. Three files feel like a start; thirty
feel like the assistant knows you. Harvest, do not compose:

- **Corrections you have already given.** Scroll your last ten chats for every
  "no, do it this way". Each one is a `feedback_` file with the *why*.
- **Your README, runbooks and onboarding notes.** Each gotcha in them is a
  `reference_` file. Leave the document where it is; the memory file points at it.
- **What is in flight.** Each open thread is a `project_` file with absolute
  dates, or a task in an initiative file at Tier 2.
- **Who you are and how you work.** Days that are off-limits, devices you use,
  how you want reports shaped. `user_` files.
- **One fact per file, telegraphic description.** A file that says two things
  gets split. A description that needs a qualifier to be correct keeps it.

Regenerate after each batch and commit by explicit path. At the end of any session
that decided or built something, one journal file (`sagnis/templates/journal-entry.md`) and
a regenerate; the root index shows its summary line. After a month, read the
journal back in one sitting and ask three questions: what did I explain twice, what
did I do by hand more than twice, and what got decided and then relitigated. The
answers are the next memory file, the next script, and the next rule.

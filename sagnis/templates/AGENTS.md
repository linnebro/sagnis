# {{OWNER}} — global instructions (loaded in every session, any folder)

{{OWNER}} works on {{PROJECT}} ({{ONE_LINE_DESCRIPTION}}) and on other projects as
they come. `{{MASTER}}` is the AI workspace: the assistant's memory, indexes of
{{OWNER}}'s folders and working documents, one tiered topic folder each under
`knowledge/`. {{OWNER}}'s own files live in the human workspace,
`{{PROJECT_PARENT}}/<Name>`, which mirrors those topics and holds only what a person
needs to see plus what CI runs. Human documents never come here; the assistant's
files never go there.

## Where things are

| What | Where |
|---|---|
| Memory, all topics | `knowledge/MEMORY.md` (generated: Recent + Routes) → the topic `INDEX.md` a route names → the one fact that matters, or the mirror index of the human folder the task touches |
| Journal | `knowledge/journal/YYYY-MM-DD-HHMM-<slug>.md`, one file per session; `journal.md` is the generated rollup |
| This repo | private `{{MASTER_REPO_URL}}`, rooted at `{{MASTER}}` (tracks AGENTS.md, knowledge/, skills/) |
| {{PROJECT}} working files | `{{PROJECT_DIR}}` (git repo; its AGENTS.md is a shim; the model's index of it is `knowledge/{{PROJECT_SLUG}}/`: mirror indexes{{TOPIC_STATE}}) |
| New project | run `init_workspace.py` again with the new `--project` and `--name`: it makes `knowledge/<name>/` here (TOPIC.md, repo/INDEX.md, then mirror indexes as folders earn them) and the shim in the project folder |
| Sagnis | `skills/sagnis/`: SKILL.md is the session procedure |

## Memory conventions

- One fact per file in its topic folder (`general/` = how {{OWNER}} works and their
  tooling; a project folder = facts about it), frontmatter as
  `skills/sagnis/templates/memory-file.md`. Prefix `user_`, `feedback_`,
  `project_`, `reference_`; `title:`, `description:` (the index hook), optional
  `keywords:` (route triggers). Topic triggers live in `knowledge/<topic>/TOPIC.md`.
- GENERATED, never hand-edited: `MEMORY.md`, every topic `INDEX.md`, `journal.md`.
  Their sources: the fact files, `TOPIC.md`, the journal files. After any write:
  `python {{MASTER}}/skills/sagnis/scripts/build_index.py --knowledge {{MASTER}}/knowledge`,
  then commit the regenerated files with the source. A conflict in a generated file
  is never hand-merged: take either side, regenerate, commit.
<!-- tier 2 -->
- Also generated, by the same command: every topic `TASKS.md`, from
  `initiatives/*.md` (one file per initiative, one `## task` section each, close
  with `- done: <date>`). A decision worth remembering is one dated line in the
  topic `LOG.md`; a rule that has bitten twice goes in the topic `RULES.md`.
<!-- /tier -->
- Hand-maintained one tier down: `knowledge/<topic>/<folder>/INDEX.md` mirrors one
  human folder and changes in the same commit as the file it describes.
- A session that decided or built something ends with one journal file (from
  `skills/sagnis/templates/journal-entry.md`: `date`, `time`, `topic`,
  `summary`, `next`, the entry as body), a regenerate, then a commit and push of this
  repo staged by explicit path. A session that only answered a question skips the journal.

## How {{OWNER}} works (details in the memory files)

- Stage by explicit path, never `git add -A`. Other sessions and scheduled jobs
  touch the same trees.
- Backup before any config change (this file, the index generator, settings,
  the skill, a merge to main that rewrites those): a git tag and a zip of the
  master space, named in the report.
- Finished work gets pushed the same turn.
- Confirm before anything irreversible or outward-facing.
<!-- tier 2 -->
- Mechanical, repeatable work becomes a script or a scheduled job, not an agent and
  not something done by hand in the session.
- Ask before any bulk run on a metered API and before any pay-per-token model use.
  State the count first.
<!-- /tier -->
- {{ADD_ONE_LINE_PER_STANDING_PREFERENCE}}

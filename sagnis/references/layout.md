# Layout: master space and project space

`<MASTER>` is `~/.codex` for Codex or `~/.claude` for Claude Code. The
global instructions file is `AGENTS.md` everywhere (the cross-tool convention);
a tool that only reads its own name gets a two-line shim beside it
(`CLAUDE.md` = `@AGENTS.md`).

## Master space (private git repo, one per person)

```
<MASTER>/
├── AGENTS.md                 global instructions: who the user is, where things are,
│                             memory conventions, how they like to work (templates/AGENTS.md)
├── .gitignore                tracks ONLY AGENTS.md, knowledge/, skills/ (templates/gitignore)
├── knowledge/
│   ├── MEMORY.md             GENERATED (build_index.py): Recent facts + journal, Routes table
│   ├── <topic>/TOPIC.md      title, description, keywords (route triggers) for the folder
│   ├── <topic>/INDEX.md      GENERATED: every fact in the folder, one line each, whole hook,
│   │                         plus a Routes table to the mirror indexes below
│   ├── <topic>/TASKS.md      GENERATED (build_tasks.py): the roster, one row per open task
│   ├── <topic>/initiatives/<initiative>.md
│   │                         HAND-MAINTAINED: one file per initiative (never per folder), one
│   │                         "## task" section each with area/when/status(/done) and the whole
│   │                         detail; _rules.md = standing rules the roster prints first
│   ├── <topic>/LOG.md        decision history for the topic, one dated line per decision
│   ├── <topic>/<folder>/INDEX.md
│   │                         HAND-MAINTAINED mirror index of one human folder: frontmatter
│   │                         title, description, keywords, mirrors; every file described,
│   │                         warnings and history kept
│   ├── journal/              one file per session that decided or built something:
│   │                         YYYY-MM-DD-HHMM-<slug>.md, frontmatter summary + next, whole entry as body
│   ├── journal.md            GENERATED (build_journal.py): rollup, newest first, for grepping
│   ├── general/              how the user works, tooling, infrastructure
│   │   ├── user_*.md         who they are, schedule, devices
│   │   ├── feedback_*.md     corrections and confirmed approaches, each with a Why
│   │   ├── project_*.md      cross-project projects (hardware, hosting, automation)
│   │   └── reference_*.md    pointers, gotchas about tools
│   ├── <project-a>/         facts about that project only
│   ├── <project-b>/
│   ├── ideas/                things not yet a project; project_ideas_ledger.md ranks them
│   └── archive/              closed topics, kept for the record, not loaded as context
└── skills/
    └── sagnis/   this skill (Codex reads ~/.codex/skills, older builds ~/.agents/skills; copy)
```

Rules:
- Human documents never live here. The model's own working documents for a
  topic (notes, drafts, roadmaps, runbooks, initiative notes) do, inside that
  topic's folder, mirroring the human folder they concern.
- Memory files follow `templates/memory-file.md`. Prefix says the type.
- After any memory or journal write, commit and push this repo, staging by
  explicit path.
- If the tool has an auto-memory directory per project (Claude Code does:
  `projects/<encoded-cwd>/memory`), point it at `knowledge/` with a
  symlink or junction so every project reads and writes the same base.

## Project space (one git repo per project or idea)

```
~/Projects/<Name>/
├── AGENTS.md                 the shim: read order into the AI workspace + @import of the
│                             topic's RULES.md (templates/REPO-AGENTS.md). Nothing else of
│                             the model's lives here: index, tasks, log, notes are in
│                             <MASTER>/knowledge/<topic>/
├── README.md                 optional, for the person: what the folder is
├── .gitignore                private data folders, secrets, generated outputs
├── <data folders>/           gitignored private data; local disk or a NAS, never GitHub
├── <scripts folder>/         the project's own scripts, once it has repeatable work, plus a
│                             README that documents each one and its schedule
└── <working folders>         proposals, outreach, delivery, whatever the project does
```

Rules:
- The folder's mirror index (`<MASTER>/knowledge/<topic>/<folder>/INDEX.md`)
  is updated in the same commit that adds, moves or rebuilds a file.
- The topic `TASKS.md` (generated) is truth for state. The topic `LOG.md` is
  truth for why. Neither is a transcript; the journal is the session record.
- Nested repos (a toolbox, a product) are gitignored in the parent, get their
  own shim with `../` paths and their own mirror index; a change spanning both
  lands as two commits, and both get pushed or neither.
- No generated or model-only file is ever written into a human folder.
- Scheduled jobs commit and push on their own. A clean `git status` does
  not mean work was lost; check `git log` first.

## Where the two meet

The project repo's `AGENTS.md` says, first line: read
`<MASTER>/knowledge/MEMORY.md`, then `<MASTER>/knowledge/<topic>/INDEX.md`,
and imports the topic's `RULES.md`. If the project repo is cloned somewhere
the master space is not (a cloud sandbox), add the master repo as a git
submodule at `AI-Memory/` so the same files travel with it.
On the workstation that path can be a symlink to the live master space so
there is never a second copy.

## Multiple projects

Each project is a separate repo with its own index and its own knowledge
folder. Nothing is shared between them except `knowledge/general/`. A
per-project skill (five lines: "when working on <Name>, load its
INDEX.md first") is the cheapest way to make the assistant land in the
right repo without being told the path each time.

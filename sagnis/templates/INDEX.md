---
title: Repository root
description: "the {{PROJECT}} repo itself: what it is, the folder map with a pointer to each mirror index, the root files"
keywords: [repo root, README]
mirrors: "."
---

# {{PROJECT}} repository — mirror index of `{{PROJECT_DIR}}` (root level)

Hand-maintained (no generated header). {{ONE_LINE_DESCRIPTION}} Pull only the
specific file(s) relevant to the task, never a whole folder.

**Storage:** this folder is a git repo pushed to `{{PROJECT_REPO_URL}}`. Gitignored
(private data, never on GitHub): {{DATA_FOLDERS}}.

## Folder map (one mirror index per folder that earns one, beside this file)
- (one line per top-level folder, added the day the folder appears)

## Root files
- `AGENTS.md` / `CLAUDE.md` — the shim: read order into the AI workspace
- `README.md` — optional note for {{OWNER}}
- `.gitignore`

<!-- Every file in the root and every top-level folder must be named here; a folder
that grows past a few entries gets its own mirror index (<topic>/<folder>/INDEX.md
with frontmatter title, description, keywords, mirrors) and one line here pointing
at it. -->

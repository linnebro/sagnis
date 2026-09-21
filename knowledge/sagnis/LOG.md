# sagnis — Decision Log

One dated line per decision. State is in the generated `TASKS.md`; the mirror indexes
say what each folder holds; this file is the *why*.

- **2026-09-19** — Repository created, private at first so the scrub could be done in the open.
- **2026-09-21** — Renamed to Sagnis and made public. The internal build plan and the raw
  measurement files were deleted rather than sanitized; `EVIDENCE.md` is the summary
  that survives and `measure.py` reproduces it. The category wording settled as
  "context system": not a framework, not an operating system.
- **2026-09-21** — A harness that cannot run a script gets a build, not a fork: `sagnis/cowork/`
  carries the same folders and index shapes onto OneDrive with the indexes kept by hand,
  laid out so `build_index.py` can take over when the folder is synced to a machine with Python.
- **2026-09-19** — The installable package stays a subfolder (`sagnis/`) so `cp -r` into a skills directory is the whole install; the front door (README, GETTING-STARTED, example) lives at the root.
- **2026-09-19** — MIT licence.
- **2026-09-19** — The repository carries its AI workspace in-repo (`knowledge/`), the submodule-style topology, because a public repository has no shared master space.

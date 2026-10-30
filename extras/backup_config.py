#!/usr/bin/env python3
"""Back up the master space before a configuration change. Stdlib only.

    python backup_config.py --label hooks-merge                  # master = $SAGNIS_MASTER or ~/.claude
    python backup_config.py --master ~/.codex --label hooks --out ~/Backups
    python backup_config.py --selftest

A configuration change is anything that alters what a session reads or runs
before it does any work: the global instructions, the memory index shape, hook
or settings files, the skill package, or a merge to the main branch that
rewrites those. The rule (WORKING-RULES.md): back up first, every time.

Two artifacts, so the backup survives both a bad commit and a bad file:

1. A git tag `pre-<label>-<date>` on HEAD, pushed if a remote exists. Restore
   with `git checkout pre-<label>-<date> -- <path>` or a full reset.
2. A zip in --out: `git archive` of HEAD (every tracked file) plus the
   untracked files that matter (settings.json and settings.local.json by
   default, more with --extra) under `_untracked/`. Integrity-tested.

Nothing is deleted or rotated; a backup is small and a year of them is cheap.
"""
import argparse
import datetime as dt
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_MASTER = Path(os.environ.get("SAGNIS_MASTER") or Path.home() / ".claude")
DEFAULT_EXTRAS = ("settings.json", "settings.local.json")


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def backup(master, label, out, extras=DEFAULT_EXTRAS, date=None, push=True):
    master, out = Path(master).expanduser(), Path(out).expanduser()
    date = date or dt.date.today().isoformat()
    tag = f"pre-{label}-{date}"
    head = git(master, "rev-parse", "--short", "HEAD")
    existing = git(master, "tag", "-l", tag)
    if not existing:
        git(master, "tag", tag)
    pushed = False
    if push and not existing and git(master, "remote", check=False):
        pushed = subprocess.run(["git", "-C", str(master), "push", "-q", "origin", tag],
                                capture_output=True).returncode == 0
    # untracked files live in the main checkout only; a worktree has none of them
    main = Path(git(master, "rev-parse", "--path-format=absolute", "--git-common-dir")).parent
    out.mkdir(parents=True, exist_ok=True)
    zpath = out / f"{main.name.strip('.') or 'master'}-config-{tag}.zip"
    git(master, "archive", "--format=zip", "-o", str(zpath), "HEAD")
    added = []
    with zipfile.ZipFile(zpath, "a") as zf:
        for name in extras:
            p = main / name
            if p.is_file():
                zf.write(p, f"_untracked/{name}")
                added.append(name)
    with zipfile.ZipFile(zpath) as zf:
        bad = zf.testzip()
        count = len([n for n in zf.namelist() if not n.endswith("/")])   # git archive adds dir entries
    if bad:
        raise RuntimeError(f"zip integrity failed at {bad}")
    return {"tag": tag, "tag_existed": bool(existing), "pushed": pushed, "head": head,
            "zip": str(zpath), "files": count, "untracked": added}


def selftest():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        m = d / ".master"
        (m / "knowledge").mkdir(parents=True)
        (m / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
        (m / "knowledge" / "MEMORY.md").write_text("index\n", encoding="utf-8")
        (m / "settings.json").write_text("{}", encoding="utf-8")
        (m / ".gitignore").write_text("settings.json\n", encoding="utf-8")
        git(m, "init", "-q")
        git(m, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        git(m, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")
        r = backup(m, "test", d / "out", date="2026-01-01", push=False)
        assert r["tag"] == "pre-test-2026-01-01" and not r["tag_existed"], r
        assert r["untracked"] == ["settings.json"], r
        with zipfile.ZipFile(r["zip"]) as zf:
            names = zf.namelist()
        assert "CLAUDE.md" in names and "knowledge/MEMORY.md" in names and "_untracked/settings.json" in names, names
        assert r["files"] == 4, names
        assert git(m, "tag", "-l", "pre-test-2026-01-01")
        r2 = backup(m, "test", d / "out", date="2026-01-01", push=False)   # rerun: tag kept, zip refreshed
        assert r2["tag_existed"]
        git(m, "worktree", "add", "-q", str(d / "wt"))                    # from a worktree: settings still found
        r3 = backup(d / "wt", "wt", d / "out", date="2026-01-01", push=False)
        assert r3["untracked"] == ["settings.json"] and Path(r3["zip"]).name.startswith("master-config"), r3
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    ap.add_argument("--label", help="short kebab label for what is about to change, e.g. hooks, phase1-merge")
    ap.add_argument("--out", default=str(Path.home() / "Documents" / "Backups"))
    ap.add_argument("--extra", action="append", default=[], help="extra untracked file (relative to master) to include")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.label:
        ap.error("--label is required")
    r = backup(a.master, a.label, a.out, tuple(DEFAULT_EXTRAS) + tuple(a.extra), push=not a.no_push)
    print(f"tag  {r['tag']} at {r['head']}" + (" (already existed)" if r["tag_existed"] else "")
          + (" pushed" if r["pushed"] else ""))
    print(f"zip  {r['zip']}  ({r['files']} files, untracked: {', '.join(r['untracked']) or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

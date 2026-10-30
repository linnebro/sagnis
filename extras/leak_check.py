#!/usr/bin/env python3
"""Refuse to publish what you meant to keep. Stdlib only.

    python leak_check.py --terms ~/private-terms.txt                 # staged files (pre-commit)
    python leak_check.py --terms ~/private-terms.txt --tree          # every tracked file
    python leak_check.py --terms ~/private-terms.txt --range origin/main..HEAD   # every commit about to be pushed
    python leak_check.py --selftest

For a repo you publish that was built from a workspace you keep private. Two kinds of check:

1. Your terms, from a file kept OUTSIDE the published repo (a list of the names you
   keep private is itself private): one term per line, matched case-insensitively on
   word boundaries. `#` starts a comment. A line `!term` allows a term you reviewed
   and decided is generic.
2. Patterns that are personal whatever your list says: email addresses, phone
   numbers, home-folder paths (C:\\Users\\<name>, /home/<name>, /Users/<name>).
   example.com/.org/.net addresses and placeholder paths (<name>, you, me) pass.

Checks what would be published: the staged content of each file (not the working
copy), every tracked file with --tree, or every added line and commit message in a
range with --range (run it before a push: an old commit is published as much as the
newest). The commit author is not checked: it is your git config, public once pushed.
Exit 1 with one line per hit: file, line, what matched.

As a pre-commit hook in the published repo (local only; .git/hooks is never pushed):
    #!/bin/sh
    exec python extras/leak_check.py --terms "$HOME/private-terms.txt"
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EMAIL = re.compile(r"\b[\w.+-]+@(?:[\w-]+\.)+(?!(?:md|py|txt|jsonl?|ya?ml|toml|sh|js)\b)[a-z]{2,}\b", re.I)
EMAIL_OK = re.compile(r"@(example\.(com|org|net)|users\.noreply\.github\.com|anthropic\.com)$", re.I)
PHONE = re.compile(r"(?<![\w.-])(\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w-])")
HOME = re.compile(r"(?:[A-Za-z]:[\\/]+Users|/home|/Users)[\\/]+([\w.-]+)", re.I)
HOME_OK = {"you", "me", "name", "user", "username", "public", "runner", "default", "shared"}
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".xz", ".pyc", ".docx", ".xlsx", ".pptx"}


def load_terms(path):
    """-> (terms, allowed), lowercased. A missing file is an error, not an empty list."""
    terms, allowed = [], set()
    for line in Path(path).expanduser().read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("!"):
            allowed.add(line[1:].strip().lower())
        else:
            terms.append(line.lower())
    return [t for t in dict.fromkeys(terms) if t not in allowed], allowed


def term_pattern(terms):
    if not terms:
        return None
    alt = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alt})(?!\w)", re.I)


def scan_text(name, text, pat):
    """-> ['name:line: what matched']"""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        if pat:
            hits += [f"{name}:{n}: private term '{m.group(0)}'" for m in pat.finditer(line)]
        hits += [f"{name}:{n}: email address '{m.group(0)}'" for m in EMAIL.finditer(line)
                 if not EMAIL_OK.search(m.group(0))]
        hits += [f"{name}:{n}: phone number '{m.group(0).strip()}'" for m in PHONE.finditer(line)]
        hits += [f"{name}:{n}: home folder '{m.group(0)}'" for m in HOME.finditer(line)
                 if m.group(1).lower() not in HOME_OK]
    return hits


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.decode(errors='replace').strip()}")
    return r.stdout


def files_to_scan(repo, tree=False):
    """-> [(name, text)]: the staged blob of each staged file, or every tracked file with tree."""
    if tree:
        names = git(repo, "ls-files", "-z").decode().split("\0")
        read = lambda n: (Path(repo) / n).read_bytes()
    else:
        names = git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").decode().split("\0")
        read = lambda n: git(repo, "show", f":{n}")
    return [(n, "" if Path(n).suffix.lower() in BINARY else read(n).decode("utf-8", errors="replace"))
            for n in filter(None, names)]


def range_to_scan(repo, rng):
    """-> [(name@commit, text)]: each commit's message and the lines it added, for every commit in rng."""
    out = []
    # "A..B" or "B --not --remotes"; the trailing -- stops git checking the range as a file name
    # (that check fails when the working-tree path is very long)
    for c in git(repo, "rev-list", "--reverse", *rng.split(), "--").decode().split():
        out.append((f"message@{c[:7]}", git(repo, "show", "-s", "--format=%B", c).decode("utf-8", "replace")))
        diff = git(repo, "show", "--format=", "--unified=0", c).decode("utf-8", errors="replace")
        name, added = "?", {}
        for line in diff.splitlines():
            if line.startswith("+++ "):
                name = line[6:] if line.startswith("+++ b/") else line[4:]
            elif line.startswith("+"):
                added.setdefault(name, []).append(line[1:])
        out += [(f"{n}@{c[:7]}", "\n".join(v)) for n, v in added.items() if Path(n).suffix.lower() not in BINARY]
    return out


def check(items, terms):
    pat = term_pattern(terms)
    return [h for name, text in items for h in scan_text(name, text, pat)]


def selftest():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "terms.txt").write_text("# private\nAcme Patio\nJo Smith\nridgeline\n!ridgeline\n", encoding="utf-8")
        terms, allowed = load_terms(d / "terms.txt")
        assert terms == ["acme patio", "jo smith"] and allowed == {"ridgeline"}, (terms, allowed)
        # built at run time, so this file does not trip its own check when committed
        email, phone, home = "jo" + "@acmepatio.com", "612-555-" + "0142", "C:\\Users\\" + "jsmith"
        text = (f"Quote for ACME Patio.\nmail {email} or me@example.com\n"
                f"call {phone}, built 2026-10-30\n{home}\\x and C:\\Users\\<you>\\x\n"
                "Ridgeline and jo smithers\nlocalhost:8443 and v1.2.3-4567, f\"{n}@INDEX.md\"\n")
        hits = check([("a.md", text)], terms)
        assert hits == ["a.md:1: private term 'ACME Patio'",
                        f"a.md:2: email address '{email}'",
                        f"a.md:3: phone number '{phone}'",
                        f"a.md:4: home folder '{home}'"], hits
        repo = d / "r"
        repo.mkdir()
        git(repo, "init", "-q")
        commit = ("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q")
        (repo / "ok.md").write_text("nothing here\n", encoding="utf-8")
        (repo / "bad.md").write_text("Jo Smith\n", encoding="utf-8")
        git(repo, "add", "ok.md")
        assert check(files_to_scan(repo), terms) == []                        # unstaged bad.md is not scanned
        git(repo, "add", "bad.md")
        assert check(files_to_scan(repo), terms) == ["bad.md:1: private term 'Jo Smith'"]
        git(repo, *commit, "-m", "one")
        (repo / "bad.md").write_text("clean now\n", encoding="utf-8")
        git(repo, *commit, "-am", "two, for Acme Patio")
        assert check(files_to_scan(repo, tree=True), terms) == []             # the tree is clean...
        hits = check(range_to_scan(repo, "HEAD~1..HEAD"), terms)
        assert len(hits) == 1 and hits[0].startswith("message@") and "'Acme Patio'" in hits[0], hits   # ...the message is not
        root = git(repo, "rev-list", "--max-parents=0", "HEAD").decode().strip()
        assert any(h.startswith("bad.md@") for h in check(range_to_scan(repo, root), terms))           # nor is history
        assert len(range_to_scan(repo, "HEAD --not --remotes")) == 5    # 2 messages + 3 files; a new branch (pre-push): every unpublished commit
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--terms", help="your private term list, kept outside this repo")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--tree", action="store_true", help="every tracked file, not only what is staged")
    ap.add_argument("--range", help="every commit in a git range, e.g. origin/main..HEAD")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.terms:
        ap.error("--terms is required: without your list only the built-in patterns would run")
    terms, _ = load_terms(a.terms)
    items = range_to_scan(a.repo, a.range) if a.range else files_to_scan(a.repo, a.tree)
    hits = check(items, terms)
    for h in hits:
        print("leak: " + h, file=sys.stderr)
    if hits:
        print(f"leak: {len(hits)} hit(s); remove them, or allow a reviewed generic term with !term "
              "in your list. Never bypass with --no-verify.", file=sys.stderr)
    else:
        print(f"leak check ok: {len(items)} item(s), {len(terms)} private term(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())

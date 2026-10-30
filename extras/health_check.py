#!/usr/bin/env python3
"""Drift check: the backstop for rules that only a check keeps. Stdlib only, report-only.

    python health_check.py --master ~/.claude ~/Projects/acme ~/Projects/site
    python health_check.py --master ~/.claude --budget AGENTS.md,knowledge/MEMORY.md:2000
    python health_check.py ... --out ~/.claude/health/latest.txt      # SessionEnd hook
    python health_check.py --hint ~/.claude/health/latest.txt         # SessionStart hook: one line
    python health_check.py --master . --gate                          # pre-commit: repo-only checks
    python health_check.py --verify-approvals .git/COMMIT_EDITMSG --owner "Jo"   # commit-msg hook
    python health_check.py --review reviews/2026-10-30.md --owner "Jo"
    python health_check.py --selftest

Per repo: commits the remote has not seen (any branch), uncommitted changes, instruction
shims out of date (build_shims.py). For the master space (the folder holding your
AGENTS.md and the memory folder, default `<master>/knowledge`): facts that cannot be
indexed and stale generated indexes (sagnis.py build --check), task rosters behind their
initiatives (build_tasks.py), control characters in memory `.md` files, references in
them that resolve nowhere, the injected-context budgets you name, the audit trail
(never linked from a session-start file, never tracked by git, every chain intact:
audit.py), and more than five merged, clean worktrees waiting to be removed. Exit 1
when anything was found.

Why it exists: on the setup this came from, a check like this was retired as unread,
then restored after an audit found drift it would have caught (a control character
from a mangled escape, dead links, a stale index). Run it from the SessionEnd hook and
print one line at the next SessionStart (--hint), so it is read.

sagnis.py, build_shims.py, build_tasks.py and audit.py are used when they sit beside
this file or in ../core/; a check whose script is absent is skipped.
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "core"):
    if str(p) not in sys.path:
        sys.path.append(str(p))


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def optional(name):
    try:
        return __import__(name)
    except ImportError:
        return None


def check_repo(repo):
    repo = Path(repo).expanduser()
    if not (repo / ".git").exists():
        return [f"{repo}: not a git repo"]
    out = []
    unpushed = git(repo, "log", "--branches", "--not", "--remotes", "--oneline")
    if unpushed:
        out.append(f"{repo.name}: {len(unpushed.splitlines())} commit(s) the remote has not seen (any branch)")
    dirty = git(repo, "status", "--porcelain")
    if dirty:
        out.append(f"{repo.name}: {len(dirty.splitlines())} uncommitted/untracked path(s)")
    shims = optional("build_shims")
    if shims and (repo / "AGENTS.md").is_file():
        out += [f"instruction shim {st}: {p}" for p, st in shims.check(repo, ["claude"])]
    return out


def check_memory(master, memory):
    """Facts indexable, generated files current, task rosters current."""
    sagnis = optional("sagnis")
    if not sagnis:
        return ["sagnis.py not found beside health_check.py or in ../core/"]
    changed, problems, warns = sagnis.build(str(memory), check=True)
    out = [f"fact not indexable: {p}" for p in problems]
    out += [f"generated file stale, run sagnis.py build --root {memory.name}: {p}" for p in changed]
    out += warns
    tasks = optional("build_tasks")
    if tasks:
        dates = tasks.b.git_dates(memory)
        for idir in sorted(memory.glob("*/initiatives")):
            topic, today = idir.parent, dt.date.today().isoformat()
            d = {k[len(topic.name) + 1:]: v for k, v in dates.items() if k.startswith(topic.name + "/")}
            stale = tasks.check(topic, tasks.render(topic, topic.name, d, today=today),
                                tasks.render_status(topic, today, d))
            out += [f"generated file stale, run build_tasks.py --topic {memory.name}/{topic.name}: {n}" for n in stale]
            out += tasks.lint(topic)
    return out


LINK = re.compile(r"\]\(([^)#\s]+\.md)\)|`([\w./\\-]+\.md)`")
FACT_NAME = re.compile(r"^(user|project|feedback|reference)_[\w-]+\.md$")
HISTORY = {"notes", "initiatives", "archive"}      # dated records: they may name retired files


def check_text(master, memory, extra_roots=()):
    """Control characters in any memory .md file, and references a session follows that resolve
    nowhere: every markdown link, every backticked path, every backticked fact name, tried against
    the file's folder, its topic, the memory root, the master, each extra root and each repo nested
    one or two levels inside one (two: a repo in a plain grouping folder). History folders are
    exempt (dated records), and so are generated files (checked against their generator)."""
    roots = [memory, Path(master)]
    for r in (Path(x).expanduser() for x in extra_roots):
        kids = [k for k in r.iterdir() if k.is_dir() and not k.is_symlink() and not k.name.startswith(".")]
        roots += [r] + [k for k in kids if (k / ".git").exists()] + \
            [g for k in kids if not (k / ".git").exists() for g in k.iterdir() if g.is_dir() and (g / ".git").exists()]
    facts = {p.name for p in memory.rglob("*.md") if FACT_NAME.match(p.name)}
    out = []
    for p in sorted(list(memory.rglob("*.md")) + [Path(master) / "AGENTS.md"]):
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = p.relative_to(master).as_posix() if p.is_relative_to(master) else p.as_posix()
        bad = sorted({f"U+{ord(c):04X}" for c in text if ord(c) < 32 and c not in "\t\n\r"})
        if bad:
            out.append(f"{rel}: control character(s) {', '.join(bad)}")
        inside = p.relative_to(memory).parts if p.is_relative_to(memory) else ()
        if text.startswith("<!-- generated by ") or HISTORY & set(inside[:-1]):
            continue
        topic = memory / inside[0] if len(inside) > 1 else memory
        for m in LINK.finditer(text):
            ref = (m.group(1) or m.group(2)).replace("\\", "/")
            if "<" in ref or "*" in ref or ref.startswith(("http", "~")):
                continue
            if m.group(2) and "/" not in ref and not FACT_NAME.match(ref):
                continue                       # a bare name in prose (README.md): a mention, not a path
            if FACT_NAME.match(ref) and ref in facts:
                continue
            if not any((h / ref).exists() for h in [p.parent, topic] + roots):
                out.append(f"{rel}: reference '{ref}' resolves nowhere")
    return out


def check_budgets(master, budgets):
    """budgets: ['AGENTS.md,knowledge/MEMORY.md:2000', ...], paths relative to master."""
    sagnis = optional("sagnis")
    if not sagnis:
        return []
    out = []
    for spec in budgets:
        files, _, cap = spec.rpartition(":")
        paths = [str(Path(master) / f.strip()) for f in files.split(",") if f.strip()]
        total = sum(t or 0 for _, t in sagnis.budget(paths))
        if total > int(cap):
            out.append(f"context budget: {files} loads {total:,} tokens at start, guide {int(cap):,} "
                       "(move a line down a tier; never trim content to clear it)")
    return out


def check_audit(master, memory):
    """The audit trail is written on every action and never loaded: no session-start file links
    into audit/, git does not track it, every chain and archived day verifies."""
    master = Path(master)
    if not (master / "audit").is_dir():
        return []
    out = []
    for f in [master / "CLAUDE.md", master / "AGENTS.md", memory / "MEMORY.md", memory / "INDEX.md"] \
            + sorted(memory.glob("*/INDEX.md")):
        if f.is_file() and re.search(r"\]\([^)]*\baudit/", f.read_text(encoding="utf-8")):
            out.append(f"audit trail linked from a session-start file: {f.name}")
    if git(master, "ls-files", "audit"):
        out.append("audit trail is tracked by git; it must stay ignored")
    audit = optional("audit")
    if audit:
        out += [f"audit trail: {p}" for p in audit.verify(master, legacy=[])[0]]   # legacy: known torn lines, kept apart
        if git(master, "status", "--porcelain", "--", audit.MANIFEST):
            out.append(f"{audit.MANIFEST} has uncommitted lines: commit it (it is the tamper evidence)")
    return out


def check_worktrees(repo, keep=5):
    """Worktrees whose branch is already in origin/main and that have nothing uncommitted:
    safe to remove, listed when more than `keep`, never removed here."""
    lines = git(repo, "worktree", "list", "--porcelain").splitlines()
    paths = [l[9:] for l in lines if l.startswith("worktree ")][1:]           # the first is the main checkout
    done = [w for w in paths if not git(w, "status", "--porcelain")
            and subprocess.run(["git", "-C", w, "merge-base", "--is-ancestor", "HEAD", "origin/main"],
                               capture_output=True).returncode == 0]
    return [f"{Path(repo).name}: {len(done)} of {len(paths)} worktrees are merged and clean; "
            f"remove with git worktree remove (first: {Path(done[0]).name})"] if len(done) > keep else []


def approved_re(owner):
    return re.compile(rf'^Approved-by:\s*{re.escape(owner)}\s*\(\s*([\w-]+)\s*,\s*([^,]+?)\s*,\s*"(.+)"\s*\)\s*$', re.M)


def verify_approvals(msg_file, owner, transcripts):
    """commit-msg hook. Each `Approved-by: <owner> (<session id>, <time>, "<their words>")` trailer
    must quote words found in a user message of that session's transcript (Claude Code writes
    them as <transcripts>/*/<session id>.jsonl; the harness writes them, not the model). An
    approval claimed in prose without a trailer is reported, not refused."""
    text = Path(msg_file).read_text(encoding="utf-8", errors="replace")
    bad = []
    for sid, _, quote in approved_re(owner).findall(text):
        want = " ".join(quote.split()).lower()
        found = False
        for tr in Path(transcripts).expanduser().glob(f"*/{sid}.jsonl"):
            for line in tr.open(encoding="utf-8", errors="replace"):
                if '"type":"user"' not in line.replace(" ", ""):
                    continue
                try:
                    c = json.loads(line).get("message", {}).get("content")
                except json.JSONDecodeError:
                    continue
                said = c if isinstance(c, str) else " ".join(
                    x.get("text", "") for x in c or [] if isinstance(x, dict) and x.get("type") == "text")
                if want in " ".join(said.split()).lower():
                    found = True
                    break
            if found:
                break
        if not found:
            bad.append(f'Approved-by quote not found in a user message of session {sid}: "{quote[:80]}"')
    for b in bad:
        print("commit-msg: " + b, file=sys.stderr)
    claim = re.compile(rf"{re.escape(owner)}'?s OK|approved by {re.escape(owner)}|{re.escape(owner)} approved", re.I)
    if not approved_re(owner).search(text) and claim.search(text):
        print(f"commit-msg: the message claims {owner}'s approval; record it as an Approved-by trailer "
              "quoting their message. Not refused.", file=sys.stderr)
    return 1 if bad else 0


def field(text, key):
    m = re.search(rf"^{key}:\s*\"?([^\"\n]+)\"?\s*$", text[:600], re.M) if text.startswith("---") else None
    return m.group(1).strip() if m else None


def check_review(path, owner):
    """A review record (REVIEW.md) may say `verdict: pass` only when no critical or high finding
    is open and every accepted one quotes the owner. Returns the problems."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    verdict = field(text, "verdict")
    out = [] if verdict in ("pass", "fail") else [f"{path}: verdict must be pass or fail, not {verdict!r}"]
    for key in ("reviewed", "criteria", "reviewer", "checks"):
        v = field(text, key)
        if not v or v.startswith("<"):
            out.append(f"{path}: `{key}` is not filled in")
    rows = re.findall(r"^\|\s*([A-Z]+-\d+)\s*\|\s*(\w+)\s*\|.*\|\s*([^|]+?)\s*\|\s*$", text, re.M)
    for rid, sev, status in rows:
        if status.startswith("accepted") and not re.search(rf'by {re.escape(owner)} \(".+"\)', status):
            out.append(f"{path}: {rid} is accepted without {owner}'s quoted words")
        elif sev.lower() in ("critical", "high") and status == "open" and verdict == "pass":
            out.append(f"{path}: verdict pass with {sev} finding {rid} open")
    return out


def hint(digest):
    """One line, never the content: the next session is told the last check found something."""
    try:
        lines = Path(digest).expanduser().read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    n = sum(1 for l in lines if l.startswith("- ") and l != "- nothing to report")
    if n:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
              f"Health check ({lines[0][13:]}): {n} drift finding(s) in {digest}. Read it when the task touches "
              "memory, a repo it names or the end-of-session commit; fix what this session caused."}}))
    return 0


def selftest():
    sagnis = optional("sagnis")
    assert sagnis, "selftest needs sagnis.py beside this file or in ../core/"
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        know = d / "knowledge"
        (know / "general").mkdir(parents=True)
        (know / "general" / "feedback_a.md").write_text(
            '---\ntitle: "A"\ndescription: "a"\nsource: "s"\nupdated: 2020-01-01\n---\nA.\n', encoding="utf-8")
        (know / "general" / "feedback_b.md").write_text("x", encoding="utf-8")
        (know / "MEMORY.md").write_text("# Routes\n- general: a\n", encoding="utf-8")
        found = check_memory(d, know)
        assert any(f.startswith("fact not indexable: general") and "feedback_b.md" in f for f in found), found
        assert any("generated file stale" in f and "INDEX.md" in f for f in found), found
        assert check_repo(d) == [f"{d}: not a git repo"]
        # control characters and dead references; history folders and prose mentions are exempt
        (know / "general" / "RULES.md").write_text("see `general\x0ceedback_a.md` and `general/feedback_a.md`, "
                                                   "`README.md`, [gone](project_gone.md)\n", encoding="utf-8")
        (know / "general" / "notes").mkdir()
        (know / "general" / "notes" / "old.md").write_text("`general/retired.md`\n", encoding="utf-8")
        found = check_text(d, know)
        assert "knowledge/general/RULES.md: control character(s) U+000C" in found, found
        assert "knowledge/general/RULES.md: reference 'project_gone.md' resolves nowhere" in found, found
        assert not any("feedback_a" in f or "README" in f or "retired" in f for f in found), found
        # budgets: the injected set over its guide is reported
        (d / "AGENTS.md").write_text("x" * 4000 + "\n@knowledge/MEMORY.md\n", encoding="utf-8")
        assert check_budgets(d, ["AGENTS.md:2000"]) == []
        assert check_budgets(d, ["AGENTS.md:500"])[0].startswith("context budget: AGENTS.md loads 1,")
        # the audit trail is never linked from a session-start file
        (d / "audit").mkdir()
        (know / "MEMORY.md").write_text("# Routes\n- general: a, see [trail](../audit/x.jsonl)\n", encoding="utf-8")
        assert "audit trail linked from a session-start file: MEMORY.md" in check_audit(d, know)
        # approvals: a trailer must quote a user message of that session's transcript
        proj = d / "projects" / "p"
        proj.mkdir(parents=True)
        (proj / "s1.jsonl").write_text('{"type":"user","message":{"content":"yes,  merge it to main"}}\n'
                                       '{"type":"assistant","message":{"content":"I approve"}}\n', encoding="utf-8")
        msg = d / "msg"
        msg.write_text('x\n\nApproved-by: Jo (s1, 2026-10-16T10:00, "Yes, merge it to main")\n', encoding="utf-8")
        assert verify_approvals(msg, "Jo", d / "projects") == 0
        msg.write_text('x\n\nApproved-by: Jo (s1, 2026-10-16T10:00, "I approve")\n', encoding="utf-8")
        assert verify_approvals(msg, "Jo", d / "projects") == 1          # the model's own words are not theirs
        # a review cannot pass with a high finding open, or one accepted without the owner's words
        rv = d / "review.md"
        head = ('---\nreviewed: "x 1..2"\ncriteria: "spec"\nreviewer: "s, 2026-10-16"\n'
                'checks: "tests pass"\nverdict: pass\n---\n')
        rv.write_text(head + "| R-1 | high | bad | open |\n| R-2 | low | meh | open |\n", encoding="utf-8")
        assert check_review(rv, "Jo") == [f"{rv}: verdict pass with high finding R-1 open"], check_review(rv, "Jo")
        rv.write_text(head + "| R-1 | high | bad | accepted by Jo |\n", encoding="utf-8")
        assert "without Jo's quoted words" in check_review(rv, "Jo")[0]
        rv.write_text(head + '| R-1 | high | bad | fixed abc123 |\n| R-2 | medium | x | accepted by Jo ("ship it") |\n',
                      encoding="utf-8")
        assert check_review(rv, "Jo") == []
        # the SessionStart hint is one line, and silent when the digest is clean
        dg = d / "latest.txt"
        dg.write_text("health check 2026-10-30T09:00\n- a\n- b\n", encoding="utf-8")
        assert hint(dg) == 0
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="*", help="project repos to check")
    ap.add_argument("--master", help="the folder holding your AGENTS.md and memory folder (e.g. ~/.claude)")
    ap.add_argument("--memory", help="memory folder (default <master>/knowledge)")
    ap.add_argument("--budget", action="append", default=[], metavar="FILES:N",
                    help="comma-separated files relative to master, then the token guide, e.g. AGENTS.md,knowledge/MEMORY.md:2000")
    ap.add_argument("--owner", help="the name in Approved-by trailers and review records")
    ap.add_argument("--transcripts", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--out", help="also write the digest here (the SessionEnd hook)")
    ap.add_argument("--hint", metavar="DIGEST", help="SessionStart hook: one line of context when DIGEST has findings")
    ap.add_argument("--gate", action="store_true", help="commit gate: repo-only checks, exit 1 on any finding")
    ap.add_argument("--verify-approvals", metavar="MSG_FILE", help="commit-msg hook: check Approved-by quotes")
    ap.add_argument("--review", metavar="FILE", help="check a review record before reporting work as reviewed")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.hint:
        return hint(a.hint)
    if (a.verify_approvals or a.review) and not a.owner:
        ap.error("--owner is required with --verify-approvals and --review")
    if a.verify_approvals:
        return verify_approvals(a.verify_approvals, a.owner, a.transcripts)
    if a.review:
        found = check_review(a.review, a.owner)
        print("\n".join(found) or "review record ok")
        return 1 if found else 0
    if not a.master and not a.repos:
        ap.error("give --master, one or more repos, or both")
    master = Path(a.master).expanduser().resolve() if a.master else None
    memory = Path(a.memory).expanduser().resolve() if a.memory else (master / "knowledge" if master else None)
    if a.gate:
        found = check_memory(master, memory) + check_text(master, memory) + check_budgets(master, a.budget)
        for f in found:
            print("gate: " + f, file=sys.stderr)
        if found:
            print("gate: commit refused; fix the above, never bypass with --no-verify", file=sys.stderr)
        return 1 if found else 0
    findings = []
    if master:
        if not memory.is_dir():
            ap.error(f"no memory folder at {memory}; pass --memory")
        findings += check_memory(master, memory) + check_text(master, memory, a.repos)
        findings += check_budgets(master, a.budget) + check_audit(master, memory)
        findings += check_repo(master) + check_worktrees(master)
    for r in a.repos:
        findings += check_repo(r) + check_worktrees(Path(r).expanduser())
    findings = list(dict.fromkeys(findings))
    text = f"health check {dt.datetime.now().isoformat(timespec='minutes')}\n" + \
        ("\n".join(f"- {f}" for f in findings) if findings else "- nothing to report")
    print(text)
    if a.out:
        Path(a.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).expanduser().write_text(text + "\n", encoding="utf-8")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

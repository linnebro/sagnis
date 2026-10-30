#!/usr/bin/env python3
"""Generate a topic's task roster (TASKS.md) from its initiative notes. Stdlib only.

    python build_tasks.py --topic ~/.claude/knowledge/acme            # regenerate
    python build_tasks.py --topic ~/.claude/knowledge/acme --check    # exit 1 on drift
    python build_tasks.py --topic <dir> --migrate ~/Projects/Acme/TASKS.md
    python build_tasks.py --selftest

health_check.py runs its --check for every topic that has an `initiatives/` folder.

Source of truth (hand-maintained, one file per initiative, never per folder):

  knowledge/<topic>/initiatives/<slug>.md
      ---
      title: Acme Patio
      ---
      ## <task title>
      - area: Acme Patio / Pricing        (optional, the finer label)
      - when: Before Oct 12               (free text)
      - status: Not started               (free text, the current state)
      - done: 2026-09-11                  (optional; present = closed, kept for the record)

      <the task's detail, whole: history, commands, identifiers>

  knowledge/<topic>/initiatives/_rules.md   optional; its body opens the roster verbatim
                                            (standing priorities, call days, the like)
  `- priority: N` and `- next: ...` on a task put it in status.md (a one-page handoff
  for a chat or voice assistant that cannot read the repo), in priority order, followed
  by initiatives/_handoff.md verbatim (standing context: pricing, lower-priority lines).

Output, stamped with a generated-file header:

  knowledge/<topic>/TASKS.md   standing rules, Recent (initiatives by git commit date),
                               every open task as one table row per initiative
                               (title -> initiative file, area, when, status), then Done

The detail never appears in the roster: it is one hop down, whole. Closing a task is
adding `- done: <date>`; nothing is deleted.

--migrate splits a legacy single-table TASKS.md (| Task | <initiative> | Due | Status |)
into initiative files: the initiative is the first segment of the second column
("Organization / Suppliers" -> Organization, area "Organization / Suppliers"); each row's
title is its bold lead or first clause; the whole cell becomes the detail. Text between
the H1 and the table becomes `_rules.md`. Run it once, review the titles, regenerate.
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path

import subprocess


class b:
    """Frontmatter and git-date helpers, formerly imported from the retired build_index.py."""

    @staticmethod
    def split_frontmatter(text):
        m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
        return (None, text) if not m else (m.group(1).splitlines(), text[m.end():])

    @staticmethod
    def parse_frontmatter(lines):
        d = {}
        for line in lines or []:
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if m:
                d[m.group(1)] = m.group(2).strip().strip('"')
        return d

    @staticmethod
    def yaml_quote(v):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'

    @staticmethod
    def git_dates(know):
        """rel path (posix, relative to know) -> last commit date; a file with uncommitted changes -> today,
        so a roster generated before its sources are committed is still right after the commit."""
        import datetime as dt
        import os
        # inside a git hook GIT_INDEX_FILE and its kin are set relative to the repo root; cwd here is not it
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        try:
            top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=know, env=env, capture_output=True,
                                 text=True, encoding="utf-8", check=True).stdout.strip()
            log = subprocess.run(["git", "log", "--format=%cs", "--name-only", "--", "."], cwd=know, env=env,
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
            dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", "."], cwd=know, env=env,
                                   capture_output=True, text=True, encoding="utf-8", check=True).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {}
        prefix = Path(know).resolve().relative_to(Path(top).resolve()).as_posix()
        prefix = "" if prefix == "." else prefix + "/"
        dates, date = {}, None
        for line in log.splitlines():
            if re.match(r"^\d{4}-\d{2}-\d{2}$", line):
                date = line
            elif line.strip() and line.startswith(prefix):
                dates.setdefault(line[len(prefix):], date)
        today = dt.date.today().isoformat()
        for line in dirty.splitlines():
            path = line[3:].split(" -> ")[-1].strip('"')
            if path.startswith(prefix):
                dates[path[len(prefix):]] = today
        return dates

HEADER = ("<!-- generated by build_tasks.py from initiatives/*.md; edit the initiative file, "
          "then regenerate. Hand edits are overwritten. -->")
FIELDS = ("area", "when", "status", "done", "updated", "priority", "next")
FIELD_RE = re.compile(r"^- (%s):\s*(.*)$" % "|".join(FIELDS))
N_RECENT = 5


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-") or "initiative"


# ------------------------------------------------------------------ loading
def load(topic_dir):
    """-> (rules_text, [initiative dicts]) ; each initiative: title, file, tasks[]"""
    idir = Path(topic_dir) / "initiatives"
    rules, inits = "", []
    if not idir.is_dir():
        return rules, inits
    for p in sorted(idir.glob("*.md")):
        fm, body = b.split_frontmatter(p.read_text(encoding="utf-8"))
        if p.name == "_rules.md":
            rules = body.strip()
            continue
        meta = b.parse_frontmatter(fm)
        tasks = []
        for block in re.split(r"^## ", body, flags=re.M)[1:]:
            title, _, rest = block.partition("\n")
            t, detail, in_fields = {"title": title.strip()}, [], True
            for line in rest.splitlines():
                m = FIELD_RE.match(line) if in_fields else None
                if m:
                    t[m.group(1)] = m.group(2).strip()
                elif in_fields and not line.strip():
                    continue
                else:
                    in_fields = False
                    detail.append(line)
            t["detail"] = "\n".join(detail).strip()
            tasks.append(t)
        inits.append({"title": meta.get("title", p.stem), "file": p.name, "tasks": tasks})
    return rules, inits


# ---------------------------------------------------------------- rendering
def cell(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")


def area_cell(area, initiative):
    """The area minus the initiative it repeats ("Cold Outreach — DIB" under Cold Outreach -> "DIB")."""
    a = area or ""
    if a.lower().startswith(initiative.lower()):
        a = re.sub(r"^\s*[/—–-]\s*", "", a[len(initiative):])
    return a


def render(topic_dir, topic_title, dates=None, today=None):
    """dates: {relpath under topic_dir: last commit date} (git); uncommitted -> today."""
    rules, inits = load(topic_dir)
    dates = dates or {}
    n_open = sum(1 for i in inits for t in i["tasks"] if not t.get("done"))
    n_done = sum(1 for i in inits for t in i["tasks"] if t.get("done"))
    L = [HEADER, "", f"# Tasks — {topic_title}", "",
         "Generated roster: one row per task, detail one hop down in the initiative file.",
         "Change a task in its initiative file, then regenerate. Close one with `- done: <date>`.", ""]
    if rules:
        L += ["## Standing rules", "", rules, ""]
    L += [f"## Recent — initiatives touched (git commit date), last {N_RECENT}", ""]
    stamped = sorted(inits, key=lambda i: (dates.get(f"initiatives/{i['file']}") or today or "9999", i["file"]),
                     reverse=True)
    for i in stamped[:N_RECENT]:
        d = dates.get(f"initiatives/{i['file']}") or today or "uncommitted"
        o = sum(1 for t in i["tasks"] if not t.get("done"))
        L.append(f"- {d} [{i['title']}](initiatives/{i['file']}) — {o} open")
    L += ["", f"## Open — {n_open} tasks in {len(inits)} initiatives", ""]
    for i in inits:
        open_tasks = [t for t in i["tasks"] if not t.get("done")]
        if not open_tasks:
            continue
        L += [f"### {i['title']} — [initiatives/{i['file']}](initiatives/{i['file']})", "",
              "| Task | Area | When | Status |", "|---|---|---|---|"]
        for t in open_tasks:
            L.append(f"| {cell(t['title'])} | {cell(area_cell(t.get('area'), i['title']))} | {cell(t.get('when'))} | {cell(t.get('status'))} |")
        L.append("")
    if n_done:
        L += [f"## Done — {n_done}, kept for the record", "", "| Task | Initiative | Done |", "|---|---|---|"]
        for i in inits:
            for t in i["tasks"]:
                if t.get("done"):
                    L.append(f"| {cell(t['title'])} | [{i['title']}](initiatives/{i['file']}) | {cell(t['done'])} |")
        L.append("")
    return "\n".join(L)


STATUS_HEADER = "<!-- generated by build_tasks.py from initiatives/*.md (priority, status, next) and initiatives/_handoff.md; edit those, then regenerate. -->"


def render_status(topic_dir, today, dates=None):
    """status.md, the one-page handoff: open tasks carrying `- priority: N`, in order, then _handoff.md verbatim.
    Stamped with the newest commit date of its sources (today when one is uncommitted), not the
    run date, so the same sources always give the same file and a copy's age is readable from it."""
    _, inits = load(topic_dir)
    top = sorted(((int(t["priority"]), t, i) for i in inits for t in i["tasks"]
                  if t.get("priority", "").isdigit() and not t.get("done")), key=lambda r: r[0])
    srcs = [f"initiatives/{i['file']}" for i in inits] + ["initiatives/_handoff.md"]
    dates = dates or {}
    stamp = max((dates.get(s) or today) for s in srcs) if dates else today
    L = [STATUS_HEADER, "", "# Status: top tasks", "",
         f"Generated from `{Path(topic_dir).name}/initiatives/`; sources last changed {stamp}. "
         f"Edit the initiatives, never this file.", ""]
    for n, (_, t, i) in enumerate(top, 1):
        L += [f"## {n}. {t['title']} ({i['title']})",
              f"- **Where:** {t.get('status', '')}"]
        if t.get("when"):
            L.append(f"- **When:** {t['when']}")
        if t.get("next"):
            L.append(f"- **Next:** {t['next']}")
        L.append("")
    hand = Path(topic_dir) / "initiatives" / "_handoff.md"
    if hand.is_file():
        L += [b.split_frontmatter(hand.read_text(encoding="utf-8"))[1].strip(), ""]
    return "\n".join(L)


def summary(topic_dir):
    """-> (open, done, initiatives) for the topic index's one-line pointer."""
    _, inits = load(topic_dir)
    return (sum(1 for i in inits for t in i["tasks"] if not t.get("done")),
            sum(1 for i in inits for t in i["tasks"] if t.get("done")), len(inits))


# ---------------------------------------------------------------- migration
ROW_RE = re.compile(r"^\|\s*(.*?)\s*\|\s*$")


def derive_title(text, limit=90):
    m = re.match(r"\s*\*\*(.+?)\*\*", text)
    t = m.group(1) if m else re.split(r"(?<=[.;:])\s|\s—\s", text, 1)[0]
    t = re.sub(r"\s+", " ", t).strip(" .:;—-")
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0].rstrip(" ,;:") + " …"
    return t


def initiative_of(label):
    return re.split(r"\s+[/—–-]\s+", label, 1)[0].strip() or label


def migrate(tasks_md, topic_dir):
    """Legacy | Task | Initiative | Due | Status | table -> initiatives/*.md. Returns files written."""
    idir = Path(topic_dir) / "initiatives"
    idir.mkdir(parents=True, exist_ok=True)
    lines = Path(tasks_md).read_text(encoding="utf-8").splitlines()
    pre, groups, order = [], {}, []
    for line in lines:
        if line.startswith("|"):
            if re.match(r"^\|\s*-{2,}", line) or re.match(r"^\|\s*Task\s*\|", line, re.I):
                continue
            cells = [c.strip() for c in ROW_RE.match(line).group(1).split(" | ")]
            if len(cells) < 4:
                continue
            task, label, when, status = " | ".join(cells[:-3]), cells[-3], cells[-2], cells[-1]
            init = initiative_of(label)
            if init not in groups:
                groups[init], order = [], order + [init]
            groups[init].append((derive_title(task), label, when, status, task))
        elif not groups and not line.startswith("#"):
            pre.append(line)
    written = []
    rules = "\n".join(pre).strip()
    if rules:
        (idir / "_rules.md").write_text("---\ntitle: Standing rules\n---\n\n" + rules + "\n",
                                        encoding="utf-8", newline="\n")
        written.append("_rules.md")
    for init in order:
        L = ["---", f"title: {b.yaml_quote(init)}", "---", "", f"# {init}", ""]
        for title, label, when, status, task in groups[init]:
            L += [f"## {title}", f"- area: {label}", f"- when: {when}", f"- status: {status}", "", task, ""]
        name = slug(init) + ".md"
        (idir / name).write_text("\n".join(L), encoding="utf-8", newline="\n")
        written.append(name)
    return written


# ------------------------------------------------------------------ checks
STATUS_CAP = 600       # characters: `status` and `next` are where a task stands, not its history


def lint(topic_dir):
    """A task whose `status` or `next` outgrew STATUS_CAP: the history belongs in the task's
    detail or notes/, the field keeps the current state (it is copied into TASKS.md and status.md)."""
    out = []
    for i in load(topic_dir)[1]:
        for t in i["tasks"]:
            for f in ("status", "next"):
                if not t.get("done") and len(t.get(f, "")) > STATUS_CAP:
                    out.append(f"{Path(topic_dir).name}/initiatives/{i['file']}: '{t['title'][:50]}' {f} is "
                               f"{len(t[f]):,} characters (cap {STATUS_CAP}); move the history below the fields")
    return out


def check(topic_dir, text, status=None):
    out = []
    for name, want in (("TASKS.md", text), ("status.md", status)):
        p = Path(topic_dir) / name
        if want is not None and not (p.is_file() and p.read_text(encoding="utf-8") == want):
            out.append(name)
    return out


def selftest():
    with tempfile.TemporaryDirectory() as d:
        topic = Path(d) / "acme"
        (topic / "initiatives").mkdir(parents=True)
        (topic / "initiatives" / "_rules.md").write_text("---\ntitle: Standing rules\n---\n\nCalls Mon/Tue.\n", encoding="utf-8")
        (topic / "initiatives" / "acme.md").write_text(
            "---\ntitle: Acme\n---\n\n# Acme\n\n## Bind insurance | before kickoff\n- area: Acme / Insurance\n- when: Before Oct 12\n"
            "- status: Quoted\n\nBroker quote 9/2.\n`stripe fixtures x.json`\n\n## Old thing\n- when: Aug\n- status: Done\n- done: 2026-08-30\n\nwas done\n",
            encoding="utf-8")
        (topic / "initiatives" / "org.md").write_text(
            "---\ntitle: Org\n---\n\n## Renew the domain\n- when: Nov\n- status: Not started\n", encoding="utf-8")
        rules, inits = load(topic)
        assert rules == "Calls Mon/Tue." and [i["title"] for i in inits] == ["Acme", "Org"], inits
        t = inits[0]["tasks"][0]
        assert t["title"] == "Bind insurance | before kickoff" and t["area"] == "Acme / Insurance" and t["status"] == "Quoted"
        assert t["detail"] == "Broker quote 9/2.\n`stripe fixtures x.json`", t["detail"]     # whole, fields stripped
        assert inits[0]["tasks"][1]["done"] == "2026-08-30"
        assert summary(topic) == (2, 1, 2)
        out = render(topic, "Acme", {"initiatives/acme.md": "2026-09-02"}, today="2026-09-18")
        assert out.startswith(HEADER) and "## Standing rules\n\nCalls Mon/Tue." in out
        assert out.index("- 2026-09-18 [Org](initiatives/org.md) — 1 open") < out.index("- 2026-09-02 [Acme]")  # uncommitted first
        assert "## Open — 2 tasks in 2 initiatives" in out
        assert "| Bind insurance \\| before kickoff | Insurance | Before Oct 12 | Quoted |" in out, out   # area minus the initiative
        assert area_cell("Organization / Suppliers", "Organization") == "Suppliers" and area_cell("Other", "Org") == "Other"
        assert "Broker quote" not in out                                    # detail stays one hop down
        assert "| Old thing | [Acme](initiatives/acme.md) | 2026-08-30 |" in out
        assert check(topic, out) == ["TASKS.md"]
        (topic / "TASKS.md").write_text(out, encoding="utf-8", newline="\n")
        assert check(topic, out) == []
        # migrate a legacy table
        legacy = Path(d) / "TASKS.md"
        legacy.write_text("# Acme — Active Tasks\n\n**Standing rules:** Acme first.\n\n| Task | Client | Due | Status |\n|---|---|---|---|\n"
                          "| **Supplier lunch — Fri 9/11.** Bring the price list | Organization / Suppliers | Fri 9/11 | Set 9/8 |\n"
                          "| Call Hollis about the patio; they want it before frost. Log it | Spring Cleanups — Mailers | Whenever | Awaiting callback |\n"
                          "| Second org task | Organization | Nov | Not started |\n", encoding="utf-8")
        topic2 = Path(d) / "acme2"
        written = migrate(legacy, topic2)
        assert written == ["_rules.md", "organization.md", "spring-cleanups.md"], written
        rules, inits = load(topic2)
        assert rules == "**Standing rules:** Acme first."
        org = next(i for i in inits if i["title"] == "Organization")
        assert [t["title"] for t in org["tasks"]] == ["Supplier lunch — Fri 9/11", "Second org task"], org
        assert org["tasks"][0]["area"] == "Organization / Suppliers" and org["tasks"][0]["detail"].startswith("**Supplier")
        co = next(i for i in inits if i["title"] == "Spring Cleanups")
        assert co["tasks"][0]["title"] in ("Call Hollis about the patio;", "Call Hollis about the patio"), co
        assert derive_title("x" * 200).endswith(" …") and len(derive_title("x " * 100)) <= 92
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--topic", help="knowledge/<topic> folder holding initiatives/")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--migrate", metavar="TASKS_MD", help="one-time: split a legacy table into initiatives/")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.topic:
        ap.error("--topic is required")
    topic = Path(a.topic).expanduser()
    if a.migrate:
        for name in migrate(a.migrate, topic):
            print(f"wrote initiatives/{name}")
        return 0
    know = topic.parent
    dates = {k[len(topic.name) + 1:]: v for k, v in b.git_dates(know).items() if k.startswith(topic.name + "/")}
    import datetime as dt
    text = render(topic, topic.name, dates, today=dt.date.today().isoformat())
    status = render_status(topic, dt.date.today().isoformat(), dates)
    if a.check:
        drift = check(topic, text, status)
        print("TASKS.md and status.md match initiatives" if not drift else f"stale: {', '.join(drift)}; run without --check")
        return 1 if drift else 0
    (topic / "TASKS.md").write_text(text, encoding="utf-8", newline="\n")
    (topic / "status.md").write_text(status, encoding="utf-8", newline="\n")
    print(f"wrote TASKS.md  ({len(text):,} chars, ~{len(text)//4:,} tok)")
    print(f"wrote status.md ({len(status):,} chars, ~{len(status)//4:,} tok))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

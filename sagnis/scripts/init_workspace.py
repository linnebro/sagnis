#!/usr/bin/env python3
"""Scaffold the master space and one project repo from templates/. Stdlib only.

    python init_workspace.py --master ~/.claude --project ~/Projects/Acme --name Acme \
        --owner "Jane Doe" --description "invoicing for trades" [--tier 1|2] [--tool claude|codex] \
        [--data-folders "Customers,Contracts"]

Two tiers, each useful alone; the default is 1 and a rerun with --tier 2
--tier adds the next layer without touching what exists:

  1  memory and routing   global AGENTS.md, knowledge/ with a TOPIC.md per topic, the
                          generated MEMORY.md + topic indexes + journal, one mirror index
                          of the project root, and a two-line shim in the project repo
  2  state and guardrails + RULES.md (read order, rules that have bitten), LOG.md, the
                          first initiative file, the generated TASKS.md roster, and the rule
                          that repeatable work becomes a script rather than an agent

Hand-written files are never overwritten; each is reported as "kept". The
generated ones are rebuilt from their sources on every run by build_index.py.
Run again with a new --project/--name to add a second project to the same master
space: it gets a topic folder, a global table row, and the indexes regenerate.
`--business` is accepted as an alias of `--project` for older instructions.
"""
import argparse
import datetime as dt
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "templates"
sys.path.insert(0, str(HERE))

TIER_BLOCK = re.compile(r"^[ \t]*<!-- tier (\d) -->[ \t]*\n(.*?)^[ \t]*<!-- /tier -->[ \t]*\n", re.S | re.M)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render(template_name, subs, tier=3):
    """Fill {{PLACEHOLDERS}}; keep a `<!-- tier N -->...<!-- /tier -->` block only when tier >= N."""
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    text = TIER_BLOCK.sub(lambda m: m.group(2) if tier >= int(m.group(1)) else "", text)
    for k, v in subs.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def put(path, text, log):
    path = Path(path)
    if path.exists():
        log.append(f"kept    {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    log.append(f"created {path}")


def append_if_missing(path, marker, block, log):
    path = Path(path)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        log.append(f"kept    {path} ({marker.strip()} already present)")
        return
    path.write_text(text.rstrip("\n") + "\n" + block, encoding="utf-8", newline="\n")
    log.append(f"appended {path}")


def topic_md(title, description, keywords):
    return ('---\n'
            f'title: {title}\n'
            f'description: "{description}"\n'
            f'keywords: [{", ".join(keywords)}]\n'
            '---\n')


def scaffold(master, project, name, owner, description, tool, log, today=None, tier=1, data_folders=()):
    master, project = Path(master).expanduser(), Path(project).expanduser()
    s = slug(name)
    today = today or dt.date.today().isoformat()
    data_folders = [d.strip().strip("/") for d in data_folders if d.strip()]
    subs = {
        "OWNER": owner, "PROJECT": name, "PROJECT_SLUG": s,
        "ONE_LINE_DESCRIPTION": description, "MASTER": str(master),
        "MASTER_REPO_URL": "<private repo url>", "PROJECT_REPO_URL": "<private repo url>",
        "PROJECT_DIR": str(project), "PROJECT_PARENT": str(project.parent),
        "DATA_FOLDERS": ", ".join(f"`{d}/`" for d in data_folders) or "(none declared yet; name them here and in .gitignore)",
        "YYYY-MM-DD": today,
        # what the topic folder holds beyond mirror indexes, and what the repo shim says about it
        "TOPIC_STATE": ", TASKS.md, LOG.md, RULES.md" if tier >= 2 else "",
        "REPO_STATE": ", its rules, task roster and decision log" if tier >= 2 else "",
        "RULES_LINE": ", and the rules below" if tier >= 2 else "",
        "RULES_IMPORT": f"@{master}/knowledge/{s}/RULES.md\n" if tier >= 2 else "",
    }
    global_file = "AGENTS.md"                 # canonical; per-tool shims are generated
    know = master / "knowledge"

    # ---- tier 1: master space instructions, git boundary, topic folders with their triggers
    put(master / global_file, render("AGENTS.md", subs, tier), log)
    if tool == "claude":
        put(master / "CLAUDE.md", "<!-- the instructions live in AGENTS.md -->\n@AGENTS.md\n", log)
    put(master / ".gitignore", render("gitignore", subs), log)
    put(master / ".gitattributes", render("gitattributes", subs), log)
    topics = {
        "general": ("General", f"how {owner} works, tooling, infrastructure",
                    ["memory", "journal", "skill", "workstation", "git"]),
        s: (name, description, [name]),
        "ideas": ("Ideas", "anything not yet a project", ["idea", "new project"]),
        "archive": ("Archive", "closed topics, not loaded as active context", ["archived", "closed topic"]),
    }
    for folder, (title, desc, kws) in topics.items():
        put(know / folder / "TOPIC.md", topic_md(title, desc, kws), log)
    append_if_missing(master / global_file, f"| {name} working files",
                      f"| {name} working files | `{project}` (git repo; its AGENTS.md is a shim; "
                      f"the model's index of it is `knowledge/{s}/`: mirror indexes{subs['TOPIC_STATE']}) |\n", log)
    put(know / s / "repo" / "INDEX.md", render("INDEX.md", subs, tier), log)   # the one project index

    # journal: one file per session; seed the first one so the rollup is never empty
    put(know / "journal" / f"{today}-0000-setup.md",
        "---\n"
        f"date: {today}\n"
        'time: "00:00"\n'
        'topic: "setup"\n'
        f'summary: "Installed the sagnis skill (tier {tier}); created the master space and the {name} repo"\n'
        'next: "Describe files in repo/INDEX.md as they appear; write the first memory files; git init and push both folders"\n'
        "---\n\n"
        f"Scaffolded by init_workspace.py on {today}: master space at `{master}`, "
        f"{name} working files at `{project}`, tier {tier}.\n", log)

    # ---- tier 2: the topic's own state: rules, decision log, first initiative, standing rules
    if tier >= 2:
        subs["INITIATIVE"] = "Setup"
        subs["LIST_PROCEDURES_BY_NAME_AND_PATH"] = "(none yet; add each `.claude/skills/<name>/SKILL.md` here by name and path)"
        put(know / s / "RULES.md", render("RULES.md", subs, tier), log)
        put(know / s / "LOG.md", render("LOG.md", subs, tier), log)
        put(know / s / "initiatives" / "_rules.md", render("standing-rules.md", subs, tier), log)
        put(know / s / "initiatives" / "setup.md", render("initiative.md", subs, tier), log)

    # generated layer: always rebuilt from the sources above
    import build_index
    d = build_index.DEFAULTS
    gen = build_index.build(know, d["n_facts"], d["n_journal"], today, d["titles"])
    build_index.write(know, gen)
    log += [f"generated {know / rel}" for rel in gen]

    # ---- project space: only the shim and what CI needs; the model's files stay above
    put(project / "AGENTS.md", render("REPO-AGENTS.md", subs, tier), log)
    if tool == "claude":
        put(project / "CLAUDE.md", "<!-- the instructions live in AGENTS.md -->\n@AGENTS.md\n", log)
    put(project / ".gitignore", "".join(f"{d}/\n" for d in data_folders) + ".env\n__pycache__/\n*.log\n", log)



def _all_text(*roots):
    for r in roots:
        for f in Path(r).rglob("*"):
            if f.is_file() and f.suffix in (".md", ".json", ".py", "") and ".git" not in f.parts:
                yield f, f.read_text(encoding="utf-8")


def selftest():
    import build_index
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        log = []
        # ---- tier 1: memory and routing, nothing else, and nothing that names a business
        scaffold(d / "m", d / "b", "Acme Co", "Jane", "widgets", "codex", log, today="2026-01-01", tier=1)
        know = d / "m" / "knowledge"
        t = know / "acme-co"
        assert (d / "m" / "AGENTS.md").exists() and (d / "b" / "AGENTS.md").exists()
        assert (t / "TOPIC.md").is_file() and (t / "repo" / "INDEX.md").is_file() and (know / "MEMORY.md").is_file()
        for absent in ("RULES.md", "LOG.md", "TASKS.md", "initiatives"):
            assert not (t / absent).exists(), absent
        assert not (d / "b" / "Automations").exists()
        shim = (d / "b" / "AGENTS.md").read_text(encoding="utf-8")
        assert "RULES.md" not in shim and "task roster" not in shim, shim
        assert "TASKS.md" not in (d / "m" / "AGENTS.md").read_text(encoding="utf-8")
        for f, text in _all_text(d / "m", d / "b"):
            assert not re.search(r"business|client|consult", text, re.I), (f, text)      # Phase 7 acceptance
            assert "{{" not in text.replace("{{ADD_ONE", "").replace("{{e.g.", ""), f
            assert "<!-- tier" not in text, f
        gen = build_index.build(know, 10, 3, "2026-01-01")
        assert build_index.check(know, gen) == []                                         # drift-clean out of the box
        assert "| Acme Co — widgets | Acme Co | [acme-co/INDEX.md](acme-co/INDEX.md) | 0 |" in (know / "MEMORY.md").read_text(encoding="utf-8")
        n = len(log)
        scaffold(d / "m", d / "b", "Acme Co", "Jane", "widgets", "codex", log, today="2026-01-01", tier=1)
        assert all(l.startswith(("kept", "generated", "shim ok")) for l in log[n:]), log[n:]   # idempotent
        # ---- tier 2 on top: state and guardrails appear, tier-1 files are kept
        scaffold(d / "m", d / "b", "Acme Co", "Jane", "widgets", "codex", log, today="2026-01-01", tier=2,
                 data_folders=["Customers", "Contracts"])
        for f in ("RULES.md", "LOG.md", "initiatives/_rules.md", "initiatives/setup.md", "TASKS.md"):
            assert (t / f).is_file(), f
        assert "| Set up the repository and the first automation | Setup | This week | Not started |" in (t / "TASKS.md").read_text(encoding="utf-8")
        assert "](repo/INDEX.md)" in (t / "INDEX.md").read_text(encoding="utf-8")        # routed
        rules = (t / "RULES.md").read_text(encoding="utf-8")
        assert "`Customers/`, `Contracts/`" in rules and "Automations/" not in rules       # no execution block
        assert (d / "b" / "AGENTS.md").read_text(encoding="utf-8") == shim               # kept, so still tier-1 wording
        assert not (d / "b" / "Automations").exists()
        # ---- tier 2, fresh, with a data folder and the claude shim
        scaffold(d / "m3", d / "b3", "Acme Co", "Jane", "widgets", "claude", log, today="2026-01-01", tier=2,
                 data_folders=["Customers"])
        b3 = d / "b3"
        assert "@" + str(d / "m3") + "/knowledge/acme-co/RULES.md" in (b3 / "AGENTS.md").read_text(encoding="utf-8")
        assert (b3 / "CLAUDE.md").exists() and "@AGENTS.md" in (b3 / "CLAUDE.md").read_text(encoding="utf-8")
        assert not (d / "b" / "CLAUDE.md").exists()                                       # codex: no shim
        assert (b3 / ".gitignore").read_text(encoding="utf-8").startswith("Customers/\n")
        assert not (b3 / "Automations").exists()
        for f, text in _all_text(d / "m3", b3):
            assert "{{" not in text.replace("{{ADD_ONE", "").replace("{{e.g.", "") and "<!-- tier" not in text, f
        # a second project in the same master space
        scaffold(d / "m3", d / "b4", "Second", "Jane", "other", "claude", log, today="2026-01-01", tier=2)
        mem = (d / "m3" / "knowledge" / "MEMORY.md").read_text(encoding="utf-8")
        assert "| Second — other |" in mem and "| Acme Co — widgets |" in mem             # both routes
        assert (d / "m3" / "AGENTS.md").read_text(encoding="utf-8").count("working files |") == 2
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--master", help="~/.claude or ~/.codex")
    ap.add_argument("--project", "--business", dest="project", help="path of the project folder to create")
    ap.add_argument("--name", help="project name")
    ap.add_argument("--owner", default="the owner")
    ap.add_argument("--description", default="(one line about the project)")
    ap.add_argument("--tool", choices=["codex", "claude"], default="claude")
    ap.add_argument("--tier", type=int, choices=[1, 2], default=1)
    ap.add_argument("--data-folders", default="", help="comma-separated private folders to gitignore, e.g. Customers,Contracts")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.master and a.project and a.name):
        ap.error("--master, --project and --name are required")
    log = []
    scaffold(a.master, a.project, a.name, a.owner, a.description, a.tool, log, tier=a.tier,
             data_folders=a.data_folders.split(","))
    print("\n".join(log))
    master = Path(a.master).expanduser()
    print(f"\nNext: edit {master}/AGENTS.md so every line is true, put real triggers in each "
          f"knowledge/<topic>/TOPIC.md, git init both folders, and describe files in "
          f"knowledge/{slug(a.name)}/repo/INDEX.md as they appear. Regenerate after any memory or journal write:\n"
          f"  python {HERE / 'build_index.py'} --knowledge {master / 'knowledge'}\n"
          f"Rerun with --tier 2 when tier 1 is habit." if a.tier == 1 else "")


if __name__ == "__main__":
    sys.exit(main())

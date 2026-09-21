#!/usr/bin/env python3
"""Measure what a workspace costs a model to load. Stdlib only.

    python measure.py --master ~/.claude ~/Projects/Acme [more repos...]
    python measure.py --master ~/.claude ./repo --json
    python measure.py --selftest

Reports four things, in the order they matter:

1. **Cold load** per project: the bytes a session reads before it has done any
   work at all (global instructions + repo rules + memory index + project index).
   This is the headline number and the one to drive down.
2. **Memory index health**: how many memory files exist, how many the index
   never mentions, and how many index lines point at files that are gone.
3. **Split candidates**: for each project index, the top-level folders ranked by
   how much of the index they account for. This is the input to a decision about
   breaking one index into several.
4. **Per-folder shape**: file count, bytes and depth per top-level folder, so
   growth is visible between runs.

Token counts are ESTIMATES at `--chars-per-token` (default 4.0), not a real
tokenizer, which no stdlib module provides. Raw character counts are reported
alongside so any number here can be recomputed later with a real tokenizer. For
before-and-after comparison the estimator only has to be stable, and it is.

Exit code is always 0; this is a measurement, not a check.
"""
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

# Files a session reads before doing any work. First match in each group wins,
# so a repo using either naming convention measures the same.
INSTRUCTION_NAMES = ("CLAUDE.md", "AGENTS.md", "AI.md", ".cursorrules")
INDEX_NAMES = ("INDEX.md", "Index.md", "index.md")
TASK_NAMES = ("TASKS.md", "Tasks.md", "tasks.md")

LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")
SKIP_DIRS = {".git", ".obsidian", "node_modules", "__pycache__", ".venv", "venv",
             "AI-Memory"}   # the AI workspace linked into a human repo is not a human folder


def first_existing(root, names):
    for n in names:
        p = root / n
        if p.is_file():
            return p
    return None


def stat_file(path, cpt):
    if path is None or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(path),
        "name": path.name,
        "bytes": path.stat().st_size,
        "chars": len(text),
        "lines": text.count("\n") + 1,
        "est_tokens": round(len(text) / cpt),
    }


def walk_files(root):
    for p in root.rglob("*"):
        if p.is_file() and not any(d in SKIP_DIRS for d in p.parts):
            yield p


def measure_master(master, cpt):
    master = Path(master).expanduser().resolve()
    know = master / "knowledge"
    out = {"path": str(master), "exists": master.is_dir()}
    if not out["exists"]:
        return out

    out["instructions"] = stat_file(first_existing(master, INSTRUCTION_NAMES), cpt)

    index_path = know / "MEMORY.md"
    out["memory_index"] = stat_file(index_path, cpt)

    # journal may be one file or a folder of per-session files
    j_file, j_dir = know / "journal.md", know / "journal"
    if j_dir.is_dir():
        files = sorted(j_dir.glob("*.md"))
        out["journal"] = {"form": "per-session", "files": len(files),
                          "bytes": sum(f.stat().st_size for f in files)}
    else:
        s = stat_file(j_file, cpt)
        out["journal"] = {"form": "single-file", "files": 1 if s else 0,
                          "bytes": s["bytes"] if s else 0}

    # memory files vs what the index references
    facts, linked, missing = [], set(), []
    if know.is_dir():
        for p in sorted(know.rglob("*.md")):
            if any(d in SKIP_DIRS for d in p.parts):
                continue
            rel = p.relative_to(know).as_posix()
            if rel in ("MEMORY.md", "journal.md") or rel.startswith("journal/") \
                    or p.name in ("INDEX.md", "TOPIC.md", "LOG.md", "TASKS.md", "RULES.md"):
                continue                                  # generated / topic config / state
            if rel.count("/") >= 2 and ((p.parent / "INDEX.md").is_file() or p.parent.name == "initiatives"):
                continue                                  # a working document beside its mirror index / an initiative note
            facts.append(rel)
    # a fact counts as referenced if the root index OR its topic INDEX.md links it
    for idx in [index_path] + sorted(know.glob("*/INDEX.md")):
        if not idx.is_file():
            continue
        base = "" if idx.parent == know else idx.parent.name + "/"
        text = idx.read_text(encoding="utf-8", errors="replace")
        for m in LINK_RE.findall(text):
            # links are relative to the index's own folder (root: topic/file.md;
            # topic: file.md or sub/INDEX.md)
            rel = base + m.replace("\\", "/").lstrip("./")
            linked.add(rel)
            if not (know / rel).is_file():
                missing.append(rel)

    by_topic = {}
    for rel in facts:
        by_topic.setdefault(rel.split("/")[0] if "/" in rel else "(root)", 0)
        by_topic[rel.split("/")[0] if "/" in rel else "(root)"] += 1

    out["memory"] = {
        "files": len(facts),
        "referenced": len([f for f in facts if f in linked]),
        "unreferenced": sorted(f for f in facts if f not in linked),
        "index_points_at_missing": sorted(missing),
        "by_topic": dict(sorted(by_topic.items())),
        "total_bytes": sum((know / f).stat().st_size for f in facts),
    }
    return out


def index_split_candidates(index_stat, repo, cpt):
    """Which top-level folders account for how much of this index."""
    if not index_stat:
        return []
    text = Path(index_stat["path"]).read_text(encoding="utf-8", errors="replace")
    tops = [d.name for d in sorted(repo.iterdir())
            if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith(".")]
    rows = []
    for line in text.splitlines():
        owner = next((t for t in tops if t in line), None)
        rows.append((owner, len(line)))
    agg = {}
    for owner, n in rows:
        if owner:
            agg.setdefault(owner, {"lines": 0, "chars": 0})
            agg[owner]["lines"] += 1
            agg[owner]["chars"] += n
    return sorted(
        ({"folder": k, "index_lines": v["lines"], "index_chars": v["chars"],
          "est_tokens": round(v["chars"] / cpt)} for k, v in agg.items()),
        key=lambda r: -r["index_chars"])


def measure_repo(repo, master_stat, cpt):
    repo = Path(repo).expanduser().resolve()
    out = {"path": str(repo), "name": repo.name, "exists": repo.is_dir()}
    if not out["exists"]:
        return out

    rules_file = first_existing(repo, INSTRUCTION_NAMES)
    rules = stat_file(rules_file, cpt)
    index = stat_file(first_existing(repo, INDEX_NAMES), cpt)
    tasks = stat_file(first_existing(repo, TASK_NAMES), cpt)
    out["read_path"], out["descent"], out["imports"] = "repo", None, []
    if rules_file is not None:
        # The shim shape (Phase 3): the repo's instruction file imports the topic's
        # RULES.md (@path, paid on every session, so it counts as repo rules) and
        # points at the topic INDEX.md in the AI workspace, which replaces the repo
        # index; the mirror indexes one tier down are what one descent costs.
        text = rules_file.read_text(encoding="utf-8", errors="replace")
        for imp in re.findall(r"(?<![\w.])@([^\s)`,;]+)", text):
            p = (repo / imp) if not Path(imp).is_absolute() else Path(imp)
            s = stat_file(p, cpt)
            if s:
                out["imports"].append(s)
                rules = dict(rules, chars=rules["chars"] + s["chars"], bytes=rules["bytes"] + s["bytes"],
                             est_tokens=rules["est_tokens"] + s["est_tokens"])
        m = re.search(r"knowledge/([\w-]+)/INDEX\.md", text)
        mpath = Path(master_stat["path"]) if master_stat and master_stat.get("path") else None
        if m and mpath and (mpath / "knowledge" / m.group(1) / "INDEX.md").is_file():
            topic = mpath / "knowledge" / m.group(1)
            out["read_path"] = f"ai-workspace:{m.group(1)}"
            index = stat_file(topic / "INDEX.md", cpt)
            tasks = stat_file(topic / "TASKS.md", cpt) or tasks
            mirrors = sorted(stat_file(p, cpt)["est_tokens"] for p in topic.glob("*/INDEX.md"))
            if mirrors:
                out["descent"] = {"count": len(mirrors), "median": mirrors[len(mirrors) // 2],
                                  "max": mirrors[-1], "total": sum(mirrors)}
    out["rules"], out["index"], out["tasks"] = rules, index, tasks
    out["missing"] = [label for label, s in
                      (("rules", rules), ("index", index), ("tasks", tasks)) if s is None]

    # cold load: global instructions + repo rules + memory index + project index
    parts = {
        "global_instructions": (master_stat or {}).get("instructions"),
        "memory_index": (master_stat or {}).get("memory_index"),
        "repo_rules": rules,
        "project_index": index,
    }
    cold = {k: (v["est_tokens"] if v else 0) for k, v in parts.items()}
    out["cold_load"] = {
        "parts": cold,
        "est_tokens": sum(cold.values()),
        "chars": sum((v["chars"] if v else 0) for v in parts.values()),
    }
    out["cold_load_plus_tasks"] = out["cold_load"]["est_tokens"] + (
        tasks["est_tokens"] if tasks else 0)

    out["split_candidates"] = index_split_candidates(index, repo, cpt)

    folders = []
    max_depth = 0
    for d in sorted(repo.iterdir()):
        if not d.is_dir() or d.name in SKIP_DIRS or d.name.startswith("."):
            continue
        files = list(walk_files(d))
        depth = max((len(f.relative_to(d).parts) for f in files), default=0)
        max_depth = max(max_depth, depth)
        folders.append({"folder": d.name, "files": len(files),
                        "bytes": sum(f.stat().st_size for f in files),
                        "max_depth": depth})
    out["folders"] = sorted(folders, key=lambda r: -r["bytes"])
    out["max_depth"] = max_depth
    out["total_files"] = sum(f["files"] for f in folders)
    return out


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n/1:,.1f} {unit}"
        n /= 1024


def render(data):
    cpt = data["chars_per_token"]
    L = [f"# Workspace baseline: {data['date']}", "",
         f"Token figures are estimates at {cpt} characters per token, not a real "
         f"tokenizer. Character counts are given so any figure here can be recomputed "
         f"later with a real one. What matters for before-and-after is that the "
         f"estimator is stable.", ""]

    m = data["master"]
    L += ["## Master space", "", f"`{m['path']}`", ""]
    if not m.get("exists"):
        L += ["Not found.", ""]
    else:
        L += ["| File | Bytes | Chars | Est. tokens |", "|---|---:|---:|---:|"]
        for label, key in (("Global instructions", "instructions"),
                           ("Memory index", "memory_index")):
            s = m.get(key)
            L.append(f"| {label} | {s['bytes']:,} | {s['chars']:,} | {s['est_tokens']:,} |"
                     if s else f"| {label} | (missing) | | |")
        L += ["", f"Journal: {m['journal']['form']}, {m['journal']['files']} file(s), "
                  f"{m['journal']['bytes']:,} bytes.", ""]
        mem = m["memory"]
        L += ["### Memory files", "",
              f"- {mem['files']} fact files, {mem['total_bytes']:,} bytes total",
              f"- {mem['referenced']} referenced by the index, "
              f"**{len(mem['unreferenced'])} unreferenced**",
              f"- **{len(mem['index_points_at_missing'])} index lines point at files "
              f"that do not exist**", ""]
        if mem["unreferenced"]:
            L += ["Unreferenced:", ""] + [f"- `{f}`" for f in mem["unreferenced"]] + [""]
        if mem["index_points_at_missing"]:
            L += ["Index points at missing:", ""] + \
                 [f"- `{f}`" for f in mem["index_points_at_missing"]] + [""]
        L += ["By topic: " + ", ".join(f"{k} {v}" for k, v in mem["by_topic"].items()), ""]

    L += ["## Cold load per project", "",
          "What a session reads before doing any work: global instructions, repo "
          "rules, memory index, project index. This is the number to drive down.", "",
          "| Project | Instructions | Memory index | Repo rules | Project index | "
          "**Total** | + tasks | One descent (median mirror index) |",
          "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in data["repos"]:
        if not r.get("exists"):
            L.append(f"| {r['name']} | (not found) | | | | | | |")
            continue
        p = r["cold_load"]["parts"]
        d = r.get("descent")
        L.append(f"| {r['name']} | {p['global_instructions']:,} | {p['memory_index']:,} "
                 f"| {p['repo_rules']:,} | {p['project_index']:,} | "
                 f"**{r['cold_load']['est_tokens']:,}** | "
                 f"{r['cold_load_plus_tasks']:,} | "
                 + (f"{d['median']:,} (max {d['max']:,}, {d['count']} indexes)" if d else "n/a") + " |")
    L.append("")
    for r in data["repos"]:
        if r.get("exists") and r["read_path"] != "repo":
            L.append(f"{r['name']}: read path is the AI workspace topic `{r['read_path'].split(':', 1)[1]}` "
                     f"(repo rules include {len(r['imports'])} imported file(s); project index and tasks are "
                     f"the topic's INDEX.md and TASKS.md).")
    L.append("")

    for r in data["repos"]:
        if not r.get("exists"):
            continue
        L += [f"## {r['name']}", "", f"`{r['path']}`", "",
              f"{r['total_files']:,} files, max depth {r['max_depth']}."]
        if r["missing"]:
            L.append(f"**Missing: {', '.join(r['missing'])}.**")
        L.append("")
        if r["split_candidates"]:
            L += ["Index split candidates (which folders the index spends itself on):",
                  "", "| Folder | Index lines | Chars | Est. tokens |",
                  "|---|---:|---:|---:|"]
            for c in r["split_candidates"][:12]:
                L.append(f"| {c['folder']} | {c['index_lines']} | "
                         f"{c['index_chars']:,} | {c['est_tokens']:,} |")
            L.append("")
        if r["folders"]:
            L += ["| Folder | Files | Bytes | Depth |", "|---|---:|---:|---:|"]
            for f in r["folders"][:15]:
                L.append(f"| {f['folder']} | {f['files']:,} | {f['bytes']:,} | "
                         f"{f['max_depth']} |")
            L.append("")
    return "\n".join(L)


def collect(master, repos, cpt, date):
    m = measure_master(master, cpt) if master else {}
    return {"date": date, "chars_per_token": cpt, "master": m,
            "repos": [measure_repo(r, m, cpt) for r in repos]}


def selftest():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        mk = d / "master"
        (mk / "knowledge" / "general").mkdir(parents=True)
        (mk / "CLAUDE.md").write_text("# rules\n" * 10, encoding="utf-8")
        (mk / "knowledge" / "general" / "user_a.md").write_text("a" * 100, encoding="utf-8")
        (mk / "knowledge" / "general" / "orphan.md").write_text("b" * 50, encoding="utf-8")
        (mk / "knowledge" / "MEMORY.md").write_text(
            "# Memory\n- [A](general/user_a.md)\n- [Gone](general/nope.md)\n", encoding="utf-8")
        (mk / "knowledge" / "journal.md").write_text("- entry\n", encoding="utf-8")

        rp = d / "proj"
        (rp / "Docs").mkdir(parents=True)
        (rp / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
        (rp / "INDEX.md").write_text("# Index\n- Docs/thing.md  a thing\n", encoding="utf-8")
        (rp / "TASKS.md").write_text("# Tasks\n", encoding="utf-8")
        (rp / "Docs" / "thing.md").write_text("x" * 20, encoding="utf-8")

        data = collect(mk, [rp], 4.0, "test")
        mem = data["master"]["memory"]
        assert mem["files"] == 2, mem
        assert mem["unreferenced"] == ["general/orphan.md"], mem
        assert mem["index_points_at_missing"] == ["general/nope.md"], mem
        r = data["repos"][0]
        assert r["missing"] == [], r["missing"]
        assert r["cold_load"]["est_tokens"] > 0
        assert any(c["folder"] == "Docs" for c in r["split_candidates"]), r["split_candidates"]
        assert data["master"]["journal"]["form"] == "single-file"

        # per-session journal form is detected
        (mk / "knowledge" / "journal").mkdir()
        (mk / "knowledge" / "journal" / "2026-01-01-x.md").write_text("e\n", encoding="utf-8")
        assert collect(mk, [], 4.0, "t")["master"]["journal"]["form"] == "per-session"

        # a repo missing its index still measures, and says so
        bare = d / "bare"
        bare.mkdir()
        assert collect(mk, [bare], 4.0, "t")["repos"][0]["missing"] == [
            "rules", "index", "tasks"]

        # the shim shape: repo rules = shim + @import; project index = the topic index
        # in the AI workspace; descent = the mirror indexes
        (mk / "knowledge" / "acme" / "kit").mkdir(parents=True)
        (mk / "knowledge" / "acme" / "INDEX.md").write_text("t" * 400, encoding="utf-8")
        (mk / "knowledge" / "acme" / "RULES.md").write_text("r" * 800, encoding="utf-8")
        (mk / "knowledge" / "acme" / "TASKS.md").write_text("k" * 200, encoding="utf-8")
        (mk / "knowledge" / "acme" / "kit" / "INDEX.md").write_text("m" * 1200, encoding="utf-8")
        shim = d / "shim"
        shim.mkdir()
        (shim / "CLAUDE.md").write_text(
            f"read {mk}/knowledge/MEMORY.md then {mk}/knowledge/acme/INDEX.md\n\n@{mk}/knowledge/acme/RULES.md\n",
            encoding="utf-8")
        r = collect(mk, [shim], 4.0, "t")["repos"][0]
        assert r["read_path"] == "ai-workspace:acme" and len(r["imports"]) == 1, r["read_path"]
        assert r["cold_load"]["parts"]["repo_rules"] == r["rules"]["est_tokens"] >= 200 + 20, r["rules"]
        assert r["cold_load"]["parts"]["project_index"] == 100 and r["tasks"]["est_tokens"] == 50
        assert r["descent"] == {"count": 1, "median": 300, "max": 300, "total": 300}, r["descent"]
        assert r["missing"] == [] and "One descent" in render(collect(mk, [shim], 4.0, "t"))

        render(data)  # must not raise
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="*", help="project repositories to measure")
    ap.add_argument("--master", help="master space (~/.claude or ~/.codex)")
    ap.add_argument("--chars-per-token", type=float, default=4.0)
    ap.add_argument("--date", default=None, help="label for the report (default: today)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON instead of markdown")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.master and not a.repos:
        ap.error("give --master and/or one or more repository paths")
    import datetime as dt
    data = collect(a.master, a.repos, a.chars_per_token, a.date or dt.date.today().isoformat())
    print(json.dumps(data, indent=2) if a.json else render(data))


if __name__ == "__main__":
    sys.exit(main())

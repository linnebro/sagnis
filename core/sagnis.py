#!/usr/bin/env python3
"""sagnis.py: the one script in the Sagnis core. Python 3 standard library, no network.

A memory is a folder of fact files behind a generated INDEX.md. This script does
everything that is formatting or bookkeeping, so the model's only job is content.

  save      write or update one fact, regenerate its index (an existing fact needs --expect <hash>)
  show      print a fact with its hash: the read a later save --expect refers to
  delete    remove a fact, regenerate its index
  keywords  add search words to a fact (the miss log: the words someone asked with)
  build     regenerate every INDEX.md from the facts; --check reports drift and writes nothing
  find      search every fact; prints the top lines, then the model opens one fact
  budget    tokens of what a session reads before any work: the files given plus their @imports
  --selftest

A fact file, the only thing written by hand (or by `save`):

    ---
    title: "Cedar Yard"
    description: "one line, at most 120 characters; it becomes the index line"
    source: "where it came from, with a date"
    status: stated            # stated | verified | inferred | superseded
    verified: "2026-09-16 against the org chart"   # only with status verified
    updated: 2026-09-16
    keywords: "optional. names, acronyms, synonyms, misspellings. read by find, never by the model"
    ---
    The fact. Absolute dates. Two to six sentences.

File name: <type>_<slug>.md, type one of user | feedback | project | reference.
Layout: facts directly under the root (one index), or one folder per topic (one
index each). A subfolder with an INDEX.md and no facts is a folder index and is
listed in the topic's generated FOLDERS.md, not walked (a notes/ folder with an INDEX.md
is one); the topic index links FOLDERS.md instead of carrying the list. scripts/ and initiatives/ are skipped. A fact stays about
150 words; the long record behind it goes in notes/<slug>.md and the fact names it.
"""
import argparse, collections, datetime, math, os, re, sys

TYPES = ["user", "project", "feedback", "reference"]
# How far a fact can be trusted. stated: the user said or decided it (the source names who and when);
# verified: checked against its authoritative source (`verified:` says when and where);
# inferred: the model's reading, summary or assumption; superseded: kept for history, names
# what replaced it. A stated or verified fact changes only on the user's word or a re-check.
STATUSES = ["stated", "verified", "inferred", "superseded"]
STATE = ["TASKS.md", "RULES.md"]
FOLDERS = "FOLDERS.md"   # generated beside INDEX.md: the folder indexes, opened on demand, not loaded
SKIP_DIRS = {"journal", "scripts", "initiatives", "__pycache__"}
MAX_DESC = 120
LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) \[(.+?)\]\((.+?)\) — (.+)$")
STOP = set("a an the of to in on for is are was were and or what which who whom how do does did i my me "
           "we our us it its at as be by with from that this there should can could would when where why "
           "still up come about use any has have had been get going gone whats s".split())


# ---- fact files -------------------------------------------------------------------------------

def parse(text):
    """(fields, body) from a fact file. Fields are the flat key: value pairs of the frontmatter."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    fields = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip().strip('"')
    return fields, text[end + 5:]


def render(fields, body):
    out = ["---"]
    for k in ("title", "description", "source", "status", "verified", "updated", "keywords"):
        v = fields.get(k, "")
        if k in ("keywords", "status", "verified") and not v:
            continue
        out.append(f"{k}: {v}" if k in ("updated", "status") else f'{k}: "{v.replace(chr(34), chr(39))}"')
    return "\n".join(out) + "\n---\n" + body.strip() + "\n"


def read(path):
    return open(path, encoding="utf-8").read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def is_fact(name):
    return name.endswith(".md") and name.split("_", 1)[0] in TYPES and "_" in name


def index_line(fname, fields):
    title = fields.get("title") or fname[:-3].split("_", 1)[1].replace("-", " ").capitalize()
    mark = f" ({fields['status']})" if fields.get("status") in ("inferred", "superseded") else ""
    return f"- {fields['updated']} [{title}]({fname}) — {fields['description']}{mark}"


def check_fields(fields, body):
    missing = [k for k in ("description", "source", "updated") if not fields.get(k)]
    if missing:
        return "missing " + ", ".join(missing)
    if not body.strip():
        return "empty body"
    if fields.get("status") and fields["status"] not in STATUSES:
        return f"status is '{fields['status']}', one of {', '.join(STATUSES)}"
    if len(fields["description"]) > MAX_DESC:
        return f"description is {len(fields['description'])} characters, the cap is {MAX_DESC}"
    return None


# ---- indexes ------------------------------------------------------------------------------------

def topics(root):
    """[(dir, name)]: the root itself when it holds facts, then every first-level folder with facts."""
    out = []
    if any(is_fact(f) for f in os.listdir(root)):
        out.append((root, ""))
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if os.path.isdir(p) and d not in SKIP_DIRS and not d.startswith(".") \
                and any(is_fact(f) for f in os.listdir(p)):
            out.append((p, d))
    return out


def folder_indexes(tdir):
    """Subfolders that carry their own INDEX.md (a mirror of some other folder): listed, not walked."""
    out = []
    for d in sorted(os.listdir(tdir)):
        ip = os.path.join(tdir, d, "INDEX.md")
        if os.path.isdir(os.path.join(tdir, d)) and d not in SKIP_DIRS and os.path.exists(ip):
            desc = parse(read(ip))[0].get("description", "")
            out.append(f"- [{d}/]({d}/INDEX.md)" + (f" — {desc}" if desc else ""))
    return out


def render_index(tdir, name, lines_by_file):
    """Deterministic: state links (FOLDERS.md when the topic has folder indexes), then facts by
    type, newest first, then title. The folder list itself lives in FOLDERS.md (render_folders)."""
    out = [f"# {name.replace('-', ' ').capitalize() if name else 'Memory'}", ""]
    state = [s for s in STATE if os.path.exists(os.path.join(tdir, s))]
    if folder_indexes(tdir):
        state.append(FOLDERS)
    if state:
        out += [" · ".join(f"[{s[:-3].capitalize()}]({s})" for s in state), ""]
    for t in TYPES:
        rows = [(l, f) for f, l in lines_by_file.items() if f.startswith(t + "_")]
        if not rows:
            continue
        rows.sort(key=lambda r: (LINE.match(r[0]).group(1), LINE.match(r[0]).group(2).lower()), reverse=True)
        out += [f"## {t}"] + [l for l, _ in rows] + [""]
    return "\n".join(out)


def render_folders(tdir, name):
    """FOLDERS.md text, or None when the topic has no folder indexes."""
    folders = folder_indexes(tdir)
    if not folders:
        return None
    title = name.replace('-', ' ').capitalize() if name else 'Memory'
    return "\n".join([f"# {title}: folder indexes", "",
                      "Open the one for the folder the task touches, never the folder itself.", ""]
                     + folders + [""])


def build_one(tdir, name):
    """(index text, [problems]) for one topic folder, from its fact files."""
    lines, problems = {}, []
    for f in sorted(os.listdir(tdir)):
        if not is_fact(f):
            continue
        fields, body = parse(read(os.path.join(tdir, f)))
        err = check_fields(fields, body)
        if err:
            problems.append(f"{name + '/' if name else ''}{f}: {err}")
            continue
        lines[f] = index_line(f, fields)
    return render_index(tdir, name, lines), problems


def build(root, check=False):
    """Regenerate every INDEX.md. Returns (changed, problems, warnings)."""
    changed, problems, warns = [], [], []
    tops = topics(root)
    for tdir, name in tops:
        new, probs = build_one(tdir, name)
        problems += probs
        ipath = os.path.join(tdir, "INDEX.md")
        old = read(ipath) if os.path.exists(ipath) else ""
        if old != new:
            changed.append(os.path.relpath(ipath, root).replace(os.sep, "/"))
            if not check:
                write(ipath, new)
        fpath, fnew = os.path.join(tdir, FOLDERS), render_folders(tdir, name)
        fold = read(fpath) if os.path.exists(fpath) else None
        if fold != fnew:
            changed.append(os.path.relpath(fpath, root).replace(os.sep, "/"))
            if not check and fnew is None:
                os.remove(fpath)
            elif not check:
                write(fpath, fnew)
    mem =os.path.join(root, "MEMORY.md")
    if os.path.exists(mem):
        routes = read(mem)
        for _, name in tops:
            if name and not re.search(rf"\b{re.escape(name)}\b", routes):
                warns.append(f"routes: topic '{name}' is not named in MEMORY.md")
    unrated = [f"{name + '/' if name else ''}{f}" for tdir, name in tops for f in sorted(os.listdir(tdir))
               if is_fact(f) and not parse(read(os.path.join(tdir, f)))[0].get("status")]
    if unrated:
        warns.append(f"{len(unrated)} fact(s) carry no status (stated|verified|inferred|superseded), e.g. {unrated[0]}")
    return changed, problems, warns


# ---- writes -------------------------------------------------------------------------------------

def topic_dir(root, topic):
    tdir = os.path.join(root, topic) if topic else root
    if not os.path.isdir(tdir):
        raise ValueError(f"topic folder not found: {tdir} (a new topic is a decision; make the folder first)")
    return tdir


def regen(tdir, name):
    new, problems = build_one(tdir, name)
    if problems:
        raise ValueError("; ".join(problems))
    write(os.path.join(tdir, "INDEX.md"), new)
    return os.path.join(tdir, "INDEX.md")


def fact_hash(path):
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]


def save(root, topic, typ, slug, title, description, source, body, updated=None, keywords="",
         status="inferred", verified="", expect=None):
    """Write one fact. Changing an existing fact needs `expect`, the hash `show` printed when
    the writer read it: a fact another session changed since then is refused, never overwritten."""
    tdir = topic_dir(root, topic)
    if typ not in TYPES:
        raise ValueError(f"type must be one of {TYPES}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):       # underscores: facts migrated from older layouts
        raise ValueError("slug: lower-case letters, digits, hyphens and underscores")
    fields = {"title": " ".join(title.split()), "description": " ".join(description.split()),
              "source": " ".join(source.split()), "status": status, "verified": " ".join(verified.split()),
              "updated": updated or datetime.date.today().isoformat(), "keywords": " ".join(keywords.split())}
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    err = check_fields(fields, body)
    if err:
        raise ValueError(err)
    fpath = os.path.join(tdir, f"{typ}_{slug}.md")
    if os.path.exists(fpath) and expect != fact_hash(fpath):
        raise ValueError(f"{typ}_{slug}.md exists and " + ("changed since you read it" if expect else "you passed no --expect")
                         + f": run `show --topic {topic} --file {typ}_{slug}.md`, read the current version, "
                           "then save again with --expect <its hash>")
    write(fpath, render(fields, body))
    return [fpath, regen(tdir, topic)]


def show(root, topic, fname):
    """The current fact with its hash: the read that a later `save --expect` refers to."""
    fpath = os.path.join(topic_dir(root, topic), fname)
    if not os.path.exists(fpath):
        raise ValueError(f"{fname} is not in {topic or 'the root'}")
    return f"hash: {fact_hash(fpath)}\n" + read(fpath)


def delete(root, topic, fname):
    tdir = topic_dir(root, topic)
    fpath = os.path.join(tdir, fname)
    if not os.path.exists(fpath):
        raise ValueError(f"{fname} is not in {tdir}")
    os.remove(fpath)
    return [regen(tdir, topic)]


def add_keywords(root, topic, fname, words):
    tdir = topic_dir(root, topic)
    fpath = os.path.join(tdir, fname)
    fields, body = parse(read(fpath))
    have = [w.strip() for w in fields.get("keywords", "").split(",") if w.strip()]
    new = [w.strip() for w in words.split(",") if w.strip() and w.strip() not in have]
    fields["keywords"] = ", ".join(have + new)
    write(fpath, render(fields, body))
    return [fpath]


# ---- search -------------------------------------------------------------------------------------

def toks(s):
    """Lower-case words minus stop words, cut to five characters so decide/decided and one
    misspelling still meet."""
    out = []
    for w in re.findall(r"[a-z0-9&][a-z0-9&+/-]*", s.lower().replace("'", "").replace("’", "")):
        for p in re.split(r"[/-]", w):
            if p and p not in STOP:
                out.append(p[:5])
    return out


def documents(root):
    """{label: text}: every fact (fields + body + file name), each state file whole, each folder index."""
    docs = {}
    for tdir, name in topics(root):
        pre = name + "/" if name else ""
        for f in sorted(os.listdir(tdir)):
            if is_fact(f):
                fields, body = parse(read(os.path.join(tdir, f)))
                docs[pre + f] = " ".join([fields.get("title", ""), fields.get("description", ""),
                                          fields.get("keywords", ""), f[:-3].replace("_", " "), body])
        for s in STATE:
            p = os.path.join(tdir, s)
            if os.path.exists(p):
                docs[pre + s] = s[:-3].lower() + " " + read(p)
        for d in os.listdir(tdir):                       # folder indexes: where documents live
            ip = os.path.join(tdir, d, "INDEX.md")
            if os.path.isdir(os.path.join(tdir, d)) and d not in SKIP_DIRS and os.path.exists(ip):
                docs[f"{pre}{d}/INDEX.md"] = d.replace("-", " ") + " " + read(ip)
    return docs


def bm25(docs, query, k1=1.2, b=0.75):
    d = {p: toks(t) for p, t in docs.items()}
    if not d:
        return []
    avg = sum(len(v) for v in d.values()) / len(d)
    df = collections.Counter(w for v in d.values() for w in set(v))
    n = len(d)
    idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}
    qs = toks(query)
    res = []
    for p, ws in d.items():
        tf, L, s = collections.Counter(ws), len(ws), 0.0
        for w in qs:
            if w in tf:
                s += idf[w] * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * L / avg))
        if s > 0:
            res.append((s, p))
    res.sort(key=lambda r: (-r[0], r[1]))
    return res


def find(root, query, top=5):
    """Top matches as printable lines. The model reads these, then opens one fact."""
    docs = documents(root)
    lines = []
    for score, p in bm25(docs, query)[:top]:
        if os.path.basename(p).split("_")[0] in TYPES or p.endswith("/INDEX.md"):
            fields = parse(read(os.path.join(root, p)))[0]
            lines.append(f"{p}  — {fields.get('description', '')}".rstrip(" —"))
        else:
            lines.append(p)
    return lines


# ---- budget -------------------------------------------------------------------------------------

def budget(paths, seen=None):
    """[(path, tokens)] for each file and, recursively, each `@path` import it names at the start
    of a line (Claude Code's import form; other tools read the line as a pointer). 4 chars = 1 token."""
    seen = seen if seen is not None else set()
    out = []
    for raw in paths:
        p = os.path.abspath(os.path.expanduser(raw))
        if p in seen:
            continue
        seen.add(p)
        if not os.path.isfile(p):
            out.append((raw, None))
            continue
        text = read(p)
        out.append((raw, len(text) // 4))
        for line in text.splitlines():
            m = re.match(r"^@(\S+)\s*$", line)
            if m:
                target = os.path.expanduser(m.group(1))
                if not os.path.isabs(target):
                    target = os.path.join(os.path.dirname(p), target)
                out += budget([target], seen)
    return out


# ---- cli ----------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    def common(p, *names):
        p.add_argument("--root", required=True, help="the memory folder")
        p.add_argument("--topic", default="", help="topic folder under root; omit for a single index")
        for n in names:
            p.add_argument("--" + n, required=True)

    s = sub.add_parser("save", help="write or update one fact")
    common(s, "type", "slug", "title", "description", "source")
    s.add_argument("--updated", help="YYYY-MM-DD, default today")
    s.add_argument("--keywords", default="", help="comma-separated search words")
    s.add_argument("--status", default="inferred", choices=STATUSES,
                   help="stated (the user said it), verified (checked at its source), inferred (default), superseded")
    s.add_argument("--verified", default="", help="with status verified: 'YYYY-MM-DD against <source>'")
    s.add_argument("--expect", help="changing an existing fact: the hash `show` printed")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--body"); g.add_argument("--body-file")
    common(sub.add_parser("show", help="print a fact with its hash (read before changing it)"), "file")
    common(sub.add_parser("delete", help="remove a fact"), "file")
    common(sub.add_parser("keywords", help="add search words to a fact"), "file", "words")
    b = sub.add_parser("build", help="regenerate every INDEX.md")
    b.add_argument("--root", required=True); b.add_argument("--check", action="store_true")
    f = sub.add_parser("find", help="search every fact")
    f.add_argument("--root", required=True); f.add_argument("query"); f.add_argument("--top", type=int, default=5)
    bu = sub.add_parser("budget", help="tokens a session reads before any work: these files plus their @imports")
    bu.add_argument("files", nargs="+"); bu.add_argument("--max", type=int, default=2000, help="exit 1 above this total")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()
    if not a.cmd:
        ap.print_help(); return 2
    try:
        if a.cmd == "build":
            changed, problems, warns = build(a.root, a.check)
            for p in problems: print("ERROR", p)
            for w in warns: print("WARN ", w)
            print(("DRIFT " if a.check else "WROTE ") + (", ".join(changed) or "nothing"))
            return 1 if problems or (a.check and changed) else 0
        if a.cmd == "find":
            lines = find(a.root, a.query, a.top)
            print("\n".join(lines) if lines else "NO MATCH: not in memory, or the words differ; try the topic index")
            return 0
        if a.cmd == "budget":
            rows = budget(a.files)
            total = sum(t or 0 for _, t in rows)
            for path, t in rows:
                print(f"{'MISSING' if t is None else t:>8}  {path}")
            print(f"{total:>8}  total, budget {a.max}: {'OK' if total <= a.max else 'OVER'}")
            return 0 if total <= a.max else 1
        if a.cmd == "save":
            body = a.body if a.body is not None else read(a.body_file)
            out = save(a.root, a.topic, a.type, a.slug, a.title, a.description, a.source, body, a.updated, a.keywords,
                       a.status, a.verified, a.expect)
        elif a.cmd == "show":
            print(show(a.root, a.topic, a.file))
            return 0
        elif a.cmd == "delete":
            out = delete(a.root, a.topic, a.file)
        else:
            out = add_keywords(a.root, a.topic, a.file, a.words)
        print("\n".join(p.replace(os.sep, "/") for p in out))   # the files that changed: the upload list in Cowork
        return 0
    except ValueError as e:
        print("ERROR", e); return 1


def selftest():
    import shutil, tempfile
    d = tempfile.mkdtemp()
    try:
        body = "Cedar Yard supplies the mulch. Deliveries every Tuesday."
        save(d, "", "reference", "cedar-yard", "Cedar Yard", "the mulch yard; delivers Tuesdays",
             "yard list, 2026-09-16", body, "2026-09-16", "mulch, bark, deliveries")
        save(d, "", "reference", "stonebrook-pavers", "Stonebrook Pavers", "the paver supplier; quotes by email",
             "vendor list, 2026-09-16", "Stonebrook Pavers sells the pavers. Quotes come by email.", "2026-09-10")
        idx = read(os.path.join(d, "INDEX.md"))
        assert idx.count("\n- 2026-") == 2 and idx.index("cedar-yard") < idx.index("stonebrook-pavers"), idx
        assert build(d, check=True)[0] == [], "fresh save must not drift"
        write(os.path.join(d, "INDEX.md"), idx.replace("delivers Tue", "delivers Wed"))
        assert build(d, check=True)[0] == ["INDEX.md"], "hand edit must show as drift"
        assert build(d)[0] == ["INDEX.md"] and read(os.path.join(d, "INDEX.md")) == idx
        assert find(d, "who brings the mulch?")[0].startswith("reference_cedar-yard.md"), find(d, "who brings the mulch?")
        assert find(d, "which supplier emails quotes")[0].startswith("reference_stonebrook-pavers.md")
        assert find(d, "quantum banana") == []
        try:
            save(d, "", "reference", "x", "X", "y" * (MAX_DESC + 1), "s", "b")
            raise AssertionError("long description must be refused")
        except ValueError:
            pass
        save(d, "", "project", "old_style", "Old", "an underscore slug updates in place", "s", "b")
        assert os.path.exists(os.path.join(d, "project_old_style.md"))
        delete(d, "", "project_old_style.md")
        write(os.path.join(d, "RULES.md"), "# Rules\n- Plowing is out of scope (Jo, 2026-09-20)\n")
        build(d); assert "[Rules](RULES.md)" in read(os.path.join(d, "INDEX.md"))
        assert find(d, "is plowing in scope")[0] == "RULES.md", find(d, "is plowing in scope")
        os.makedirs(os.path.join(d, "notes"))
        write(os.path.join(d, "notes", "long.md"), "# long\nproject_nothing_here.md is not a fact\n")
        assert "notes" not in read(os.path.join(d, "INDEX.md")) and build(d, check=True)[0] == []
        # budget: files plus their @imports, counted once
        write(os.path.join(d, "AGENTS.md"), "# rules\n@INDEX.md\n@people/INDEX.md\n@INDEX.md\n")
        rows = budget([os.path.join(d, "AGENTS.md")])
        assert [os.path.basename(r[0]) for r in rows][:2] == ["AGENTS.md", "INDEX.md"] and rows[-1][1] is None, rows
        assert all(t is None or t == len(read(os.path.abspath(os.path.expanduser(pth)))) // 4 for pth, t in rows)
        # status: inferred is the default and is marked in the index; stated is not
        assert "delivers Tuesdays (inferred)" in read(os.path.join(d, "INDEX.md"))
        # changing an existing fact: refused without the hash of the version read, or with a stale one
        fp = os.path.join(d, "reference_cedar-yard.md")
        for exp in (None, "000000000000"):
            try:
                save(d, "", "reference", "cedar-yard", "Cedar Yard", "x", "s", "b", expect=exp)
                raise AssertionError("an overwrite without the current hash was accepted")
            except ValueError as e:
                assert "show --topic" in str(e)
        h = show(d, "", "reference_cedar-yard.md").splitlines()[0][6:]
        save(d, "", "reference", "cedar-yard", "Cedar Yard", "the mulch yard; delivers Tuesdays",
             "Jo, 2026-09-17", body, "2026-09-17", "mulch, bark, deliveries", status="stated", expect=h)
        assert "status: stated" in read(fp) and "(stated)" not in read(os.path.join(d, "INDEX.md"))
        try:
            save(d, "", "reference", "new-one", "N", "n", "s", "b", status="maybe")
            raise AssertionError("an unknown status was accepted")
        except ValueError:
            pass
        add_keywords(d, "", "reference_stonebrook-pavers.md", "pavers, stone, stonebrook")
        assert "stonebrook" in parse(read(os.path.join(d, "reference_stonebrook-pavers.md")))[0]["keywords"]
        assert find(d, "stonebrook")[0].startswith("reference_stonebrook-pavers.md")
        delete(d, "", "reference_stonebrook-pavers.md")
        assert "stonebrook" not in read(os.path.join(d, "INDEX.md"))
        # topic layout, a folder index, and the routes check
        os.makedirs(os.path.join(d, "people", "repo"))
        write(os.path.join(d, "people", "repo", "INDEX.md"), '---\ndescription: "the team wiki"\n---\n# wiki\n')
        save(d, "people", "user", "odette", "Odette", "runs the Thursday crew", "crew schedule 2026-09-22", "Odette runs it.")
        pidx = read(os.path.join(d, "people", "INDEX.md"))
        assert "[Folders](FOLDERS.md)" in pidx and "repo/INDEX.md" not in pidx, pidx
        build(d)
        pfold = read(os.path.join(d, "people", FOLDERS))
        assert "[repo/](repo/INDEX.md) — the team wiki" in pfold, pfold
        os.remove(os.path.join(d, "people", "repo", "INDEX.md"))
        assert "people/FOLDERS.md" in build(d)[0]
        assert not os.path.exists(os.path.join(d, "people", FOLDERS)), "last folder index gone, FOLDERS.md must go"
        write(os.path.join(d, "people", "repo", "INDEX.md"), '---\ndescription: "the team wiki"\n---\n# wiki\n')
        build(d)
        write(os.path.join(d, "MEMORY.md"), "# Routes\n- general: nothing yet\n")
        assert build(d, check=True)[2] == ["routes: topic 'people' is not named in MEMORY.md"]
        assert find(d, "Thursday crew")[0].startswith("people/user_odette.md")
        assert find(d, "where is the team wiki")[0].startswith("people/repo/INDEX.md  — the team wiki")
        print("SELFTEST OK")
        return 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())

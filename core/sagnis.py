#!/usr/bin/env python3
"""sagnis.py: the one script in the Sagnis core. Python 3 standard library, no network.

A memory is a folder of fact files behind a generated INDEX.md. This script does
everything that is formatting or bookkeeping, so the model's only job is content.

  save      write or update one fact, regenerate its index
  delete    remove a fact, regenerate its index
  log       add one dated line to LOG.md, newest first
  keywords  add search words to a fact (the miss log: the words someone asked with)
  build     regenerate every INDEX.md from the facts; --check reports drift and writes nothing
  find      search every fact and decision; prints the top lines, then the model opens one fact
  --selftest

A fact file, the only thing written by hand (or by `save`):

    ---
    title: "Troy Hagen"
    description: "one line, at most 120 characters; it becomes the index line"
    source: "where it came from, with a date"
    updated: 2026-09-16
    keywords: "optional. names, acronyms, synonyms, misspellings. read by find, never by the model"
    ---
    The fact. Absolute dates. Two to six sentences.

File name: <type>_<slug>.md, type one of user | feedback | project | reference.
Layout: facts directly under the root (one index), or one folder per topic (one
index each). A subfolder with an INDEX.md and no facts is a folder index and is
listed, not walked. journal/, scripts/ and initiatives/ are skipped.
"""
import argparse, collections, datetime, math, os, re, sys

TYPES = ["user", "project", "feedback", "reference"]
STATE = ["TASKS.md", "LOG.md", "RULES.md"]
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
    for k in ("title", "description", "source", "updated", "keywords"):
        v = fields.get(k, "")
        if k == "keywords" and not v:
            continue
        out.append(f"{k}: {v}" if k == "updated" else f'{k}: "{v.replace(chr(34), chr(39))}"')
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
    return f"- {fields['updated']} [{title}]({fname}) — {fields['description']}"


def check_fields(fields, body):
    missing = [k for k in ("description", "source", "updated") if not fields.get(k)]
    if missing:
        return "missing " + ", ".join(missing)
    if not body.strip():
        return "empty body"
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
    """Deterministic: state links, folder indexes, then facts by type, newest first, then title."""
    out = [f"# {name.replace('-', ' ').capitalize() if name else 'Memory'}", ""]
    state = [s for s in STATE if os.path.exists(os.path.join(tdir, s))]
    if state:
        out += [" · ".join(f"[{s[:-3].capitalize()}]({s})" for s in state), ""]
    folders = folder_indexes(tdir)
    if folders:
        out += ["## Folders"] + folders + [""]
    for t in TYPES:
        rows = [(l, f) for f, l in lines_by_file.items() if f.startswith(t + "_")]
        if not rows:
            continue
        rows.sort(key=lambda r: (LINE.match(r[0]).group(1), LINE.match(r[0]).group(2).lower()), reverse=True)
        out += [f"## {t}"] + [l for l, _ in rows] + [""]
    return "\n".join(out)


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
    mem = os.path.join(root, "MEMORY.md")
    if os.path.exists(mem):
        routes = read(mem)
        for _, name in tops:
            if name and not re.search(rf"\b{re.escape(name)}\b", routes):
                warns.append(f"routes: topic '{name}' is not named in MEMORY.md")
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


def save(root, topic, typ, slug, title, description, source, body, updated=None, keywords=""):
    tdir = topic_dir(root, topic)
    if typ not in TYPES:
        raise ValueError(f"type must be one of {TYPES}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):       # underscores: facts migrated from older layouts
        raise ValueError("slug: lower-case letters, digits, hyphens and underscores")
    fields = {"title": " ".join(title.split()), "description": " ".join(description.split()),
              "source": " ".join(source.split()), "updated": updated or datetime.date.today().isoformat(),
              "keywords": " ".join(keywords.split())}
    err = check_fields(fields, body)
    if err:
        raise ValueError(err)
    fpath = os.path.join(tdir, f"{typ}_{slug}.md")
    write(fpath, render(fields, body))
    return [fpath, regen(tdir, topic)]


def delete(root, topic, fname):
    tdir = topic_dir(root, topic)
    fpath = os.path.join(tdir, fname)
    if not os.path.exists(fpath):
        raise ValueError(f"{fname} is not in {tdir}")
    os.remove(fpath)
    return [regen(tdir, topic)]


def log(root, topic, text, date=None):
    tdir = topic_dir(root, topic)
    p = os.path.join(tdir, "LOG.md")
    body = read(p) if os.path.exists(p) else f"# {topic or 'Memory'}: decisions\n\n"
    lines = body.splitlines()
    first = next((i for i, l in enumerate(lines) if l.startswith("- **")), len(lines))
    lines.insert(first, f"- **{date or datetime.date.today().isoformat()}** — {' '.join(text.split())}")
    write(p, "\n".join(lines).rstrip() + "\n")
    return [p, regen(tdir, topic)]           # the index gains the LOG link on the first decision


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
    """{label: text}: every fact (fields + body + file name), every LOG line, each state file whole."""
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
                text = read(p)
                if s == "LOG.md":
                    for l in text.splitlines():
                        if l.startswith("- **"):
                            docs[pre + "LOG.md " + l[:160]] = "decided decision log " + l
                else:
                    docs[pre + s] = s[:-3].lower() + " " + text
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
        if " " in p:                                    # a LOG line
            lines.append(p)
        elif os.path.basename(p).split("_")[0] in TYPES or p.endswith("/INDEX.md"):
            fields = parse(read(os.path.join(root, p)))[0]
            lines.append(f"{p}  — {fields.get('description', '')}".rstrip(" —"))
        else:
            lines.append(p)
    return lines


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
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--body"); g.add_argument("--body-file")
    common(sub.add_parser("delete", help="remove a fact"), "file")
    lg = sub.add_parser("log", help="one dated decision line in LOG.md")
    common(lg, "text"); lg.add_argument("--date")
    common(sub.add_parser("keywords", help="add search words to a fact"), "file", "words")
    b = sub.add_parser("build", help="regenerate every INDEX.md")
    b.add_argument("--root", required=True); b.add_argument("--check", action="store_true")
    f = sub.add_parser("find", help="search every fact and decision")
    f.add_argument("--root", required=True); f.add_argument("query"); f.add_argument("--top", type=int, default=5)
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
        if a.cmd == "save":
            body = a.body if a.body is not None else read(a.body_file)
            out = save(a.root, a.topic, a.type, a.slug, a.title, a.description, a.source, body, a.updated, a.keywords)
        elif a.cmd == "delete":
            out = delete(a.root, a.topic, a.file)
        elif a.cmd == "log":
            out = log(a.root, a.topic, a.text, a.date)
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
        body = "Troy Hagen is the manager. Weekly one-to-one on Tuesdays."
        save(d, "", "reference", "troy-hagen", "Troy Hagen", "Steve's manager; weekly 1:1 Tuesdays",
             "org chart, 2026-09-16", body, "2026-09-16", "boss, reports to, supervisor")
        save(d, "", "reference", "arctic-wolf", "Arctic Wolf", "the MDR vendor; alerts by email",
             "vendor list, 2026-09-16", "Arctic Wolf watches the network. Alerts go to the security mailbox.", "2026-09-10")
        idx = read(os.path.join(d, "INDEX.md"))
        assert idx.count("\n- 2026-") == 2 and idx.index("troy-hagen") < idx.index("arctic-wolf"), idx
        assert build(d, check=True)[0] == [], "fresh save must not drift"
        write(os.path.join(d, "INDEX.md"), idx.replace("weekly 1:1", "weekly 1:2"))
        assert build(d, check=True)[0] == ["INDEX.md"], "hand edit must show as drift"
        assert build(d)[0] == ["INDEX.md"] and read(os.path.join(d, "INDEX.md")) == idx
        assert find(d, "who's my boss?")[0].startswith("reference_troy-hagen.md"), find(d, "who's my boss?")
        assert find(d, "which vendor emails alerts")[0].startswith("reference_arctic-wolf.md")
        assert find(d, "quantum banana") == []
        try:
            save(d, "", "reference", "x", "X", "y" * (MAX_DESC + 1), "s", "b")
            raise AssertionError("long description must be refused")
        except ValueError:
            pass
        save(d, "", "project", "old_style", "Old", "an underscore slug updates in place", "s", "b")
        assert os.path.exists(os.path.join(d, "project_old_style.md"))
        delete(d, "", "project_old_style.md")
        log(d, "", "Atlas is out of scope (Steve, 2026-09-20)", "2026-09-20")
        log(d, "", "Weekly IT moved to Thursdays", "2026-09-22")
        lg = read(os.path.join(d, "LOG.md")).splitlines()
        assert lg[2].startswith("- **2026-09-22**") and lg[3].startswith("- **2026-09-20**"), lg
        assert "[Log](LOG.md)" in read(os.path.join(d, "INDEX.md"))
        assert find(d, "what did we decide about Atlas")[0].startswith("LOG.md ")
        add_keywords(d, "", "reference_arctic-wolf.md", "MDR, SOC, arcticwolf")
        assert "arcticwolf" in parse(read(os.path.join(d, "reference_arctic-wolf.md")))[0]["keywords"]
        assert find(d, "arcticwolf")[0].startswith("reference_arctic-wolf.md")
        delete(d, "", "reference_arctic-wolf.md")
        assert "arctic" not in read(os.path.join(d, "INDEX.md"))
        # topic layout, a folder index, and the routes check
        os.makedirs(os.path.join(d, "people", "repo"))
        write(os.path.join(d, "people", "repo", "INDEX.md"), '---\ndescription: "the team wiki"\n---\n# wiki\n')
        save(d, "people", "user", "nick", "Nick", "owns the NetScout evaluation", "meeting 2026-09-22", "Nick owns it.")
        pidx = read(os.path.join(d, "people", "INDEX.md"))
        assert "## Folders" in pidx and "[repo/](repo/INDEX.md) — the team wiki" in pidx, pidx
        write(os.path.join(d, "MEMORY.md"), "# Routes\n- general: nothing yet\n")
        assert build(d, check=True)[2] == ["routes: topic 'people' is not named in MEMORY.md"]
        assert find(d, "NetScout owner")[0].startswith("people/user_nick.md")
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

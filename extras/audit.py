#!/usr/bin/env python3
"""Audit trail: written on every action, read almost never, never in context.

    python audit.py hook                          # stdin = Claude Code hook JSON (PostToolUse / SessionEnd / SessionStart)
    python audit.py record --action note --target path/to/file --outcome ok [--approval "<owner> 14:02"]
    python audit.py session-end --transcript <path.jsonl> [--session ID]
    python audit.py query [--since 2026-09-18] [--until ...] [--session ID] [--action Write] [--path knowledge/] [--device X] [--json]
    python audit.py rotate [--days 7] [--ship-after 90] [--archive <archive path>]   # also runs from the SessionEnd hook
    python audit.py verify [--archive <archive path>]                                # every manifest hash, local or archived
    python audit.py selftest

Storage: gitignored, outside version control,
partitioned so no two writers share an append target:

    <master>/audit/<device>/<YYYY-MM-DD>/<session-id>.jsonl

One JSON object per line. **References, not content**: an event carries a path
and a content hash, never file contents, prompt text or record data. This is
enforced by the writer, not by convention: `record()` refuses any field longer
than MAX_FIELD characters.

Event shape:
    ts        ISO-8601 with offset
    session   session id
    device    hostname
    mode      "hook" (enforced, outside the model's discretion) | "manual" (best-effort)
    actor     {"assistant": "claude-code", "model": "<model that served the turn or null>"}
    action    tool name, or session_start | session_end | note
    target    path or null
    hash      sha256[:16] of the target after the action, or null
    outcome   ok | error | <short word>
    approval  reference string or null
    provider  the provider that answered a routed call, or null
    detail    small dict: tool_use id (links before, after and failure); for session_end the
              usage totals and file counts; for Bash the command length + hash (never the
              command); for a failure the exit code (never the error text); for MCP the server
    prev      sha256[:32] of the previous line in the same file ("" first): the hash chain

Events per hook: PreToolUse (file-writing tools only) -> `before:<tool>` with the hash before
the write; PostToolUse -> the tool, hash after; PostToolUseFailure -> the tool, outcome error
or interrupted; SessionEnd -> session_end, a `git_snapshot` per repo (HEAD, dirty count,
porcelain hash: the trace of Bash writes and commits), then the session's file is mirrored
to AUDIT_ARCHIVE (a second disk or a NAS) at once. `verify` checks every chain and that each local file
still starts with its mirror. The worker can still write both copies as the same user; the
chain, the mirror and the git-tracked manifest make an edit detectable, not impossible.

Query mode: filters by time range, session, action, path prefix, device; prints
a table or --json. It reads hot (.jsonl) and cold (.jsonl.xz) files alike, and
the archive too when --archive / AUDIT_ARCHIVE names it.

Retention: rotate and compress, never prune. `rotate` compresses every
day older than --days with stdlib lzma (write, re-read, compare, then delete the
plain file), and appends one line per archive to `<master>/audit-manifest.jsonl`,
the only audit file git tracks: path, sha256, event count, first and last
timestamp. Days older than --ship-after are copied to --archive, and
the local copy is deleted only after the copy's hash matches the manifest. The
SessionEnd hook calls rotate, so no scheduler is needed. `verify` re-hashes every
manifest entry wherever it lives; that is the restore test.
"""
import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
import shutil
import platform
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_MASTER = Path(os.environ.get("SAGNIS_MASTER") or Path.home() / ".claude")   # the workspace audit/ lives in
MAX_FIELD = 300                      # any string longer than this is content, not a reference
FILE_TOOLS_WRITE = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
FILE_TOOLS_READ = {"Read", "Glob", "Grep", "LS"}
MANIFEST = "audit-manifest.jsonl"
HOT_DAYS, WARM_DAYS = 7, 90                # plain JSONL for 7 days, compressed locally for 90, then the archive


# ----------------------------------------------------------------- helpers
def now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def device_name():
    return os.environ.get("AUDIT_DEVICE") or platform.node() or "unknown"


def file_hash(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError:
        return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def open_trail(path):
    """Text handle on a hot (.jsonl) or cold (.jsonl.xz) trail file."""
    if str(path).endswith(".xz"):
        return lzma.open(path, "rt", encoding="utf-8")
    return open(path, encoding="utf-8")


def trail_path(master, session, date=None):
    date = date or dt.date.today().isoformat()
    sid = "".join(c if c.isalnum() or c in "-_" else "_" for c in (session or "nosession"))[:80]
    return Path(master) / "audit" / device_name() / date / f"{sid}.jsonl"


def _check_reference_only(ev):
    for k, v in ev.items():
        if isinstance(v, str) and len(v) > MAX_FIELD:
            raise ValueError(f"audit event field '{k}' is {len(v)} chars: content is never recorded, only references")
        if isinstance(v, dict):
            _check_reference_only(v)


def line_hash(line):
    return hashlib.sha256(line.rstrip("\n").encode("utf-8")).hexdigest()[:32]


def _last_line(p):
    try:
        with open(p, "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - 65536))
            lines = fh.read().decode("utf-8", errors="replace").splitlines()
            return lines[-1] if lines else ""
    except OSError:
        return ""


class _Lock:
    """Exclusive create of <file>.lock: parallel tool calls in one session append in turn,
    so the chain never forks. A lock older than 5 s is a crashed writer and is taken over."""
    def __init__(self, p):
        self.p = Path(str(p) + ".lock")

    def __enter__(self):
        for _ in range(100):
            try:
                os.close(os.open(self.p, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if dt.datetime.now().timestamp() - self.p.stat().st_mtime > 5:
                        self.p.unlink()
                        continue
                except OSError:
                    pass
                import time
                time.sleep(0.02)
        return self                            # ponytail: after 2 s write anyway; verify reports the fork

    def __exit__(self, *a):
        try:
            self.p.unlink()
        except OSError:
            pass


def record(master, session, action, target=None, outcome="ok", mode="manual", model=None,
           approval=None, provider=None, detail=None, ts=None, actor=None):
    ev = {"ts": ts or now_iso(), "session": session or "", "device": device_name(), "mode": mode,
          "actor": {"assistant": actor or os.environ.get("AUDIT_ACTOR") or "claude-code", "model": model},
          "action": action, "target": target, "hash": file_hash(target) if target else None,
          "outcome": outcome, "approval": approval, "provider": provider, "detail": detail or {}}
    _check_reference_only(ev)
    p = trail_path(master, session, (ev["ts"][:10]))
    p.parent.mkdir(parents=True, exist_ok=True)
    with _Lock(p):
        last = _last_line(p)
        ev["prev"] = line_hash(last) if last else ""    # hash chain: an edited or deleted line breaks it
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def chain_problems(lines, label):
    """Every line's `prev` must be the hash of the line before it (the first: empty).
    Lines written before the chain existed (no `prev` key) are skipped."""
    out, before = [], None
    chained = any('"prev": ' in line for line in lines)
    for i, line in enumerate(lines, 1):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            # before the lock (2026-10-16) parallel hooks could tear a line: legacy, not tampering
            out.append(f"{label}:{i} not JSON" + ("" if chained else " (legacy: torn by a concurrent write)"))
            before = line
            continue
        if "prev" in ev:
            want = line_hash(before) if before is not None else ""
            if ev["prev"] != want:
                out.append(f"{label}:{i} chain broken (a line before it was changed, removed or inserted)")
        before = line
    return out


# ------------------------------------------------------------- transcript
def transcript_model(path, tail_bytes=65536):
    """Model named in the last assistant message; reads only the tail."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            fh.seek(max(0, size - tail_bytes))
            chunk = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    model = None
    for line in chunk.splitlines():
        if '"type":"assistant"' in line or '"type": "assistant"' in line:
            try:
                model = json.loads(line).get("message", {}).get("model") or model
            except json.JSONDecodeError:
                pass
    return model


def transcript_usage(path):
    """Sum the per-message usage the assistant reported; the real session cost."""
    tot = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "turns": 0}
    reads = writes = 0
    model = None
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("type") != "assistant":
                    continue
                m = d.get("message", {})
                u = m.get("usage") or {}
                if u:
                    tot["turns"] += 1
                    tot["input"] += u.get("input_tokens", 0) or 0
                    tot["output"] += u.get("output_tokens", 0) or 0
                    tot["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
                    tot["cache_create"] += u.get("cache_creation_input_tokens", 0) or 0
                model = m.get("model") or model
                for c in m.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        name = c.get("name", "")
                        reads += name in FILE_TOOLS_READ
                        writes += name in FILE_TOOLS_WRITE
    except OSError:
        return None, None, 0, 0
    return tot, model, reads, writes


# ------------------------------------------------------------------- hook
def handle_hook(master, data):
    """One Claude Code hook payload -> one event. Never raises."""
    event = data.get("hook_event_name", "")
    session = data.get("session_id", "")
    transcript = data.get("transcript_path")
    if event in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        tool = data.get("tool_name", "?")
        inp = data.get("tool_input") or {}
        target = inp.get("file_path") or inp.get("path") or inp.get("notebook_path")
        detail = {"id": (data.get("tool_use_id") or "")[-24:]}         # links before, after and failure
        if tool.startswith("mcp__"):                                   # connector side effects: what it touched
            detail["server"] = (data.get("mcp_server") or tool.split("__")[1])[:60]
            for k in ("fileId", "file_id", "id", "record_id", "parentId", "url", "to", "recipient"):
                v = inp.get(k)
                if isinstance(v, str) and 0 < len(v) <= MAX_FIELD:
                    target = target or f"{k}={v}"
                    break
        if tool == "Bash" and inp.get("command"):
            cmd = inp["command"]
            detail.update(command_len=len(cmd), command_hash=hashlib.sha256(cmd.encode()).hexdigest()[:16])
        if event == "PreToolUse":                                      # registered for file writes only
            return record(master, session, "before:" + tool, target, "pending", "hook", detail=detail)
        outcome = "ok"
        if event == "PostToolUseFailure":
            err = str(data.get("error") or "")
            first = err.splitlines()[0] if err else ""
            detail["exit"] = first[10:].strip()[:8] if first.startswith("Exit code ") else None
            outcome = "interrupted" if data.get("is_interrupt") else "error"
        elif isinstance(data.get("tool_response"), dict) and data["tool_response"].get("is_error"):
            outcome = "error"
        model = transcript_model(transcript) if transcript else None
        return record(master, session, tool, target, outcome, "hook", model, detail=detail)
    if event == "SessionEnd":
        ev = session_end(master, session, transcript, mode="hook", reason=data.get("reason"))
        for repo in {data.get("cwd") or "", str(master)} - {""}:     # what changed outside the file tools (Bash, git)
            snap = git_snapshot(repo)
            if snap:
                record(master, session, "git_snapshot", outcome="ok", mode="hook", detail=snap)
        try:
            mirror_session(master, session)    # off-machine copy within the session, not after 90 days
        except Exception as e:
            print(f"audit: mirror: {e}", file=sys.stderr)
        try:
            rotate(master)                     # daily rotation rides on the hook: no scheduler
        except Exception as e:
            print(f"audit: rotate: {e}", file=sys.stderr)
        try:
            msg = commit_manifest(master)
            if msg and not msg.startswith("committed and pushed"):
                print(f"audit: manifest: {msg}", file=sys.stderr)
        except Exception as e:
            print(f"audit: manifest: {e}", file=sys.stderr)
        return ev
    if event == "SessionStart":
        return record(master, session, "session_start", outcome=data.get("source") or "ok", mode="hook",
                      detail={"cwd_hash": hashlib.sha256((data.get("cwd") or "").encode()).hexdigest()[:16]})
    return None


def git_snapshot(repo):
    """HEAD, branch, dirty-path count and a hash of `git status --porcelain`: the trace a Bash
    write or a commit leaves, which the file-tool events cannot see. None outside a repo."""
    import subprocess

    def g(*args):
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    try:
        top = g("rev-parse", "--show-toplevel")
        if not top:
            return None
        status = g("status", "--porcelain") or ""
        return {"repo": Path(top).name[:80], "head": (g("rev-parse", "--short=12", "HEAD") or "")[:12],
                "branch": (g("branch", "--show-current") or "")[:120], "dirty": len(status.splitlines()),
                "status_hash": hashlib.sha256(status.encode()).hexdigest()[:16],
                "unpushed": len((g("log", "--branches", "--not", "--remotes", "--oneline") or "").splitlines())}
    except (OSError, subprocess.SubprocessError):
        return None


def mirror_session(master, session, archive=None):
    """Copy this session's hot trail files to the archive now and check the copy, so a
    later local edit shows up as a difference from the mirror. No archive configured: no-op."""
    archive = archive or os.environ.get("AUDIT_ARCHIVE")
    if not archive or not session:
        return []
    name = trail_path(master, session).name
    out = []
    for f in sorted((Path(master) / "audit").glob(f"*/*/{name}")):
        dest = Path(archive) / f.parts[-3] / f.parts[-2] / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
        out.append(("mirrored " if sha256_file(dest) == sha256_file(f) else "mirror FAILED ") + str(dest))
    return out


def session_end(master, session, transcript, mode="manual", reason=None):
    tot, model, reads, writes = transcript_usage(transcript) if transcript else (None, None, 0, 0)
    detail = {"usage": tot, "files_read": reads, "files_written": writes, "reason": reason}
    return record(master, session, "session_end", outcome="ok" if tot else "no-transcript",
                  mode=mode, model=model, detail=detail)


# ------------------------------------------------------------------ query
def trail_files(master, archive=None):
    roots = [Path(master) / "audit"] + ([Path(archive)] if archive else [])
    return sorted(f for r in roots if r.is_dir() for pat in ("*/*/*.jsonl", "*/*/*.jsonl.xz") for f in r.glob(pat))


def query(master, since=None, until=None, session=None, action=None, path=None, device=None, archive=None):
    out = []
    for f in trail_files(master, archive or os.environ.get("AUDIT_ARCHIVE")):
        dev, day = f.parts[-3], f.parts[-2]
        if device and dev != device:
            continue
        if since and day < since[:10] or until and day > until[:10]:
            continue
        with open_trail(f) as fh:
            for line in fh:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if since and ev["ts"] < since or until and ev["ts"] > until:
                    continue
                if session and not ev["session"].startswith(session):
                    continue
                if action and ev["action"] != action:
                    continue
                if path and not (ev.get("target") or "").replace("\\", "/").startswith(path.replace("\\", "/")) \
                        and path not in (ev.get("target") or ""):
                    continue
                out.append(ev)
    return sorted(out, key=lambda e: e["ts"])


def render(events):
    if not events:
        return "(no events)"
    L = [f"{'ts':25} {'session':10} {'mode':6} {'action':12} {'outcome':8} target"]
    for e in events:
        extra = ""
        if e["action"] == "session_end" and e["detail"].get("usage"):
            u = e["detail"]["usage"]
            extra = (f"  turns={u['turns']} in={u['input']:,} out={u['output']:,} "
                     f"cache_read={u['cache_read']:,} cache_create={u['cache_create']:,} "
                     f"read={e['detail'].get('files_read')} wrote={e['detail'].get('files_written')} "
                     f"model={e['actor'].get('model')}")
        L.append(f"{e['ts']:25} {e['session'][:10]:10} {e['mode']:6} {e['action'][:12]:12} "
                 f"{e['outcome'][:8]:8} {e.get('target') or ''}{extra}")
    return "\n".join(L)


# ------------------------------------------------------- rotate / verify
def _manifest_entry(xz, rel):
    n = first = last = None
    with open_trail(xz) as fh:
        for n, line in enumerate(fh, 1):
            try:
                ts = json.loads(line)["ts"]
            except (json.JSONDecodeError, KeyError):
                continue
            first = first or ts
            last = ts
    return {"path": rel, "sha256": sha256_file(xz), "events": n or 0, "first": first, "last": last,
            "archived": now_iso()}


def read_manifest(master):
    p = Path(master) / MANIFEST
    if not p.is_file():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
            out[e["path"]] = e
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def rotate(master, days=HOT_DAYS, ship_after=WARM_DAYS, archive=None, today=None):
    """Compress days older than `days`; ship days older than `ship_after` to `archive`.
    Every step is verify-then-delete, so a run killed halfway is redone next time."""
    master = Path(master)
    root = master / "audit"
    archive = archive or os.environ.get("AUDIT_ARCHIVE")
    today = dt.date.fromisoformat(today) if today else dt.date.today()
    log = []
    if not root.is_dir():
        return log
    manifest = read_manifest(master)
    for f in sorted(root.glob("*/*/*.jsonl")):
        dev, day = f.parts[-3], f.parts[-2]
        try:
            age = (today - dt.date.fromisoformat(day)).days
        except ValueError:
            continue
        if age < days or age < 1:              # never touch today: a session may still be appending
            continue
        xz = f.with_name(f.name + ".xz")
        tmp = xz.with_suffix(".tmp")
        raw = f.read_bytes()
        with lzma.open(tmp, "wb") as out:
            out.write(raw)
        with lzma.open(tmp, "rb") as back:
            if back.read() != raw:             # verify before anything is deleted
                tmp.unlink()
                log.append(f"compress FAILED {f}")
                continue
        os.replace(tmp, xz)
        rel = f"{dev}/{day}/{xz.name}"
        entry = _manifest_entry(xz, rel)
        with open(master / MANIFEST, "a", encoding="utf-8") as mf:
            mf.write(json.dumps(entry) + "\n")
        manifest[rel] = entry
        f.unlink()
        log.append(f"compressed {rel} ({entry['events']} events)")
    if archive:
        archive = Path(archive)
        for xz in sorted(root.glob("*/*/*.jsonl.xz")):
            dev, day = xz.parts[-3], xz.parts[-2]
            rel = f"{dev}/{day}/{xz.name}"
            try:
                age = (today - dt.date.fromisoformat(day)).days
            except ValueError:
                continue
            if age < ship_after or rel not in manifest:
                continue
            dest = archive / dev / day / xz.name
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(xz, dest)
                ok = sha256_file(dest) == manifest[rel]["sha256"]
            except OSError as e:               # archive offline: keep the local copy, try next time
                log.append(f"ship deferred {rel}: {e}")
                continue
            if ok:
                xz.unlink()                    # delete local only after the archive copy verifies
                log.append(f"shipped {rel}")
            else:
                log.append(f"ship FAILED {rel}: hash mismatch")
    return log


def commit_manifest(master):
    """Commit and push the manifest lines rotate() appended. Rotation runs at SessionEnd, after the
    session's own commit, so without this every next health check found them uncommitted. Only on
    main, only that one path (other sessions' staged work is left alone), and only after main
    fast-forwards to origin, so the commit never forks the shared checkout. None: nothing to do."""
    import subprocess

    def g(*args, timeout=20):
        return subprocess.run(["git", "-C", str(master), *args], capture_output=True, text=True, timeout=timeout)
    if g("branch", "--show-current").stdout.strip() != "main":
        return None
    if not g("status", "--porcelain", "--", MANIFEST).stdout.strip():
        return None
    if g("fetch", "-q", "origin", "main").returncode or g("merge", "--ff-only", "-q", "origin/main").returncode:
        return "left uncommitted: main does not fast-forward to origin/main"
    r = g("commit", "-q", "-m", f"audit manifest: rotated trail days ({now_iso()[:10]}, audit.py SessionEnd hook)",
          "--", MANIFEST, timeout=60)                  # the pre-commit gate runs here; never bypassed
    if r.returncode:
        return f"commit failed: {(r.stderr or r.stdout).strip()[:300]}"
    p = g("push", "-q", "origin", "HEAD:main")
    return "committed and pushed" if p.returncode == 0 else f"committed, push failed: {p.stderr.strip()[:300]}"


def verify(master, archive=None, legacy=None):
    """Re-hash every manifest entry, local or archived. Returns (problem lines, archives verified)."""
    master = Path(master)
    archive = archive or os.environ.get("AUDIT_ARCHIVE")
    problems, n = [], 0
    for rel, e in read_manifest(master).items():
        cands = [master / "audit" / rel] + ([Path(archive) / rel] if archive else [])
        found = [c for c in cands if c.is_file()]
        if not found:
            problems.append(f"missing {rel}")
            continue
        n += 1
        for c in found:
            if sha256_file(c) != e["sha256"]:
                problems.append(f"hash mismatch {c}")
            elif sum(1 for _ in open_trail(c)) != e["events"]:
                problems.append(f"event count differs {c}")
    # hot files: the chain inside each, and each local file must still start with its archive mirror
    for f in sorted((master / "audit").glob("*/*/*.jsonl*")):
        if f.suffix in (".lock", ".tmp"):
            continue
        with open_trail(f) as fh:
            for p in chain_problems(fh.read().splitlines(), "/".join(f.parts[-3:])):
                (legacy if legacy is not None and "(legacy" in p else problems).append(p)
        if archive and f.suffix == ".jsonl":
            m = Path(archive) / f.parts[-3] / f.parts[-2] / f.name
            if m.is_file() and not f.read_bytes().startswith(m.read_bytes()):
                problems.append(f"differs from its archive mirror {'/'.join(f.parts[-3:])}")
    return problems, n


# --------------------------------------------------------------- selftest
def selftest():
    real_archive = os.environ.pop("AUDIT_ARCHIVE", None)   # the hook paths default to it: keep tests off the real archive
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        os.environ["AUDIT_DEVICE"] = "testbox"
        f = d / "x.txt"
        f.write_text("hello", encoding="utf-8")
        ev = record(d, "sess-1", "Write", str(f), ts="2026-01-01T10:00:00+00:00")
        assert ev["hash"] == hashlib.sha256(b"hello").hexdigest()[:16] and ev["mode"] == "manual"
        p = d / "audit" / "testbox" / "2026-01-01" / "sess-1.jsonl"
        assert p.is_file() and len(p.read_text(encoding="utf-8").splitlines()) == 1, p
        # the writer refuses content
        try:
            record(d, "sess-1", "note", detail={"text": "x" * (MAX_FIELD + 1)})
            raise AssertionError("content was accepted")
        except ValueError:
            pass
        # hook payloads: PostToolUse with Bash never records the command
        tr = d / "t.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "message": {"model": "m-1", "usage": {
            "input_tokens": 5, "output_tokens": 7, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 3},
            "content": [{"type": "tool_use", "name": "Read"}, {"type": "tool_use", "name": "Write"}]}}) + "\n" +
            json.dumps({"type": "assistant", "message": {"model": "m-1", "usage": {"input_tokens": 1, "output_tokens": 1},
                        "content": []}}) + "\n", encoding="utf-8")
        ev = handle_hook(d, {"hook_event_name": "PostToolUse", "session_id": "sess-2", "transcript_path": str(tr),
                             "tool_name": "Bash", "tool_input": {"command": "rm -rf secret " * 50}})
        assert ev["mode"] == "hook" and ev["actor"]["model"] == "m-1" and "command" not in json.dumps(ev["detail"]).replace("command_", "")
        assert ev["detail"]["command_len"] == 700
        ev = handle_hook(d, {"hook_event_name": "PostToolUse", "session_id": "sess-2", "transcript_path": str(tr),
                             "tool_name": "Write", "tool_input": {"file_path": str(f)}, "tool_response": {"is_error": True}})
        assert ev["outcome"] == "error" and ev["target"] == str(f)
        ev = handle_hook(d, {"hook_event_name": "SessionEnd", "session_id": "sess-2", "transcript_path": str(tr), "reason": "exit"})
        u = ev["detail"]["usage"]
        assert u == {"input": 6, "output": 8, "cache_read": 100, "cache_create": 3, "turns": 2}, u
        assert ev["detail"]["files_read"] == 1 and ev["detail"]["files_written"] == 1
        assert handle_hook(d, {"hook_event_name": "Whatever"}) is None
        # query filters
        assert len(query(d)) == 4
        assert [e["action"] for e in query(d, session="sess-2")] == ["Bash", "Write", "session_end"]
        assert len(query(d, action="Write")) == 2 and len(query(d, path=str(f))) == 2
        assert query(d, since="2026-01-02") and not query(d, until="2025-12-31")
        assert query(d, device="nope") == []
        render(query(d))
        # acceptance 1: two devices touch one file; the trail alone reconstructs the order
        f.write_text("edited on the laptop", encoding="utf-8")
        os.environ["AUDIT_DEVICE"] = "laptop"
        record(d, "sess-9", "Edit", str(f), ts="2026-01-01T11:00:00+00:00")
        os.environ["AUDIT_DEVICE"] = "testbox"
        hist = {(e["device"], e["session"]): e["hash"] for e in query(d, path=str(f))}
        assert set(hist) == {("testbox", "sess-1"), ("testbox", "sess-2"), ("laptop", "sess-9")}, hist
        assert hist[("laptop", "sess-9")] != hist[("testbox", "sess-1")]          # who changed it, and when, from the trail alone
        # rotation: the SessionEnd hook above already compressed the January sess-1 file (it is
        # 7+ days old for real); nothing is compressed for today; manifest written; verify + query read it back
        assert (d / "audit" / "testbox" / "2026-01-01" / "sess-1.jsonl.xz").is_file() and not p.exists()
        assert rotate(d, days=7, today="2026-01-01") == []
        log = rotate(d, days=7, today="2027-01-01")
        assert len(log) == 2 and all(l.startswith("compressed") for l in log), log
        assert not list((d / "audit").glob("*/*/*.jsonl")) and len(list((d / "audit").glob("*/*/*.jsonl.xz"))) == 3
        man = read_manifest(d)
        assert man["testbox/2026-01-01/sess-1.jsonl.xz"]["events"] == 1 and sum(e["events"] for e in man.values()) == 5
        assert man["testbox/2026-01-01/sess-1.jsonl.xz"]["first"] == "2026-01-01T10:00:00+00:00"
        assert len(query(d)) == 5 and verify(d) == ([], 3)
        assert rotate(d, days=7, today="2027-01-01") == []                                  # idempotent
        # ship to an archive after 90 days, delete local only after the copy verifies, then restore-test it
        nas = d / "nas"
        log = rotate(d, days=7, ship_after=90, archive=nas, today="2027-06-01")
        assert len(log) == 3 and all(l.startswith("shipped") for l in log), log
        assert not list((d / "audit").glob("*/*/*.jsonl.xz")) and len(list(nas.glob("*/*/*.jsonl.xz"))) == 3
        assert verify(d) == (["missing " + k for k in man], 0)                             # without the archive: gone
        assert verify(d, archive=nas) == ([], 3) and len(query(d, archive=nas)) == 5      # with it: intact, queryable
        (nas / "testbox" / "2026-01-01" / "sess-1.jsonl.xz").write_bytes(b"tampered")
        assert verify(d, archive=nas)[0] == ["hash mismatch " + str(nas / "testbox" / "2026-01-01" / "sess-1.jsonl.xz")]
        record(d, "sess-1", "note", ts="2026-02-01T12:00:00+00:00")                        # a new day, compressed...
        assert len(rotate(d, today="2027-01-01")) == 1
        log = rotate(d, archive=f / "nas", ship_after=0, today="2027-06-01")             # ...but the archive is offline
        assert log == [l for l in log if l.startswith("ship deferred")] and len(log) == 1, log
        assert (d / "audit" / "testbox" / "2026-02-01" / "sess-1.jsonl.xz").is_file()      # nothing lost
        # the manifest never carries content either
        assert all(len(v) <= MAX_FIELD for e in man.values() for v in e.values() if isinstance(v, str))
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        f = d / "y.txt"
        f.write_text("before", encoding="utf-8")
        # before-hash, real failures with the exit code (never the error text), connector targets
        pre = handle_hook(d, {"hook_event_name": "PreToolUse", "session_id": "s", "tool_name": "Write",
                              "tool_input": {"file_path": str(f)}, "tool_use_id": "toolu_1"})
        f.write_text("after", encoding="utf-8")
        post = handle_hook(d, {"hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Write",
                               "tool_input": {"file_path": str(f)}, "tool_use_id": "toolu_1"})
        assert pre["action"] == "before:Write" and pre["hash"] == hashlib.sha256(b"before").hexdigest()[:16]
        assert post["hash"] != pre["hash"] and post["detail"]["id"] == pre["detail"]["id"] == "toolu_1"
        fail = handle_hook(d, {"hook_event_name": "PostToolUseFailure", "session_id": "s", "tool_name": "Bash",
                               "tool_input": {"command": "false"}, "error": "Exit code 1\nsecret output"})
        assert fail["outcome"] == "error" and fail["detail"]["exit"] == "1" and "secret" not in json.dumps(fail)
        mcp = handle_hook(d, {"hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "mcp__drive__trash_file",
                              "tool_input": {"fileId": "abc123"}})
        assert mcp["target"] == "fileId=abc123" and mcp["detail"]["server"] == "drive"
        assert record(d, "s", "note", actor="codex")["actor"]["assistant"] == "codex"
        # the chain: intact verifies; an edited line, a deleted line, both break it
        trail = trail_path(d, "s")
        lines = trail.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 5 and json.loads(lines[0])["prev"] == "" and verify(d) == ([], 0)
        trail.write_text("\n".join([lines[0], lines[1].replace('"ok"', '"error"')] + lines[2:]) + "\n", encoding="utf-8")
        assert any("chain broken" in p for p in verify(d)[0]), verify(d)
        trail.write_text("\n".join(lines[:2] + lines[3:]) + "\n", encoding="utf-8")
        assert any("chain broken" in p for p in verify(d)[0])
        trail.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # archive mirror at session end: the local file may grow, never change
        nas = d / "nas"
        assert mirror_session(d, "s", archive=nas)[0].startswith("mirrored ")
        record(d, "s", "note")
        assert verify(d, archive=nas) == ([], 0)
        m = nas / trail.parts[-3] / trail.parts[-2] / trail.name
        m.write_text(m.read_text(encoding="utf-8").replace('"note"', '"edit"'), encoding="utf-8")
        assert any("archive mirror" in p for p in verify(d, archive=nas)[0])
        # git snapshot: None outside a repo, the head and dirty count inside one
        assert git_snapshot(d) is None
        import subprocess
        if subprocess.run(["git", "init", "-q", str(d / "r")]).returncode == 0:
            (d / "r" / "a").write_text("x", encoding="utf-8")
            snap = git_snapshot(d / "r")
            assert snap and snap["dirty"] == 1 and snap["repo"] == "r", snap
        # the manifest rotate() appended is committed and pushed alone; another session's staged file stays staged
        bare, c = d / "origin.git", d / "c"

        def run(*a):
            return subprocess.run(["git", *a], capture_output=True, text=True)
        if run("init", "-q", "--bare", "-b", "main", str(bare)).returncode == 0:
            run("clone", "-q", str(bare), str(c))
            for k, v in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false")):
                run("-C", str(c), "config", k, v)
            run("-C", str(c), "checkout", "-q", "-b", "main")
            (c / MANIFEST).write_text("{}\n", encoding="utf-8")
            (c / "other").write_text("x", encoding="utf-8")
            run("-C", str(c), "add", MANIFEST, "other")
            run("-C", str(c), "commit", "-q", "-m", "init")
            run("-C", str(c), "push", "-q", "origin", "main")
            assert commit_manifest(c) is None                                              # clean: nothing to do
            (c / MANIFEST).write_text("{}\n{}\n", encoding="utf-8")
            (c / "other").write_text("staged by another session", encoding="utf-8")
            run("-C", str(c), "add", "other")
            assert commit_manifest(c) == "committed and pushed"
            assert run("-C", str(c), "status", "--porcelain").stdout.split() == ["M", "other"]
            assert run("--git-dir", str(bare), "show", "main:" + MANIFEST).stdout == "{}\n{}\n"
            assert commit_manifest(d) is None                                              # not a repo: no-op
    del os.environ["AUDIT_DEVICE"]
    if real_archive is not None:
        os.environ["AUDIT_ARCHIVE"] = real_archive
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["hook", "record", "session-end", "query", "rotate", "verify", "selftest"])
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    ap.add_argument("--session", default=os.environ.get("CLAUDE_SESSION_ID", ""))
    ap.add_argument("--action"); ap.add_argument("--target"); ap.add_argument("--outcome", default="ok")
    ap.add_argument("--approval"); ap.add_argument("--provider"); ap.add_argument("--transcript")
    ap.add_argument("--actor", help="the assistant or interface recording (codex, chat, cowork...); env AUDIT_ACTOR")
    ap.add_argument("--since"); ap.add_argument("--until"); ap.add_argument("--path"); ap.add_argument("--device")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--archive", default=os.environ.get("AUDIT_ARCHIVE"), help="cold tier (a second disk or NAS); also env AUDIT_ARCHIVE")
    ap.add_argument("--days", type=int, default=HOT_DAYS); ap.add_argument("--ship-after", type=int, default=WARM_DAYS)
    a = ap.parse_args()
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "hook":
        try:
            raw = sys.stdin.read().lstrip("﻿")
            handle_hook(a.master, json.loads(raw) if raw.strip() else {})
        except Exception as e:                    # a hook must never break the session
            print(f"audit: {e}", file=sys.stderr)
        return 0
    if a.cmd == "record":
        if not a.action:
            ap.error("--action is required")
        ev = record(a.master, a.session, a.action, a.target, a.outcome, "manual",
                    approval=a.approval, provider=a.provider, actor=a.actor)
        print(json.dumps(ev))
        return 0
    if a.cmd == "session-end":
        if not a.transcript:
            ap.error("--transcript is required")
        print(json.dumps(session_end(a.master, a.session, a.transcript)))
        return 0
    if a.cmd == "rotate":
        print("\n".join(rotate(a.master, a.days, a.ship_after, a.archive)) or "(nothing to rotate)")
        return 0
    if a.cmd == "verify":
        legacy = []
        problems, n = verify(a.master, a.archive, legacy)
        print("\n".join(legacy + problems + ([] if problems else [f"manifest ok: {n} archive(s) verified, chains intact"])))
        return 1 if problems else 0
    evs = query(a.master, a.since, a.until, a.session, a.action, a.path, a.device, a.archive)
    print("\n".join(json.dumps(e) for e in evs) if a.json else render(evs))
    return 0


if __name__ == "__main__":
    sys.exit(main())

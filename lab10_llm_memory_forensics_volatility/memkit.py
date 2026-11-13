"""
memkit.py - Sectra Memory Analyst: a memory-forensics agent over Volatility 3.

THE IDEA
--------
Volatility already gives an examiner a list of plugins (pslist, pstree, malfind, ...). Here that
plugin list IS the agent's toolset. The analyst asks a question in plain English; the language model
picks ONE plugin and its arguments; our code runs `vol -r json -f <image> <plugin>`; the model reads
the result and either runs another plugin or answers, citing the plugin and the PID it relied on.

DESIGN RULES (the same evidence discipline as the rest of the course)
---------------------------------------------------------------------
- A fixed WHITELIST of read-only Volatility plugins. The model can only choose from it; nothing is
  passed to a shell, and arguments are validated (a PID must be a number).
- Every plugin runs ONCE per image and is cached; later questions reuse the cached result.
- Output is filtered (by PID or keyword) and capped, so the model is not flooded.
- A malfind hit is a LEAD, not proof. Every claim must cite the plugin and PID behind it.
- Volatility 3's network plugins do not support Windows XP; on XP, search_memory (vadregexscan) finds
  network indicators inside process memory instead.

Reuses the shared agent loop in agentkit (connect_model, run_agent, run_agent_iter).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import agentkit as ak

connect_model = ak.connect_model   # 'groq' (default; same free key as Labs 01-06), 'openrouter', 'ollama'


run_agent = ak.run_agent
run_agent_iter = ak.run_agent_iter
answer_text = ak.answer_text

MAX_ROWS = 40          # rows shown to the model per call
MAX_CHARS = 3500       # hard cap on one observation

# ------------------------------------------------------------------ the public sample image
# Cridex: a classic Windows XP memory image of a banking-trojan infection, widely used to teach
# memory forensics, with publicly documented ground truth. 40 MB download, 512 MB unpacked.
SAMPLE = {
    "name": "cridex",
    "url": "https://github.com/Divinemonk/memory_forensics_with_volatility/releases/download/mem_sample/cridexmemdump.zip",
    "zip_sha256": "6453d0986352f7d5287cb90eeb6b72bc7bc16b03e964bb5767d93f85c3a483b2",
    "image": "cridex.vmem",
    "image_md5": "7494f3b77db1525c1974f5380744ae46",
}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_sample(dest="memory", force=False):
    """Download the public Cridex memory image, verify its hashes, and unzip it. Returns the image path."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    image = dest / SAMPLE["image"]
    if image.exists() and not force:
        print(f"Already have {image} ({image.stat().st_size // (1 << 20)} MB).")
        return str(image)
    zpath = dest / "cridexmemdump.zip"
    print("Downloading the Cridex sample (about 40 MB)...")
    try:
        import requests
        with requests.get(SAMPLE["url"], stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(zpath, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    except ImportError:
        import urllib.request
        try:
            urllib.request.urlretrieve(SAMPLE["url"], zpath)
        except Exception as e:
            raise RuntimeError(f"Download failed ({e}). Run `pip install requests` and try again.") from e
    got = _sha256(zpath)
    if got != SAMPLE["zip_sha256"]:
        raise RuntimeError(f"Download hash mismatch ({got}); the file may have changed. Not using it.")
    with zipfile.ZipFile(zpath) as z:
        z.extract(SAMPLE["image"], dest)
    zpath.unlink()
    md5 = _md5(image)
    if md5 != SAMPLE["image_md5"]:
        raise RuntimeError(f"{image} has MD5 {md5}, not the published {SAMPLE['image_md5']}. Not using it.")
    print(f"Verified {image}: MD5 {md5} (matches the published sample).")
    return str(image)


# ------------------------------------------------------------------ the toolset: whitelisted plugins
# name -> spec. vol: candidate plugin names (newest first; Volatility renames some between versions).
# pid: None (not used) / "optional" / "required". keyword: None / "optional" / "required".
PLUGINS = {
    "info": dict(vol=["windows.info"], cols=["Variable", "Value"],
                 doc="OS version, build, and capture time of the memory image. A good first step."),
    "pslist": dict(vol=["windows.pslist"], pid="optional",
                   cols=["PID", "PPID", "ImageFileName", "Threads", "Handles", "CreateTime", "ExitTime"],
                   doc="Running processes from the active process list (PID, parent PID, name, start time)."),
    "pstree": dict(vol=["windows.pstree"], tree=True,
                   cols=["PID", "PPID", "ImageFileName", "CreateTime"],
                   doc="Processes as a parent/child tree: shows which process launched which."),
    "psscan": dict(vol=["windows.psscan"], pid="optional",
                   cols=["PID", "PPID", "ImageFileName", "CreateTime", "ExitTime"],
                   doc="Scans raw memory for process objects, including exited or hidden ones pslist misses."),
    "psxview": dict(vol=["windows.malware.psxview", "windows.psxview"], pid="optional",
                    doc="Cross-checks several process lists; a process missing from a view may be hidden."),
    "cmdline": dict(vol=["windows.cmdline"], pid="optional", cols=["PID", "Process", "Args"],
                    doc="The command line each process was started with."),
    "dlllist": dict(vol=["windows.dlllist"], pid="required", keyword="optional",
                    cols=["PID", "Process", "Name", "Path"],
                    doc="DLLs loaded by ONE process (needs pid; optional keyword filters by name/path)."),
    "ldrmodules": dict(vol=["windows.malware.ldrmodules", "windows.ldrmodules"], pid="required",
                       doc="Modules mapped in ONE process and whether each loader list knows them (False = possibly unlinked/hidden). Needs pid."),
    "handles": dict(vol=["windows.handles"], pid="required", keyword="optional",
                    cols=["PID", "Process", "Type", "Name"],
                    doc="Open handles (files, registry keys, mutexes...) of ONE process (needs pid; optional keyword)."),
    "malfind": dict(vol=["windows.malware.malfind", "windows.malfind"], pid="optional",
                    doc="Memory regions that look like injected code (executable, private, often with a PE 'MZ' header). A hit is a LEAD, not proof."),
    "mutantscan": dict(vol=["windows.mutantscan"], keyword="optional",
                       doc="Named mutexes in memory; malware often creates distinctive ones (optional keyword filter)."),
    "svcscan": dict(vol=["windows.svcscan"], keyword="optional",
                    doc="Windows services: name, state, and binary path (optional keyword filter)."),
    "filescan": dict(vol=["windows.filescan"], keyword="required",
                     doc="File objects in memory. Needs a keyword (e.g. '.exe', 'Temp', 'Adobe') because the list is long."),
    "hivelist": dict(vol=["windows.registry.hivelist"], cols=["Offset", "FileFullPath"],
                     doc="Registry hives loaded in memory."),
    "getsids": dict(vol=["windows.getsids"], pid="optional", cols=["PID", "Process", "SID", "Name"],
                    doc="Which user and group SIDs a process runs as."),
    "envars": dict(vol=["windows.envars"], pid="required", keyword="optional",
                   cols=["PID", "Process", "Variable", "Value"],
                   doc="Environment variables of ONE process (needs pid)."),
    "netscan": dict(vol=["windows.netscan"], pid="optional",
                    doc="Network connections and listening sockets (Windows Vista and later ONLY; on XP use search_memory)."),
}

_NOISY = {"__children", "File output", "Hexdump", "Disasm", "Notes"}
_HEXCOLS = {"Offset", "Offset(V)", "Offset(P)", "Base", "Start VPN", "End VPN", "Physical Address"}


def _vol_version():
    """The installed Volatility 3 version (part of the plugin-check cache key)."""
    try:
        from importlib.metadata import version
        return version("volatility3")
    except Exception:
        return "unknown"


def _vol_cmd():
    """Find the Volatility 3 command-line entry point installed with `pip install volatility3`."""
    here = Path(sys.executable).with_name("vol")
    if here.exists():
        return str(here)
    found = shutil.which("vol")
    if found:
        return found
    raise RuntimeError("Volatility 3 is not installed. Run: pip install volatility3")


def _flatten(rows, depth=0):
    """Flatten Volatility's nested __children (pstree) into rows with a depth marker."""
    out = []
    for r in rows:
        r = dict(r)
        if "PID" not in r and "Pid" in r:      # e.g. ldrmodules names its column Pid, not PID
            r["PID"] = r["Pid"]
        kids = r.pop("__children", []) or []
        r["_depth"] = depth
        out.append(r)
        out += _flatten(kids, depth + 1)
    return out


def _fmt_cell(col, val):
    if val is None or val == "None":
        return "-"
    if col in _HEXCOLS and isinstance(val, int):
        return hex(val)
    s = str(val).replace("\t", " ").replace("\n", " ")
    return s if len(s) <= 120 else s[:117] + "..."


class VolRunner:
    """Runs whitelisted plugins once per image and caches the JSON rows."""

    def __init__(self, image, cache_dir=".volcache", ran=None):
        self.image = str(image)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.mem = {}
        self.ran = ran if ran is not None else []   # audit trail: every Volatility command used (shareable)

    def _log(self, plugin, extra, label):
        entry = "vol -f <image> " + " ".join([plugin, label or " ".join(extra)]).strip()
        if entry not in self.ran:
            self.ran.append(entry)

    def _key(self, plugin, extra):
        h = hashlib.sha1(f"{self.image}|{plugin}|{extra}".encode()).hexdigest()[:16]
        return self.cache_dir / f"{plugin.replace('.', '_')}_{h}.json"

    def run(self, candidates, extra=(), label=None):
        """Run the first plugin name this Volatility version knows; return (rows, plugin_used, error).
        label: a short human-readable stand-in for long arguments in the audit trail."""
        last_err = ""
        for plugin in candidates:
            key = self._key(plugin, "|".join(extra))
            if key in self.mem:
                self._log(plugin, extra, label)
                return self.mem[key], plugin, None
            if key.exists():
                rows = json.loads(key.read_text())
                self.mem[key] = rows
                self._log(plugin, extra, label)
                return rows, plugin, None
            cmd = [_vol_cmd(), "-q", "-r", "json", "-f", self.image, plugin, *extra]
            # no colour codes: notebooks make Python print coloured tracebacks, which hide the error text
            env = dict(os.environ, NO_COLOR="1", PYTHON_COLORS="0", TERM="dumb")
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
            if p.returncode == 0 and p.stdout.strip().startswith("["):
                rows = _flatten(json.loads(p.stdout))
                key.write_text(json.dumps(rows))
                self.mem[key] = rows
                self._log(plugin, extra, label)
                return rows, plugin, None
            raw = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", p.stderr or p.stdout or "")   # strip any ANSI codes
            err = raw.strip().splitlines()
            last_err = " | ".join(err[-25:]) if err else f"exit code {p.returncode}"
            if "invalid choice" not in last_err:
                break                       # a real failure, not just an unknown plugin name
        return None, candidates[0], last_err


def _table(rows, cols=None, limit=MAX_ROWS, tree=False):
    if not rows:
        return "(no rows)"
    cols = cols or [c for c in rows[0] if c not in _NOISY and not c.startswith("_")]
    lines = ["\t".join(cols)]
    for r in rows[:limit]:
        cells = [_fmt_cell(c, r.get(c)) for c in cols]
        if tree and r.get("_depth"):
            cells[0] = "." * r["_depth"] + cells[0]
        lines.append("\t".join(cells))
    if len(rows) > limit:
        lines.append(f"... {len(rows) - limit} more rows not shown. Narrow it with pid= or keyword=.")
    return "\n".join(lines)


def _malfind_view(rows):
    """malfind rows are huge (hexdump + disassembly); keep what an examiner reads first."""
    if not rows:
        return "(no suspicious regions found)"
    lines = ["PID\tProcess\tStart\tProtection\tPE header?\tfirst bytes"]
    for r in rows[:MAX_ROWS]:
        dump = (r.get("Hexdump") or "").replace("\n", " ")
        first = " ".join(dump.split()[:16])
        mz = "YES (MZ - a PE file in memory)" if "4d 5a 90 00" in dump[:200] else "no"
        lines.append(f"{r.get('PID')}\t{r.get('Process')}\t{_fmt_cell('Start VPN', r.get('Start VPN'))}\t"
                     f"{r.get('Protection')}\t{mz}\t{first}")
    if len(rows) > MAX_ROWS:
        lines.append(f"... {len(rows) - MAX_ROWS} more regions. Narrow with pid=.")
    return "\n".join(lines)


def _clip(text):
    return text if len(text) <= MAX_CHARS else text[:MAX_CHARS] + "\n...[truncated - narrow with pid= or keyword=]"


# ------------------------------------------------------------------ plugin compatibility check
def _short_reason(err):
    """Volatility's own error message (the last 'XxxError: ...'), not the traceback's source lines."""
    found = [m for m in re.findall(r"(?:Error|Exception):\s*([^|]+)", err or "") if "{" not in m]
    if found:
        return found[-1].strip()[:90]
    parts = [p.strip() for p in (err or "").split("|") if p.strip() and "{" not in p]
    return (parts[-1] if parts else "failed")[:90]


def check_plugins(image, cache_dir=".volcache", verbose=True):
    """Run every whitelisted plugin ONCE on this image and report which ones return data.

    Not every plugin supports every image (for example, Volatility 3's netscan does not support
    Windows XP). The lab gives the agent only the plugins that work on THIS image, so it never wastes
    a step on one that cannot answer. Results are cached, and the runs also warm the plugin cache, so
    later questions are instant. Returns {name: {"status": ok|empty|unsupported, "rows": n, "note": ...}}."""
    vr = VolRunner(image, cache_dir)
    tag = hashlib.sha1(f"{Path(image).resolve()}|{os.path.getsize(image)}|{_vol_version()}".encode()).hexdigest()[:16]
    key = Path(cache_dir) / f"compat_{tag}.json"
    # Only results that WORKED are cached. A failure is re-checked each time, so a one-off problem
    # (a symbol download that timed out, say) never removes a plugin for good.
    cached = json.loads(key.read_text()) if key.exists() else {}
    result = {n: r for n, r in cached.items() if n in PLUGINS and r.get("status") in ("ok", "empty")}
    todo = [n for n in PLUGINS if n not in result]
    if todo:
        if verbose:
            print(f"Checking {len(todo)} plugins against {Path(image).name} (working results are cached)...")
        for name in todo:
            spec = PLUGINS[name]
            rows, used, err = vr.run(spec["vol"])
            if err:
                status, note = "unsupported", _short_reason(err)
            elif not rows:
                status, note = "empty", "ran, but returned no rows on this image"
            else:
                status, note = "ok", f"{len(rows)} rows"
            result[name] = {"status": status, "plugin": used, "rows": len(rows or []), "note": note}
            if verbose:
                print(f"  {'OK ' if status == 'ok' else '-- '} {name:11} {note}")
        key.parent.mkdir(parents=True, exist_ok=True)
        key.write_text(json.dumps({n: r for n, r in result.items() if r["status"] in ("ok", "empty")}))
        result = {n: result[n] for n in PLUGINS}   # keep the whitelist order
    if verbose:
        ok = [n for n, r in result.items() if r["status"] == "ok"]
        print(f"{len(ok)} of {len(result)} plugins work on this image and become the agent's tools.")
        for n, r in result.items():
            if r["status"] != "ok":
                print(f"  left out: {n} ({r['status']}: {r['note']})")
    return result


# ------------------------------------------------------------------ build the agent's tools
def make_memory_tools(image, case_dir="case", cache_dir=".volcache", findings=None, ran=None,
                      compatible_only=False, compat=None):
    """Return {tool_name: function}. One tool per whitelisted plugin, plus search_memory, the case brief,
    and the findings log. `findings` collects recorded findings; `ran` collects the Volatility commands
    used (pass your own lists to keep them across calls, e.g. one chat session).
    compatible_only=True keeps only the plugins check_plugins() found working on this image."""
    vr = VolRunner(image, cache_dir, ran=ran)
    if compatible_only:
        compat = compat or check_plugins(image, cache_dir, verbose=False)
    findings = findings if findings is not None else []
    case_dir = Path(case_dir)
    tools = {}

    def make_plugin_tool(name, spec):
        def tool(pid=None, keyword=None):
            if pid in ("", "None"):
                pid = None
            if pid is not None:
                try:
                    pid = int(pid)
                except (TypeError, ValueError):
                    return f"pid must be a number, got {pid!r}."
            if spec.get("pid") == "required" and pid is None:
                return f"{name} needs a pid (one process). Find candidate PIDs with pslist or pstree first."
            if spec.get("keyword") == "required" and not keyword:
                return f"{name} needs a keyword (for example '.exe' or 'Temp') because its output is long."
            rows, used, err = vr.run(spec["vol"])
            if err:
                if name == "netscan":
                    return ("netscan failed on this image. Volatility 3's network plugins only support Windows "
                            "Vista and later; on Windows XP use search_memory(kind='ip') to find network "
                            f"indicators inside process memory. (Volatility said: {_short_reason(err)})")
                return f"{used} failed: {_short_reason(err)}"
            if name == "info":                 # drop the local symbol-cache path (noise, not evidence)
                rows = [r for r in rows if r.get("Variable") != "Symbols"]
            if pid is not None and spec.get("pid"):
                rows = [r for r in rows if str(r.get("PID", r.get("Pid"))) == str(pid)]
            if keyword:
                k = str(keyword).lower()
                rows = [r for r in rows if k in " ".join(str(v) for v in r.values()).lower()]
            body = _malfind_view(rows) if name == "malfind" else _table(rows, spec.get("cols"), tree=spec.get("tree"))
            shown_pid = f" --pid {pid}" if pid is not None and spec.get("pid") else ""
            shown_kw = f" | filter: {keyword}" if keyword else ""
            head = f"[{used}{shown_pid}{shown_kw}] {len(rows)} rows\n"
            return _clip(head + body)

        args = []
        if spec.get("pid"):
            args.append("pid" + ("" if spec["pid"] == "required" else "=optional"))
        if spec.get("keyword"):
            args.append("keyword" + ("" if spec["keyword"] == "required" else "=optional"))
        tool.__doc__ = f"({', '.join(args)}) {spec['doc']}" if args else spec["doc"]
        tool.__name__ = name
        return tool

    for name, spec in PLUGINS.items():
        if compat and compat.get(name, {}).get("status") != "ok":
            continue                         # not working on this image: the agent never sees it
        tools[name] = make_plugin_tool(name, spec)

    def search_memory(kind="ip", text="", pid=None):
        """(kind='ip'|'url'|'text', text=optional, pid=optional) Search inside PROCESS memory (windows.vadregexscan) for network indicators (ip = IP:port), URLs, or a literal text, and show which process holds each hit."""
        patterns = {
            "ip": r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])(?:\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])){3}:[0-9]{2,5}",
            "url": r"https?://[A-Za-z0-9./_?=&%-]{4,80}",
        }
        if text:
            pattern, label = re.escape(str(text)), f"text {text!r}"
        elif kind in patterns:
            pattern, label = patterns[kind], kind
        else:
            return "kind must be 'ip' or 'url', or pass text='...' to search for a literal string."
        extra = ["--pattern", pattern]
        if pid not in (None, "", "None"):
            try:
                extra += ["--pid", str(int(pid))]
            except (TypeError, ValueError):
                return f"pid must be a number, got {pid!r}."
        rows, used, err = vr.run(["windows.vadregexscan"], tuple(extra), label=f"--pattern <{label}>")
        if err:
            return f"search failed: {_short_reason(err)}"
        seen = {}
        for r in rows:
            t = str(r.get("Text", ""))
            k = (r.get("PID"), r.get("Process"), t)
            seen[k] = seen.get(k, 0) + 1
        if not seen:
            return f"[windows.vadregexscan] no {label} found in process memory."
        lines = [f"[windows.vadregexscan pattern={label}] {len(rows)} hits, {len(seen)} distinct (PID / process / text / count):"]
        for (p, proc, t), n in sorted(seen.items(), key=lambda kv: -kv[1])[:30]:
            lines.append(f"{p}\t{proc}\t{t}\tx{n}")
        return _clip("\n".join(lines))

    tools["search_memory"] = search_memory

    def case_brief():
        """The case brief: what happened, what was collected, and what the investigator needs answered."""
        p = case_dir / "case_brief.md"
        return p.read_text() if p.exists() else "No case brief found (case/case_brief.md)."

    def record_finding(finding, evidence):
        """(finding, evidence) Write a confirmed finding to the case log, with the plugin + PID that supports it."""
        if not finding or not evidence:
            return "A finding needs both the finding text and the evidence (plugin + PID) behind it."
        findings.append({"finding": str(finding), "evidence": str(evidence)})
        return f"Recorded finding #{len(findings)}."

    def findings_report():
        """Produce the findings report from everything recorded in the case log so far."""
        lines = ["FINDINGS REPORT (memory analysis)", "=" * 34,
                 f"Image: {Path(vr.image).name}", ""]
        if not findings:
            lines.append("(No findings recorded yet. Use record_finding as you confirm each one.)")
        for i, f in enumerate(findings, 1):
            lines.append(f"{i}. {f['finding']}\n   Evidence: {f['evidence']}")
        lines += ["", "Volatility commands run:"] + [f"  {c}" for c in vr.ran] + [
            "", "Note: findings are bounded by memory evidence. A malfind hit or a string in memory is a lead; "
            "confirm with disk, network, and malware analysis before attributing intent."]
        return "\n".join(lines)

    tools["case_brief"] = case_brief
    tools["record_finding"] = record_finding
    tools["findings_report"] = findings_report
    tools["_runner"] = vr               # not a tool; exposed for notebooks (stripped from the prompt)
    tools["_compat"] = compat or {}     # not a tool; the compatibility check, summarised in the prompt
    return tools


def agent_tools(tools):
    """The tools the model may call (drops private helpers like _runner)."""
    return {k: v for k, v in tools.items() if not k.startswith("_")}


def tool_descriptions(tools):
    return "\n".join(f"- {n}: {(fn.__doc__ or '').strip().splitlines()[0]}" for n, fn in agent_tools(tools).items())


def _compat_note(tools):
    compat = tools.get("_compat") or {}
    if not compat:
        return ""
    left = [f"{n} ({r['status']}: {r['note']})" for n, r in compat.items() if r["status"] != "ok"]
    note = "PLUGIN CHECK: every plugin tool above was tested on this image and returns data."
    if left:
        note += (" Left out: " + "; ".join(left) + ". An 'empty' plugin found nothing on this image, which is "
                 "itself a result you may report. For network indicators, use search_memory.")
    return note + "\n\n"


def build_memory_system_prompt(tools, case_name="the case"):
    return (
        f"You are Sectra, a memory-forensics analyst working {case_name}. You investigate a Windows memory "
        "image with Volatility 3. You cannot see memory directly: you learn ONLY by running the plugins below, "
        "and you must base every statement on what they return.\n\n"
        "TOOLS (each Volatility plugin is a tool; use exactly ONE per step):\n" + tool_descriptions(tools) + "\n\n"
        + _compat_note(tools) +
        "HOW TO REPLY: send ONE JSON object and nothing else.\n"
        "To run a plugin:\n"
        '  {"thought": "<one short sentence>", "action": "pstree", "action_input": {}}\n'
        '  {"thought": "<one short sentence>", "action": "dlllist", "action_input": {"pid": 1640}}\n'
        "When you can answer the investigator:\n"
        '  {"thought": "<one short sentence>", "final_answer": "<answer>", "evidence_path": "<plugin + PID you relied on>"}\n\n'
        "HOW TO WORK THE CASE:\n"
        "1. Pick the plugin that answers the question most directly (process questions: pslist/pstree; code "
        "injection: malfind; what a process loaded: dlllist/ldrmodules; network on Windows XP: search_memory).\n"
        "2. Read the result, then corroborate before concluding: a suspicious finding should be supported by "
        "a second plugin (for example malfind plus pstree plus cmdline).\n"
        "3. When something is confirmed, record it with record_finding (finding + plugin + PID).\n\n"
        "RULES: cite the plugin and PID in evidence_path; a malfind hit is a LEAD, not proof (system processes "
        "like csrss.exe and winlogon.exe often show benign hits); never name a malware family or claim intent "
        "unless the plugin output supports it; say plainly what memory cannot establish; keep thoughts to one "
        "sentence and answers short. /no_think"
    )


def quick_agent(question, client, model, tools, history=None, **kw):
    prompt = build_memory_system_prompt(tools)
    return run_agent(question, client, model, agent_tools(tools), prompt, history=history, **kw)

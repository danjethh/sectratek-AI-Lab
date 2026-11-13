"""
agentkit.py - the shared forensic-agent core used by the Lab 07-10 notebooks and chatbots.

One place defines: how to connect to a model (Groq, OpenRouter or Ollama), how to build the
synthetic Android image, the read-only tools the agent may call, the think-act-observe
loop with its evidence check, and a conversational wrapper for the chatbots. The chatbot .py apps import this
module; the teaching notebooks embed the same code inline so students open only one file.
"""
import contextlib
import inspect
import json
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path


def as_text(content):
    """Message content as plain text. Gradio 6 can hand a chat message back as a list of parts
    ([{'type': 'text', 'text': ...}]) instead of a string; every caller goes through this."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join((x.get("text") or x.get("content") or "") if isinstance(x, dict) else str(x)
                       for x in content)
    if isinstance(content, dict):
        return str(content.get("text") or content.get("content") or "")
    return str(content or "")


@contextlib.contextmanager
def sqlite_copy(path):
    """Open a SQLite evidence file WITHOUT touching it: query a temporary copy (with its -wal and
    -journal files, so recent rows are included). Opening the original, even read-only, can create
    -shm/-wal files beside it, and a path with '#' or '?' can be misread as a different file."""
    path = Path(path)
    tmp = Path(tempfile.mkdtemp(prefix="sectra_db_"))
    try:
        shutil.copy2(path, tmp / "evidence.db")
        for side in ("-wal", "-journal"):
            src = path.with_name(path.name + side)
            if src.exists():
                shutil.copy2(src, tmp / ("evidence.db" + side))
        con = sqlite3.connect(tmp / "evidence.db")
        try:
            yield con
        finally:
            con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def read_head(path, n=16):
    """The first n bytes of a file (its 'magic'), without reading the whole file into memory."""
    with open(path, "rb") as f:
        return f.read(n)


# ======================================================================= model backend
# Free models that follow the agent's JSON format, best first. Providers retire models from
# time to time, so connect_model picks the first one your key can actually use, and the
# notebooks print which one it chose. Put your own choice first, or pass model="...".
GROQ_MODELS = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
OPENROUTER_MODELS = ["google/gemma-4-31b-it:free", "nvidia/nemotron-3-ultra-550b-a55b:free"]
NOT_CHAT = ("whisper", "orpheus", "guard", "tts", "embed")   # speech / safety / embedding models


def pick_model(client, preferred, free_only=False):
    """Return the first preferred model this key can use, else the largest chat model it lists."""
    try:
        listed = client.models.list().data
    except Exception:
        return preferred[0]          # cannot list models: try the first choice and let it report
    ids = [m.id for m in listed]
    for m in preferred:
        if m in ids:
            return m
    chat = [m for m in listed if not any(w in m.id.lower() for w in NOT_CHAT)
            and (m.id.endswith(":free") or not free_only)]
    chat.sort(key=lambda m: getattr(m, "context_window", 0) or 0, reverse=True)
    return chat[0].id if chat else preferred[0]


def connect_model(provider="groq", model=None, api_key=None, base_url=None):
    """Return (client, model_id). provider is 'groq' (default), 'openrouter' or 'ollama'.

    groq:       free hosted models, key from https://console.groq.com/keys (the same key as Labs 01-06).
    openrouter: free hosted models, key from https://openrouter.ai/keys.
    ollama:     a Qwen model running locally (https://ollama.com), no key, nothing leaves the PC.

    max_retries=8: the free tiers allow a few thousand tokens per minute. When a step goes over,
    the provider says "try again in N seconds" and the client waits and retries instead of failing.
    """
    from openai import OpenAI
    provider = provider.lower()
    if provider == "ollama":
        base_url = base_url or "http://localhost:11434/v1"
        client = OpenAI(base_url=base_url, api_key="ollama")  # Ollama ignores the key
        return client, (model or "qwen3:8b")
    if provider == "openrouter":
        client = OpenAI(base_url=base_url or "https://openrouter.ai/api/v1",
                        api_key=api_key or os.environ.get("OPENROUTER_API_KEY", ""), max_retries=8)
        return client, (model or pick_model(client, OPENROUTER_MODELS, free_only=True))
    # default: Groq
    client = OpenAI(base_url=base_url or "https://api.groq.com/openai/v1",
                    api_key=api_key or os.environ.get("GROQ_API_KEY", ""), max_retries=8)
    return client, (model or pick_model(client, GROQ_MODELS))


# ======================================================================= synthetic image
def build_image(root="android_image"):
    """Create a tiny, synthetic Android extraction on disk. Everything in it is fictional."""
    ROOT = Path(root)
    text_files = {
        f"{root}/build.prop":
            "# Synthetic build.prop (teaching data, fictional)\n"
            "ro.product.manufacturer=Google\nro.product.brand=google\n"
            "ro.product.model=Pixel 7a\nro.product.device=lynx\nro.product.name=lynx\n"
            "ro.build.version.release=14\nro.build.version.sdk=34\n"
            "ro.build.fingerprint=google/lynx/lynx:14/AP2A.240705.005/2024072800:user/release-keys\n",
        f"{root}/data/system/packages.list":
            "com.google.android.gm 10089 0 /data/user/0/com.google.android.gm default 0 1\n"
            "com.android.providers.contacts 10003 0 /data/user/0/com.android.providers.contacts platform 0 1\n"
            "com.android.providers.telephony 10004 0 /data/user/0/com.android.providers.telephony platform 0 1\n"
            "com.whatsapp 10137 0 /data/user/0/com.whatsapp default 0 1\n"
            "com.instagram.android 10140 0 /data/user/0/com.instagram.android default 0 1\n"
            "org.thoughtcrime.securesms 10142 0 /data/user/0/org.thoughtcrime.securesms default 0 1\n",
        f"{root}/data/system/users/0/settings_secure.xml":
            "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<settings version=\"241\">\n"
            "  <setting id=\"1\" name=\"android_id\" value=\"a1b2c3d4e5f60718\" package=\"android\" />\n"
            "  <setting id=\"2\" name=\"bluetooth_name\" value=\"Pixel 7a\" package=\"com.android.settings\" />\n"
            "  <setting id=\"3\" name=\"device_name\" value=\"Nadia's Pixel 7a\" package=\"com.android.settings\" />\n"
            "</settings>\n",
        f"{root}/data/misc/wifi/WifiConfigStore.xml":
            "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<WifiConfigStoreData>\n  <NetworkList>\n"
            "    <Network><string name=\"SSID\">&quot;HomeNet_5G&quot;</string>"
            "<long name=\"LastConnectedTime\" value=\"1721295600000\" /></Network>\n"
            "    <Network><string name=\"SSID\">&quot;BrightBeans Cafe&quot;</string>"
            "<long name=\"LastConnectedTime\" value=\"1720950000000\" /></Network>\n"
            "    <Network><string name=\"SSID\">&quot;Okafor-Office&quot;</string>"
            "<long name=\"LastConnectedTime\" value=\"1721210400000\" /></Network>\n"
            "  </NetworkList>\n</WifiConfigStoreData>\n",
        # a JSON artifact (many Android apps store prefs/state as JSON)
        f"{root}/data/data/com.whatsapp/files/me.json":
            json.dumps({"jid": "15550143788@s.whatsapp.net", "pushname": "Nadia O",
                        "registered": True, "last_backup": "2024-07-18"}, indent=2),
    }
    for rel, content in text_files.items():
        p = Path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def make_db(rel, schema, inserts):
        p = Path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.unlink()
        con = sqlite3.connect(p)
        con.executescript(schema)
        for sql, params in inserts:
            con.executemany(sql, params)
        con.commit()
        con.close()

    make_db(f"{root}/data/data/com.google.android.gm/databases/accounts.db",
            "CREATE TABLE accounts(name TEXT, type TEXT, last_sync INTEGER);",
            [("INSERT INTO accounts VALUES (?,?,?)",
              [("nadia.okafor@gmail.com", "com.google", 1721295600),
               ("+15550143788", "com.whatsapp", 1721240000)])])
    make_db(f"{root}/data/data/com.android.providers.contacts/databases/contacts2.db",
            "CREATE TABLE contacts(display_name TEXT, phone TEXT, times_contacted INTEGER);",
            [("INSERT INTO contacts VALUES (?,?,?)",
              [("Marcus Webb", "+15550142210", 31), ("Priya Shah", "+15550148890", 12),
               ("Dad", "+15550149001", 54), ("BrightBeans Cafe", "+15550140077", 3),
               ("Alina K (work)", "+15550147325", 20)])])
    make_db(f"{root}/data/data/com.android.providers.telephony/databases/mmssms.db",
            "CREATE TABLE sms(address TEXT, date INTEGER, body TEXT, type INTEGER);",
            [("INSERT INTO sms VALUES (?,?,?,?)",
              [("+15550142210", 1721200000000, "Are we still on for Friday?", 1),
               ("+15550142210", 1721200600000, "Yes, 6pm at the usual place.", 2),
               ("+15550149001", 1721240500000, "Landed safe, call you tonight.", 2),
               ("+15550148890", 1721250000000, "Can you send the invoice?", 1),
               ("+15550149001", 1721299000000, "Thanks Dad, talk soon.", 2)])])
    make_db(f"{root}/data/data/com.whatsapp/databases/msgstore.db",
            "CREATE TABLE messages(chat TEXT, timestamp INTEGER, from_me INTEGER, text TEXT);",
            [("INSERT INTO messages VALUES (?,?,?,?)",
              [("Marcus Webb", 1721260000000, 0, "Did the package arrive?"),
               ("Marcus Webb", 1721260400000, 1, "Not yet, will check tomorrow."),
               ("Priya Shah", 1721280000000, 1, "Sent the files to your email.")])])
    return ROOT


# ======================================================================= the tools
# A text-ish file is one the agent can read as text. Everything else is "binary".
_TEXT_EXT = {".txt", ".xml", ".json", ".prop", ".list", ".log", ".csv", ".ini", ".conf", ".html"}


def make_tools(root="android_image", allow_python=False):
    """Build the read-only toolbox, all sealed inside `root`. Returns {name: function}."""
    ROOT = Path(root)

    def _resolve(path):
        base = ROOT.resolve()
        path = (path or ".").strip().lstrip("/")
        target = base if path in ("", ".") else (ROOT / path).resolve()
        if target != base and base not in target.parents:
            raise ValueError("path is outside the image")
        return target

    def list_dir(path="."):
        """List what is inside a folder (folders shown with a trailing '/')."""
        t = _resolve(path)
        if not t.exists():
            return f"No such path: {path}"
        if t.is_file():
            return f"{path} is a file, not a folder. Use read_file or run_sql."
        items = [e + ("/" if (t / e).is_dir() else "") for e in sorted(os.listdir(t))]
        return "\n".join(items) if items else "(empty folder)"

    def read_file(path, max_chars=1500):
        """Read a file. Pretty-prints JSON; for SQLite databases points you to run_sql;
        for other binary files shows the type and the first bytes."""
        t = _resolve(path)
        if not t.exists() or t.is_dir():
            return f"No such file: {path}"
        head = read_head(t)
        if head[:15] == b"SQLite format 3":
            with sqlite_copy(t) as con:
                tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            return f"[{path} is a SQLite database. Tables: {tables}. Use run_sql with a SELECT query.]"
        ext = t.suffix.lower()
        if ext not in _TEXT_EXT and b"\x00" in head:
            return (f"[{path} is a binary file ({t.stat().st_size} bytes). First bytes (hex): "
                    f"{head.hex(' ')}. It is not readable as text.]")
        text = t.read_text(errors="replace")
        if ext == ".json":
            try:
                text = json.dumps(json.loads(text), indent=2)
            except Exception:
                pass
        return text[:max_chars] + ("" if len(text) <= max_chars else "\n...[truncated]")

    def run_sql(path, query):
        """Run ONE read-only SQL SELECT against a SQLite database and return the rows."""
        t = _resolve(path)
        if not t.exists():
            return f"No such database: {path}"
        q = (query or "").strip().rstrip(";")
        if not q.lower().startswith(("select", "pragma")):
            return "Only read-only SELECT queries are allowed."
        try:
            with sqlite_copy(t) as con:   # a temporary copy: the evidence file is never opened
                cur = con.execute(q)
                cols = [c[0] for c in cur.description] if cur.description else []
                rows = cur.fetchmany(50)
        except Exception as e:
            return f"SQL error: {e}"
        if not rows:
            return "(no rows)"
        return "\n".join([" | ".join(cols)] + [" | ".join(str(c) for c in r) for r in rows])

    def find_files(name):
        """Find files anywhere in the image whose path contains `name` (case-insensitive)."""
        base = ROOT.resolve()
        needle = (name or "").lower()
        hits = []
        for p in sorted(base.rglob("*")):
            if p.is_symlink():
                continue                      # never follow a link out of the image
            if p.is_file() and needle in str(p.relative_to(base)).lower():
                hits.append(str(p.relative_to(base)))
        if not hits:
            return f"No files matched {name!r}."
        return "\n".join(hits[:50]) + ("" if len(hits) <= 50 else f"\n...({len(hits)} total)")

    def search_text(keyword, max_hits=20):
        """Search the text inside readable files for `keyword` (case-insensitive).
        Returns path:line for each match, so you know which file to open next."""
        base = ROOT.resolve()
        needle = (keyword or "").lower()
        out = []
        for p in sorted(base.rglob("*")):
            if p.is_symlink() or not p.is_file() or p.suffix.lower() not in _TEXT_EXT:
                continue
            try:
                for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                    if needle in line.lower():
                        out.append(f"{p.relative_to(base)}:{i}: {line.strip()[:120]}")
                        if len(out) >= max_hits:
                            return "\n".join(out) + "\n...[more matches not shown]"
            except Exception:
                continue
        return "\n".join(out) if out else f"No text matches for {keyword!r}."

    tools = {"list_dir": list_dir, "read_file": read_file, "run_sql": run_sql,
             "find_files": find_files, "search_text": search_text}

    if allow_python:
        def run_python(code):
            """ADVANCED, OPTIONAL: run a short Python snippet to inspect the image. `ROOT` (the image
            folder, a pathlib.Path) is available. Print what you want to see. Do not write or delete."""
            # NOT a sandbox: the keyword check below stops accidents, not a determined snippet (Python
            # can still import modules and touch files). Use it only on a COPY of an extraction.
            import io
            import contextlib
            if any(bad in code for bad in ("open(", "write", "unlink", "remove", "rmtree",
                                           "os.system", "subprocess", "Popen", "__import__")):
                return "Blocked: that snippet looks like it writes or runs external commands."
            buf = io.StringIO()
            safe = {"ROOT": ROOT, "sqlite3": sqlite3, "json": json, "Path": Path, "re": re}
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code, safe)  # teaching tool only; see the warning above
            except Exception as e:
                return f"Python error: {e}\n{buf.getvalue()}"
            out = buf.getvalue().strip()
            return out[:1500] if out else "(the snippet ran but printed nothing)"
        tools["run_python"] = run_python

    return tools


def tool_descriptions(tools):
    """One line per tool for the system prompt: its real signature (so the model uses the right
    argument names) and the first paragraph of its docstring."""
    lines = []
    for name, fn in tools.items():
        try:
            sig = str(inspect.signature(fn))
        except (TypeError, ValueError):
            sig = "()"
        doc = " ".join((fn.__doc__ or "").strip().split("\n\n")[0].split())
        lines.append(f"- {name}{sig}: {doc}")
    return "\n".join(lines)


# ======================================================================= the agent
def build_system_prompt(tools):
    return (
        "You are Sectra, a digital-forensics examiner's assistant. You are investigating an Android "
        "device extraction (a copy of the phone's files) to answer the examiner's question. You cannot "
        "see any file until you open it with a tool, and you must base every answer only on what the "
        "tools return.\n\n"
        "TOOLS (use exactly one per step):\n" + tool_descriptions(tools) + "\n\n"
        "HOW TO REPLY: send ONE JSON object and nothing else.\n"
        "To use a tool:\n"
        '  {"thought": "<one short sentence>", "action": "list_dir", "action_input": {"path": "data/data"}}\n'
        "When you can answer, reply:\n"
        '  {"thought": "<one short sentence>", "final_answer": "<your answer>", "evidence_path": "<the file you used>"}\n\n'
        "RULES: investigate step by step; use ONLY what the tools return; never invent paths, tables, "
        "or data; if a tool errors, try another path or tool; if the evidence is not there, say so "
        "plainly; always cite the exact file in evidence_path. Keep thoughts to one sentence. /no_think"
    )


def parse_action(raw):
    """Pull the JSON object out of the model's reply, tolerating <think> blocks, code fences, and
    prose before or after it (the first '{' that starts a valid JSON object wins)."""
    text = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S)
    text = text.replace("```json", "").replace("```", "")
    decoder = json.JSONDecoder()
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text, m.start())
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def chat(client, model, messages, max_tokens=None):
    """One model call. Some hosted models (gpt-oss on Groq) occasionally try a built-in function call
    instead of writing the JSON reply, which the provider rejects ("model called a tool"); when that
    happens, ask again with a plain-text reminder instead of stopping the investigation.
    max_tokens: 1,500 by default, 900 for Qwen (its free tier allows 1,000 reply tokens a minute)."""
    if max_tokens is None:
        max_tokens = 900 if "qwen" in str(model).lower() else 1500
    for attempt in range(3):
        try:
            return client.chat.completions.create(model=model, messages=messages, temperature=0,
                                                  max_tokens=max_tokens).choices[0].message.content or ""
        except Exception as e:
            if "called a tool" not in str(e) or attempt == 2:
                raise
            messages = messages + [{"role": "user", "content": "Do not use function calling. Reply with "
                                    "ONE JSON object written as plain text."}]


def run_agent_iter(question, client, model, tools, system_prompt=None, max_steps=12, history=None):
    """Generator version of the agent, for live UIs. Yields a dict per step
    ({step, thought, action, args, observation}) and finally the answer
    ({final_answer, evidence_path}) or a give-up dict ({final_answer: None}).

    history: optional prior [(user, assistant)] turns, so the agent remembers a conversation.
    """
    system_prompt = system_prompt or build_system_prompt(tools)
    messages = [{"role": "system", "content": system_prompt}]
    for u, a in (history or []):
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})
    question = as_text(question)
    messages.append({"role": "user", "content": f"Investigate and answer this question: {question}"})

    seen = question + " " + " ".join(as_text(a) for _, a in (history or []))  # what it may rely on
    tools_run, pushbacks, ran = 0, 0, set()
    for step in range(1, max_steps + 1):
        raw = chat(client, model, messages)
        messages.append({"role": "assistant", "content": raw})
        move = parse_action(raw)
        if move is None:
            messages.append({"role": "user",
                             "content": "That was not valid JSON. Reply with ONE JSON object only."})
            continue
        if "final_answer" in move:
            answer = move["final_answer"]
            problem = evidence_check(answer, tools_run, seen, cited=move.get("evidence_path", ""),
                                     ran=ran, tool_names=list(tools))
            if problem and pushbacks < MAX_PUSHBACKS:
                # The harness, not the model, decides whether an answer is backed by evidence.
                pushbacks += 1
                yield {"step": step, "thought": "Evidence check: answer sent back",
                       "action": "evidence_check", "args": {}, "observation": problem}
                messages.append({"role": "user", "content": problem})
                continue
            if problem:   # still unsupported after the push-backs: deliver it, clearly flagged
                answer = f"{answer}\n\nUNVERIFIED: {problem}"
            yield {"final_answer": answer, "evidence_path": move.get("evidence_path", "")}
            return
        tool, args = move.get("action"), move.get("action_input", {}) or {}
        if tool not in tools:
            observation = f"Unknown tool {tool!r}. Use one of: {', '.join(tools)}."
            args = args if isinstance(args, dict) else {}
        else:
            if not isinstance(args, dict):   # e.g. "action_input": "data/data": give it to the 1st arg
                params = list(inspect.signature(tools[tool]).parameters)
                args = {params[0]: args} if params else {}
            try:
                observation = tools[tool](**args)
                tools_run += 1                 # only a tool that actually ran counts as evidence
                ran.add(tool)
            except Exception as e:
                observation = f"Tool error: {e}. Arguments are: {tool}{inspect.signature(tools[tool])}"
        seen += " " + str(observation)
        yield {"step": step, "thought": move.get("thought", ""),
               "action": tool, "args": args, "observation": observation}
        messages.append({"role": "user", "content": f"Observation:\n{observation}"})
    yield {"final_answer": None, "evidence_path": ""}


# ======================================================================= evidence check
# Limiting the tools to the evidence limits what the model can LOOK AT, not what it can SAY: a
# model can still write a plausible PID or file name from its training. So before an answer is
# accepted, the harness checks it: at least one tool must have run for this question, and every
# specific identifier in the answer must appear in something a tool actually returned (or in the
# question / earlier answers). Anything else is sent back to the model to confirm or remove.
MAX_PUSHBACKS = 2
EVIDENCE_PATTERNS = {
    "PID": r"\bPIDs?\s*[:#=]?\s*(\d{1,6})\b",
    "IP address": r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?![\d.])",
    "memory address": r"\b(0x[0-9a-fA-F]{5,})\b",
    "file": r"\b([\w-]+\.(?:exe|dll|sys|apk|db|sqlite|xml|json|plist|log|txt|csv))\b",
}


def evidence_check(answer, tools_run, seen, cited="", ran=(), tool_names=()):
    """Return a push-back message if the answer is not backed by tool output, else None.
    cited / ran / tool_names: the answer's evidence line must not name a tool that never ran."""
    answer = as_text(answer)
    if tools_run == 0 and not answer.rstrip().endswith("?"):   # a question back to the user claims nothing
        return ("You answered without running any tool. Do not answer from memory or assumption: "
                "run the tool that shows this evidence, then answer only from its output.")
    seen_low = seen.lower()
    missing = []
    for kind, pattern in EVIDENCE_PATTERNS.items():
        for value in re.findall(pattern, str(answer), flags=re.I):
            found = (re.search(rf"(?<!\d){value}(?!\d)", seen) if kind == "PID"
                     else value.lower() in seen_low)
            if not found and f"{kind} {value}" not in missing:
                missing.append(f"{kind} {value}")
    if missing:
        return ("Your answer names " + ", ".join(missing[:8]) + ", which does not appear in any tool "
                "output you have seen. Run a tool that shows it, or remove it from your answer.")
    cited_text = as_text(cited)
    unrun = [t for t in tool_names if t not in ran and re.search(rf"\b{re.escape(t)}\b", cited_text)
             and not re.search(rf"\b{re.escape(t)}\b", seen)]
    if unrun:
        return ("Your evidence cites " + ", ".join(unrun) + ", which you have not run. Cite only the tools "
                "whose output you actually used, or run them first.")
    return None


def run_agent(question, client, model, tools, system_prompt=None, max_steps=12,
              on_step=None, history=None):
    """Drive the model think->act->observe until it answers.

    on_step(dict): optional callback for live UIs (gets each step dict, then the final dict).
    history: optional prior [(user, assistant)] turns, so the agent remembers a conversation.
    Returns the final move dict (with 'final_answer'/'evidence_path'), or None if it gave up.
    """
    final = None
    for ev in run_agent_iter(question, client, model, tools, system_prompt, max_steps, history):
        if on_step:
            on_step(ev)
        if "final_answer" in ev:
            final = ev if ev["final_answer"] is not None else None
    return final


def answer_text(move):
    """Format a final move as a human answer line with its citation."""
    if not move:
        return "I could not reach an answer within the step limit. Try rephrasing the question."
    cite = move.get("evidence_path") or "(no file cited)"
    return f"{move['final_answer']}\n\nSource: {cite}"

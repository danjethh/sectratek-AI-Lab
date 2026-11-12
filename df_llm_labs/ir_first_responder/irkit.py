"""
irkit.py - Sectra First Responder: an incident-response copilot that works from a company's
own IR plan and playbooks.

DESIGN (the same discipline as the Sectra DF agent, applied to incident response)
---------------------------------------------------------------------------------
We took a comprehensive IR lifecycle (NIST SP 800-61 / SANS: identify -> notify -> collect ->
analyse -> contain -> eradicate -> recover -> after-action) and, for every action a playbook
typically calls for, decided what a language-model copilot can safely do, then built one tool
per action. Each tool is one of three kinds:

  RUN      - a real, local, read-only or analytical thing Sectra does itself (classify the
             incident, read/search/query artifacts, build a timeline, extract IOCs, check them
             against the watch-list, write the after-action report). No external side effects.
  DRAFT    - Sectra cannot touch production, so it produces ready-to-use content grounded in the
             playbook for a human to run: the notification email, the exact collection /
             containment / eradication / recovery commands and paths.
  SIMULATE - an action with an external side effect (notify management, page on-call, open a
             ticket, block an IOC, isolate a host). Sectra may only do it AFTER the team approves
             in chat, and even then it is simulated and written to the action log. Never real.

The agent reasons out loud (one short "thought" per step), uses exactly one tool per step, and
cites the plan/playbook section behind every instruction. Reuses the shared loop in agentkit.
"""
import os
import re
from pathlib import Path

import agentkit as ak

connect_model = ak.connect_model
run_agent = ak.run_agent
run_agent_iter = ak.run_agent_iter
answer_text = ak.answer_text

_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")
_TEXT_EXT = {".txt", ".log", ".csv", ".json", ".xml", ".md", ".ini", ".conf", ".eml", ".tsv"}

# ---- indicator patterns (shared by extract_iocs / check_indicators) ----
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_URL = re.compile(r"https?://[^\s\"'<>)]+", re.I)
_HASH = re.compile(r"\b[a-fA-F0-9]{64}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{32}\b")
_DOMAIN = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")
_TS = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")
# domain-looking tokens whose last label is really a file extension - not a domain
_NOT_TLD = {"exe", "dll", "txt", "log", "csv", "tsv", "7z", "zip", "pf", "hve", "raw", "evtx",
            "db", "sqlite", "json", "xml", "ini", "conf", "eml", "md", "py", "bat", "ps1", "sys"}


# ----------------------------------------------------------------- knowledge (plan + playbooks)
def load_knowledge(folder):
    """Read every .md doc in `folder` into {doc_name: [(section_title, body), ...]}."""
    knowledge = {}
    for p in sorted(Path(folder).glob("*.md")):
        knowledge[p.name] = _split_sections(p.read_text(errors="replace"))
    return knowledge


def _split_sections(text):
    sections, title, cur = [], "(top)", []
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            if cur:
                sections.append((title, "\n".join(cur).strip()))
            title, cur = m.group(2).strip(), []
        else:
            cur.append(line)
    sections.append((title, "\n".join(cur).strip()))
    return [(t, b) for t, b in sections if b or t != "(top)"]


def _domains(text):
    out = []
    for d in _DOMAIN.findall(text or ""):
        if d.split(".")[-1].lower() in _NOT_TLD:
            continue
        if _IPV4.fullmatch(d):
            continue
        out.append(d.lower())
    return out


# ----------------------------------------------------------------- the tools
def make_ir_tools(knowledge, evidence_root, action_log, org="Northwind Labs"):
    """Build the full IR toolbox. `action_log` is a list the SIMULATE/RUN tools append to."""
    EV = Path(evidence_root)
    EV.mkdir(parents=True, exist_ok=True)

    # ============================================================ shared helpers
    def _all_sections():
        for doc, secs in knowledge.items():
            for title, body in secs:
                yield doc, title, body

    def _pull(title_keywords, goal="", limit=2000):
        """Collect playbook sections whose title matches any keyword; prefer the goal's playbook."""
        key = (goal or "").lower()
        hits, fallback = [], []
        for doc, title, body in _all_sections():
            if any(w in title.lower() for w in title_keywords):
                block = f"[{doc} > {title}]\n{body}"
                if not goal or key in doc.lower() or key in (title + " " + body).lower():
                    hits.append(block)
                else:
                    fallback.append(block)
        chosen = hits or fallback
        if not chosen:
            return None
        text = "\n\n".join(chosen)
        return text[:limit] + ("" if len(text) <= limit else "\n...[truncated]")

    def _known_bad():
        """Parse the threat-intel watch-list from any knowledge section about indicators."""
        items = []
        for doc, title, body in _all_sections():
            if not any(w in title.lower() for w in ("indicator", "known-bad", "known bad",
                                                    "watch-list", "watchlist", "threat intel", "ioc")):
                continue
            for line in body.splitlines():
                line = line.strip().lstrip("-*").strip()
                if not line:
                    continue
                parts = re.split(r"\s{2,}", line)
                val = parts[0].strip()
                note = "  ".join(p.strip() for p in parts[1:]) if len(parts) > 1 else ""
                if val and " " not in val:
                    items.append((val, note, doc, title))
        return items

    def _safe(path):
        base = EV.resolve()
        path = (path or ".").strip().lstrip("/")
        t = base if path in ("", ".") else (EV / path).resolve()
        if t != base and base not in t.parents:
            raise ValueError("path is outside the evidence folder")
        return t

    def _read_text(path):
        t = _safe(path)
        if not t.exists() or t.is_dir():
            return None, f"No such artifact: {path}"
        if t.read_bytes()[:15] == b"SQLite format 3":
            return None, f"[{path} is a SQLite database. Use run_sql with a SELECT.]"
        return t.read_text(errors="replace"), None

    # ============================================================ 1. KNOWLEDGE (RUN, read-only)
    def list_playbooks():
        """RUN: list the IR plan and playbooks with their section titles. Start here to see what exists."""
        out = []
        for doc, secs in knowledge.items():
            out.append(doc + ":")
            out += [f"    - {t}" for t, _ in secs]
        return "\n".join(out) if out else "(no playbooks loaded)"

    def search_playbooks(keyword):
        """RUN: search the plan and playbooks for a keyword; returns [doc > section] matching lines."""
        key = (keyword or "").lower()
        out = []
        for doc, title, body in _all_sections():
            for line in body.splitlines():
                if key in line.lower():
                    out.append(f"[{doc} > {title}] {line.strip()[:140]}")
                    if len(out) >= 25:
                        return "\n".join(out) + "\n...[more]"
        return "\n".join(out) if out else f"No playbook text matches {keyword!r}."

    def read_playbook(name, section=""):
        """RUN: read a playbook (by file name) or one of its sections (by text in the title)."""
        want_doc, want_sec = (name or "").lower(), (section or "").lower()
        hits = []
        for doc, title, body in _all_sections():
            if want_doc and want_doc not in doc.lower():
                continue
            if want_sec and want_sec not in title.lower():
                continue
            hits.append(f"[{doc} > {title}]\n{body}")
        if not hits:
            return f"No playbook/section matching name={name!r} section={section!r}. Use list_playbooks."
        text = "\n\n".join(hits)
        return text[:2200] + ("" if len(text) <= 2200 else "\n...[truncated]")

    def classify_incident(description):
        """RUN: match the team's description to the best-fitting playbook and its severity, and
        return the playbook's first response step. Use this at the very start of an incident."""
        words = set(re.findall(r"[a-z]{4,}", (description or "").lower()))
        best, best_score = None, 0
        for doc, secs in knowledge.items():
            if "plan" in doc.lower():
                continue
            text = " ".join(t + " " + b for t, b in secs).lower()
            score = sum(1 for w in words if w in text)
            # a direct hit on the incident name in the filename is worth a lot
            score += 5 * sum(1 for w in words if w in doc.lower())
            if score > best_score:
                best, best_score = doc, score
        if not best:
            return "Could not match a playbook. Use list_playbooks and ask the team to clarify the incident."
        secs = dict(knowledge[best])
        sev = next((b for t, b in knowledge[best] if "classif" in t.lower()), "(severity not stated)")
        first = next((b for t, b in knowledge[best] if any(w in t.lower()
                     for w in ("immediate", "first", "response"))), "(no immediate-response section)")
        return (f"Best-matching playbook: {best}\n\nClassification / severity:\n{sev}\n\n"
                f"First response steps:\n{first}")

    # ============================================================ 2. NOTIFY / COORDINATE
    def draft_notification(audience="management", incident=""):
        """DRAFT: write a notification for `audience` (management/legal/customers/regulator), pulling
        the template from the playbook if there is one. This DRAFTS only - show it and ask to approve."""
        for doc, title, body in _all_sections():
            if "template" in title.lower() and (not incident or incident.lower() in doc.lower()
                                                 or incident.lower() in title.lower()):
                return f"(template from [{doc} > {title}], audience={audience})\n{body}"
        return (f"To: {audience}\nSubject: Security incident in progress ({incident or 'under triage'})\n\n"
                f"Team, we are responding to a suspected {incident or 'security incident'} at {org}. The "
                "response team is engaged and following the IR plan. We will send an update within 60 "
                "minutes or on any material change. [No playbook template found; generic draft.]")

    def notify(audience="management", approved=False):
        """SIMULATE (gated): 'send' the notification to `audience`. Only after the team approves in
        chat (approved=True). Nothing is really sent; it is logged to the action log."""
        if not approved:
            return "Not sent. I need the team's explicit approval first (reply 'approve' to send)."
        entry = f"[DRILL/SIMULATED] Notification 'sent' to {audience}."
        action_log.append(entry)
        return entry + " (No real email was sent - training drill.)"

    def open_ticket(summary="", approved=False):
        """SIMULATE (gated): open an incident ticket. Only with the team's approval. Logged, not real."""
        if not approved:
            return "Not opened. Confirm with the team first (approved=true) and I will log it."
        entry = f"[DRILL/SIMULATED] Incident ticket opened: {summary or 'security incident'}."
        action_log.append(entry)
        return entry

    def page_oncall(role="IT on-call", approved=False):
        """SIMULATE (gated): page an on-call role (e.g. 'IT on-call', 'Forensics Lead'). Gated + logged."""
        if not approved:
            return f"Not paged. Confirm with the team first (approved=true) to page {role}."
        entry = f"[DRILL/SIMULATED] Paged {role}."
        action_log.append(entry)
        return entry

    # ============================================================ 3. GUIDANCE (DRAFT, human runs it)
    def recommend_collection(goal=""):
        """DRAFT: the exact tools, commands, and paths to COLLECT evidence, from the playbook."""
        out = _pull(("collect", "evidence", "acquire", "preserve"), goal)
        if out:
            action_log.append(f"Recommended evidence-collection steps for: {goal or 'the incident'}.")
        return out or "No collection section matched. Try read_playbook(section='collection')."

    def recommend_containment(goal=""):
        """DRAFT: the CONTAINMENT steps/commands from the playbook (isolate host, disable account,
        block C2). The team runs these; Sectra can only simulate them via contain()."""
        out = _pull(("contain", "isolat"), goal)
        return out or "No containment section matched. Try read_playbook(section='contain')."

    def recommend_eradication(goal=""):
        """DRAFT: the ERADICATION steps from the playbook (remove persistence/malware, reset creds)."""
        out = _pull(("eradicat", "remov", "rebuild", "contain"), goal)
        return out or "No eradication section matched. Try read_playbook(section='eradicat')."

    def recommend_recovery(goal=""):
        """DRAFT: the RECOVERY steps from the playbook (restore from clean backup, validate, monitor)."""
        out = _pull(("recover", "restore", "monitor"), goal)
        return out or "No recovery section matched. Try read_playbook(section='recover')."

    # ============================================================ 4. CONTAINMENT ACTIONS (SIMULATE)
    def contain(kind="isolate_host", target="", approved=False):
        """SIMULATE (gated): take a containment action - kind is 'isolate_host', 'disable_account',
        or 'block_ioc'; target is the host/account/indicator. Only with approval; logged, not real."""
        done = {"isolate_host": "Isolated host", "disable_account": "Disabled account",
                "block_ioc": "Blocked indicator at the firewall"}
        plan = {"isolate_host": "isolate the host", "disable_account": "disable the account",
                "block_ioc": "block the indicator at the firewall"}
        if not approved:
            intent = plan.get(kind, f"take containment action '{kind}' on")
            return f"Not done. This would {intent}: {target or '(target?)'}. Get the team's approval first."
        entry = f"[DRILL/SIMULATED] {done.get(kind, kind)}: {target or '(unspecified)'}."
        action_log.append(entry)
        return entry

    # ============================================================ 5. EVIDENCE ANALYSIS (RUN)
    def list_evidence(path="."):
        """RUN: list the artifacts the team has collected into the evidence folder."""
        t = _safe(path)
        if not t.exists():
            return "(no evidence collected yet)"
        if t.is_file():
            return f"{path} is a file. Use read_evidence, run_sql, build_timeline, or extract_iocs."
        items = [e + ("/" if (t / e).is_dir() else "") for e in sorted(os.listdir(t))]
        return "\n".join(items) if items else "(no evidence collected yet)"

    def read_evidence(path, max_chars=1600):
        """RUN: read a collected text/log artifact (or get a hint for a SQLite database)."""
        text, err = _read_text(path)
        if err:
            return err
        return text[:max_chars] + ("" if len(text) <= max_chars else "\n...[truncated]")

    def search_evidence(keyword, max_hits=25):
        """RUN: search the collected artifacts for a keyword; returns artifact:line matches."""
        base = EV.resolve()
        key = (keyword or "").lower()
        out = []
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in _TEXT_EXT:
                continue
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if key in line.lower():
                    out.append(f"{p.relative_to(base)}:{i}: {line.strip()[:140]}")
                    if len(out) >= max_hits:
                        return "\n".join(out) + "\n...[more]"
        return "\n".join(out) if out else f"No evidence matches {keyword!r}."

    def run_sql(path, query):
        """RUN: run ONE read-only SELECT against a collected SQLite artifact."""
        import sqlite3
        t = _safe(path)
        if not t.exists():
            return f"No such artifact: {path}"
        q = (query or "").strip().rstrip(";")
        if not q.lower().startswith(("select", "pragma")):
            return "Only read-only SELECT queries are allowed."
        try:
            con = sqlite3.connect(f"file:{t}?mode=ro", uri=True)
            cur = con.execute(q)
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = cur.fetchmany(50)
            con.close()
        except Exception as e:
            return f"SQL error: {e}"
        if not rows:
            return "(no rows)"
        return "\n".join([" | ".join(cols)] + [" | ".join(str(c) for c in r) for r in rows])

    def build_timeline(path, max_rows=40):
        """RUN: build a time-ordered timeline from a log/CSV artifact (lines carrying a timestamp)."""
        text, err = _read_text(path)
        if err:
            return err
        rows = []
        for line in text.splitlines():
            m = _TS.search(line)
            if m:
                rows.append((m.group(0).replace("T", " "), line.strip()))
        if not rows:
            return f"No timestamped lines found in {path}."
        rows.sort(key=lambda r: r[0])
        shown = rows[:max_rows]
        body = "\n".join(f"{ts}  {ln[:150]}" for ts, ln in shown)
        more = "" if len(rows) <= max_rows else f"\n...[{len(rows) - max_rows} more events]"
        return f"Timeline of {path} ({len(rows)} events):\n{body}{more}"

    def extract_iocs(path):
        """RUN: extract indicators (IPs, domains, URLs, file hashes) from a collected artifact."""
        text, err = _read_text(path)
        if err:
            return err
        ips = sorted(set(_IPV4.findall(text)))
        doms = sorted(set(_domains(text)))
        urls = sorted(set(_URL.findall(text)))
        hashes = sorted(set(_HASH.findall(text)))
        if not any([ips, doms, urls, hashes]):
            return f"No IPs, domains, URLs, or hashes found in {path}."
        parts = []
        if ips: parts.append("IPs:\n  " + "\n  ".join(ips[:30]))
        if doms: parts.append("Domains:\n  " + "\n  ".join(doms[:30]))
        if urls: parts.append("URLs:\n  " + "\n  ".join(urls[:20]))
        if hashes: parts.append("Hashes:\n  " + "\n  ".join(hashes[:20]))
        return f"Indicators in {path}:\n" + "\n".join(parts) + \
               "\n(Use check_indicators to compare these against the watch-list.)"

    def check_indicators(path="", values=""):
        """RUN: compare indicators against the threat-intel watch-list. Give `path` (an artifact to
        scan) and/or `values` (comma/space-separated indicators). Returns any known-bad matches."""
        cand = set()
        if path:
            text, err = _read_text(path)
            if err:
                return err
            cand |= set(_IPV4.findall(text)) | set(_domains(text)) | set(x.lower() for x in _HASH.findall(text))
            for line in text.splitlines():  # bare file/service names too
                cand |= set(re.findall(r"\b[\w.-]+\.(?:exe|dll|txt|sys)\b", line, re.I))
                cand |= set(re.findall(r"name=([\w.-]+)", line))
        if values:
            cand |= {v.strip() for v in re.split(r"[\s,]+", values) if v.strip()}
        cand = {c.lower() for c in cand if c}
        if not cand:
            return "No indicators to check. Give a `path` to an artifact or a `values` list."
        matches = []
        for val, note, doc, title in _known_bad():
            v = val.lower()
            for c in cand:
                if c == v or c.endswith("." + v) or v.endswith("." + c) or (len(v) > 4 and v in c):
                    matches.append(f"MATCH {val}  (seen in {c})  - {note} [{doc} > {title}]")
                    break
        if not matches:
            return (f"Checked {len(cand)} indicator(s) against the watch-list: no known-bad matches. "
                    "That does not clear them - it means none are on our small list.")
        action_log.append(f"Watch-list hits: {len(matches)} indicator(s) matched known-bad.")
        return "Known-bad matches:\n" + "\n".join(matches)

    # ============================================================ 6. POST-INCIDENT (RUN)
    def after_action_report():
        """RUN: produce a short after-action report from the action log and the incident so far."""
        log = action_log or []
        lines = [f"After-action report (DRILL) - {org}", "=" * 40,
                 f"Actions taken / recommended ({len(log)}):"]
        lines += [f"  {i}. {e}" for i, e in enumerate(log, 1)] or ["  (none logged yet)"]
        lines += ["", "Reminder: write the full timeline and improvements within 5 business days "
                      "(see the IR plan, Lessons learned). All notifications above were simulated."]
        action_log.append("Generated after-action report.")
        return "\n".join(lines)

    return {
        # knowledge
        "list_playbooks": list_playbooks, "search_playbooks": search_playbooks,
        "read_playbook": read_playbook, "classify_incident": classify_incident,
        # notify / coordinate
        "draft_notification": draft_notification, "notify": notify,
        "open_ticket": open_ticket, "page_oncall": page_oncall,
        # guidance (draft)
        "recommend_collection": recommend_collection, "recommend_containment": recommend_containment,
        "recommend_eradication": recommend_eradication, "recommend_recovery": recommend_recovery,
        # containment actions (simulate)
        "contain": contain,
        # evidence analysis (run)
        "list_evidence": list_evidence, "read_evidence": read_evidence,
        "search_evidence": search_evidence, "run_sql": run_sql,
        "build_timeline": build_timeline, "extract_iocs": extract_iocs,
        "check_indicators": check_indicators,
        # post-incident
        "after_action_report": after_action_report,
    }


def build_ir_system_prompt(tools, org="Northwind Labs"):
    return (
        f"You are Sectra, the incident first responder for {org}. A response team has called you about a "
        "possible security incident. You work ONLY from the company's incident-response plan and playbooks "
        "(your knowledge tools) and the artifacts the team collects. This is a training DRILL: anything "
        "with an external effect is simulated, never real.\n\n"
        "WHAT YOU CAN DO - every tool is one of three kinds:\n"
        "  RUN      - you do it yourself (classify, read/search/query artifacts, build a timeline, extract "
        "and check indicators, write the after-action report).\n"
        "  DRAFT    - you cannot touch production, so you produce ready-to-use content for a human to run "
        "(the notification text, and the exact collection / containment / eradication / recovery commands).\n"
        "  SIMULATE - an action with a side effect (notify, open_ticket, page_oncall, contain). You may ONLY "
        "do it after the team approves in chat (approved=true); it is then logged, not real.\n\n"
        "TOOLS (use exactly one per step):\n" + ak.tool_descriptions(tools) + "\n\n"
        "HOW TO REPLY: send ONE JSON object and nothing else.\n"
        "To use a tool:\n"
        '  {"thought": "<one short sentence of reasoning>", "action": "classify_incident", "action_input": {"description": "..."}}\n'
        "To speak to the team (give a step, ask a question, or ask for approval):\n"
        '  {"thought": "<one short sentence>", "final_answer": "<what you tell the team>", "evidence_path": "<the plan/playbook section you used>"}\n\n'
        "HOW TO HANDLE A TURN:\n"
        "1. Work out what the plan/playbooks SAY about the team's situation (classify_incident, "
        "search_playbooks, read_playbook) and tell them, in plain words, citing the section.\n"
        "2. Then OFFER the concrete next action you can take for them, and say which kind it is. RUN analysis "
        "yourself when artifacts are present. DRAFT content the team must run. For any SIMULATE action, show "
        "what you will do and ASK for approval first; only call it with approved=true after they agree.\n"
        "3. Follow the incident through its phases as the playbook dictates: identify -> notify management -> "
        "collect -> analyse the collected artifacts -> contain -> eradicate -> recover -> after-action.\n\n"
        "RULES: base every instruction on the plan/playbooks and name the section in evidence_path; do only "
        "one thing per step; never invent commands, data, or indicators; keep replies short and actionable; "
        "never take a SIMULATE action without explicit approval in the chat. /no_think"
    )


def quick_agent(message, client, model, tools, history=None, **kw):
    prompt = build_ir_system_prompt(tools)
    return run_agent(message, client, model, tools, prompt, history=history, **kw)

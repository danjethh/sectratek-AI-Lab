"""
irkit.py - Sectra First Responder: an incident-response copilot over a company's
IR plan and playbooks.

The team "calls" Sectra, says what they think the incident is, and Sectra walks them
through the response using ONLY the company's plan and playbooks (its knowledge tools).
It can also act, with the team's approval: draft a management notification (pulling a
template from the playbook), recommend the exact collection tools/commands, and read the
artifacts the team collects back.

SAFETY / DESIGN (this is a drill):
- Side-effecting actions (sending a management email) are SIMULATED, never real. The agent
  must get the team's explicit approval in chat before it may call send_email(approved=True),
  and even then nothing is actually emailed - it is logged to an action log.
- Knowledge tools are read-only over the plan/playbooks. Evidence tools are read-only over
  whatever artifacts the team uploads. The agent cites the playbook section behind each step.

Reuses the shared agent loop from agentkit (connect_model, run_agent, run_agent_iter).
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
_TEXT_EXT = {".txt", ".log", ".csv", ".json", ".xml", ".md", ".ini", ".conf", ".eml"}


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


# ----------------------------------------------------------------- the tools
def make_ir_tools(knowledge, evidence_root, action_log, org="Northwind Labs"):
    """Build the IR toolbox. action_log is a list that send_email/collection append to."""
    EV = Path(evidence_root)
    EV.mkdir(parents=True, exist_ok=True)

    # ---- knowledge (read-only over the plan + playbooks) ----
    def list_playbooks():
        """List the incident-response plan and playbooks, with their section titles."""
        out = []
        for doc, secs in knowledge.items():
            out.append(doc + ":")
            out += [f"    - {t}" for t, _ in secs]
        return "\n".join(out) if out else "(no playbooks loaded)"

    def search_playbooks(keyword):
        """Search the plan and playbooks for a keyword; returns [doc > section] matching lines."""
        key = (keyword or "").lower()
        out = []
        for doc, secs in knowledge.items():
            for title, body in secs:
                for line in body.splitlines():
                    if key in line.lower():
                        out.append(f"[{doc} > {title}] {line.strip()[:140]}")
                        if len(out) >= 25:
                            return "\n".join(out) + "\n...[more]"
        return "\n".join(out) if out else f"No playbook text matches {keyword!r}."

    def read_playbook(name, section=""):
        """Read a playbook (by file name) or one of its sections (by text in the title)."""
        want_doc = (name or "").lower()
        want_sec = (section or "").lower()
        hits = []
        for doc, secs in knowledge.items():
            if want_doc and want_doc not in doc.lower():
                continue
            for title, body in secs:
                if want_sec and want_sec not in title.lower():
                    continue
                hits.append(f"[{doc} > {title}]\n{body}")
        if not hits:
            return f"No playbook/section matching name={name!r} section={section!r}. Use list_playbooks."
        text = "\n\n".join(hits)
        return text[:2200] + ("" if len(text) <= 2200 else "\n...[truncated]")

    # ---- actions (human-in-the-loop) ----
    def draft_email(audience="management", incident=""):
        """Draft a notification email. Pulls a template from the playbooks if one exists.
        This DRAFTS only; it does not send. Show it to the team and ask for approval."""
        tmpl = None
        for doc, secs in knowledge.items():
            for title, body in secs:
                if "template" in title.lower() and (not incident or incident.lower() in doc.lower()
                                                     or incident.lower() in title.lower()):
                    tmpl = f"(template from [{doc} > {title}])\n{body}"
                    break
            if tmpl:
                break
        if tmpl:
            return tmpl
        return (f"To: {audience}\nSubject: Security incident in progress ({incident or 'under triage'})\n\n"
                f"Team, we are responding to a suspected {incident or 'security incident'} at {org}. "
                "The response team is engaged and following the IR plan. We will send an update within 60 "
                "minutes or on any material change. [No playbook template was found; this is a generic draft.]")

    def send_email(audience="management", approved=False, body=""):
        """Send the notification email - SIMULATED. Only call this AFTER the team approves in chat,
        with approved=True. Nothing real is sent; the action is written to the action log."""
        if not approved:
            return "Not sent. I need the team's explicit approval first (reply 'approve' to send)."
        entry = f"[DRILL/SIMULATED] Notification 'sent' to {audience}."
        action_log.append(entry)
        return entry + " (No real email was sent - this is a training drill.)"

    def recommend_collection(goal=""):
        """Recommend the exact tools, commands, and paths to collect evidence for `goal`,
        taken from the playbooks' collection sections."""
        key = (goal or "collect").lower()
        hits = []
        for doc, secs in knowledge.items():
            for title, body in secs:
                if any(w in title.lower() for w in ("collect", "evidence", "acquire", "preserve")):
                    if not goal or key in (title + " " + body).lower() or key in doc.lower():
                        hits.append(f"[{doc} > {title}]\n{body}")
        if not hits:
            return "No collection section matched. Try search_playbooks('collect') or read_playbook(section='collection')."
        text = "\n\n".join(hits)
        action_log.append(f"Recommended collection steps for: {goal or 'the incident'}.")
        return text[:2000] + ("" if len(text) <= 2000 else "\n...[truncated]")

    # ---- evidence (read-only over artifacts the team uploads/collects) ----
    def _safe(path):
        base = EV.resolve()
        path = (path or ".").strip().lstrip("/")
        t = base if path in ("", ".") else (EV / path).resolve()
        if t != base and base not in t.parents:
            raise ValueError("path is outside the evidence folder")
        return t

    def list_evidence(path="."):
        """List the artifacts the team has collected into the evidence folder."""
        t = _safe(path)
        if not t.exists():
            return "(no evidence collected yet)"
        if t.is_file():
            return f"{path} is a file. Use read_evidence or run_sql."
        items = [e + ("/" if (t / e).is_dir() else "") for e in sorted(os.listdir(t))]
        return "\n".join(items) if items else "(no evidence collected yet)"

    def read_evidence(path, max_chars=1600):
        """Read a collected text/log artifact (or get a hint for a database)."""
        t = _safe(path)
        if not t.exists() or t.is_dir():
            return f"No such artifact: {path}"
        if t.read_bytes()[:15] == b"SQLite format 3":
            import sqlite3
            con = sqlite3.connect(f"file:{t}?mode=ro", uri=True)
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            con.close()
            return f"[{path} is a SQLite database. Tables: {tables}. Use run_sql with a SELECT.]"
        text = t.read_text(errors="replace")
        return text[:max_chars] + ("" if len(text) <= max_chars else "\n...[truncated]")

    def search_evidence(keyword, max_hits=25):
        """Search the collected artifacts for a keyword; returns artifact:line matches."""
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
        """Run ONE read-only SELECT against a collected SQLite artifact."""
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

    return {
        "list_playbooks": list_playbooks, "search_playbooks": search_playbooks,
        "read_playbook": read_playbook, "draft_email": draft_email, "send_email": send_email,
        "recommend_collection": recommend_collection, "list_evidence": list_evidence,
        "read_evidence": read_evidence, "search_evidence": search_evidence, "run_sql": run_sql,
    }


def build_ir_system_prompt(tools, org="Northwind Labs"):
    return (
        f"You are Sectra, the incident first responder for {org}. A response team has called you about a "
        "possible security incident. Your job is to calmly walk them through the response, ONE step at a "
        "time, using ONLY the company's incident-response plan and playbooks (via your tools). This is a "
        "training DRILL: any emails are simulated, never real.\n\n"
        "TOOLS (use exactly one per step):\n" + ak.tool_descriptions(tools) + "\n\n"
        "HOW TO REPLY: send ONE JSON object and nothing else.\n"
        "To use a tool:\n"
        '  {"thought": "<one short sentence>", "action": "search_playbooks", "action_input": {"keyword": "ransomware"}}\n'
        "To speak to the team (give a step, ask a question, or ask for approval):\n"
        '  {"thought": "<one short sentence>", "final_answer": "<what you tell the team>", "evidence_path": "<the playbook section you used>"}\n\n'
        "HOW TO RESPOND TO AN INCIDENT:\n"
        "1. Identify the matching playbook (search_playbooks / read_playbook) and tell the team the FIRST step.\n"
        "2. Management notification: draft_email to show the team the message, then ASK them to approve it. "
        "Only after they reply with approval may you call send_email with approved=true. Never send without approval.\n"
        "3. Evidence: use recommend_collection to give the exact tools, commands, and paths from the playbook.\n"
        "4. When the team has collected artifacts (list_evidence shows them), read_evidence / search_evidence / "
        "run_sql to analyse them and answer their questions.\n\n"
        "RULES: base every instruction on the plan/playbooks and cite the section in evidence_path; do only one "
        "thing per step; keep answers short and actionable; never invent commands or data; ask for approval "
        "before any notification. /no_think"
    )


def quick_agent(message, client, model, tools, history=None, **kw):
    prompt = build_ir_system_prompt(tools)
    return run_agent(message, client, model, tools, prompt, history=history, **kw)

"""
bugkit.py - a forensic agent over an Android BUG REPORT (adb bugreport).

A bug report is one big sectioned text file (device info, packages, battery, wifi,
accounts, logcat, ...). This reuses the same agent loop as agentkit, but gives it tools
that navigate a bug report instead of a filesystem image: list its sections, read a
section, or search it. Students can point it at their OWN `adb bugreport` output.
"""
import re
import zipfile
from pathlib import Path

import agentkit as ak  # reuse connect_model, parse_action, run_agent, run_agent_iter, answer_text

connect_model = ak.connect_model
run_agent = ak.run_agent
run_agent_iter = ak.run_agent_iter
answer_text = ak.answer_text

_SECTION_RE = re.compile(r"^-{3,}\s*(.+?)\s*-{3,}\s*$")


def _read_any(path):
    """Read a bug report from a .txt, or the first bugreport*.txt inside a .zip."""
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".txt") and "bugreport" in n.lower()]
            names = names or [n for n in z.namelist() if n.lower().endswith(".txt")]
            if not names:
                raise ValueError("no .txt bug report found inside the zip")
            return z.read(names[0]).decode("utf-8", "replace")
    return p.read_text(errors="replace")


def load_report(path):
    """Return a list of (section_title, section_body) in order."""
    text = _read_any(path)
    sections, title, cur = [], "HEADER", []
    for line in text.splitlines():
        m = _SECTION_RE.match(line)
        if m:
            sections.append((title, "\n".join(cur)))
            title, cur = m.group(1).strip(), []
        else:
            cur.append(line)
    sections.append((title, "\n".join(cur)))
    return sections


def make_bug_tools(sections):
    """Three read-only tools over a parsed bug report."""
    def list_sections():
        """List the sections of the bug report, by number and title."""
        return "\n".join(f"{i}. {t}" for i, (t, _) in enumerate(sections))

    def read_section(name, max_chars=1800):
        """Read one section, found by its number or by text in its title."""
        key = (name or "").strip().lower()
        for i, (t, body) in enumerate(sections):
            if key == str(i) or (key and key in t.lower()):
                body = body.strip() or "(section is empty)"
                return f"[{t}]\n" + (body[:max_chars] + ("" if len(body) <= max_chars else "\n...[truncated]"))
        return f"No section matching {name!r}. Use list_sections to see the titles."

    def search_report(keyword, max_hits=25):
        """Search the whole bug report for a keyword; returns [section] matching lines."""
        key = (keyword or "").lower()
        out = []
        for t, body in sections:
            for line in body.splitlines():
                if key in line.lower():
                    out.append(f"[{t}] {line.strip()[:140]}")
                    if len(out) >= max_hits:
                        return "\n".join(out) + "\n...[more matches not shown]"
        return "\n".join(out) if out else f"No matches for {keyword!r}."

    return {"list_sections": list_sections, "read_section": read_section, "search_report": search_report}


def build_bug_system_prompt(tools):
    return (
        "You are Hermes, a digital-forensics examiner's assistant. You are reading an Android BUG REPORT "
        "(the output of `adb bugreport`): one large text file split into sections such as device "
        "properties, installed packages, battery, Wi-Fi, accounts, and the system log. You answer the "
        "examiner's question using ONLY what the tools return.\n\n"
        "TOOLS (use exactly one per step):\n" + ak.tool_descriptions(tools) + "\n\n"
        "HOW TO REPLY: send ONE JSON object and nothing else.\n"
        "To use a tool:\n"
        '  {"thought": "<one short sentence>", "action": "search_report", "action_input": {"keyword": "battery"}}\n'
        "When you can answer, reply:\n"
        '  {"thought": "<one short sentence>", "final_answer": "<your answer>", "evidence_path": "<the section you used>"}\n\n'
        "RULES: investigate step by step; a good first move is often search_report for a keyword, or "
        "list_sections to see what is there; use ONLY what the tools return; never invent data; if the "
        "answer is not in the report, say so; cite the section you used in evidence_path. /no_think"
    )


def quick_agent(question, client, model, sections, **kw):
    """Convenience: build tools + prompt for a report and run the agent."""
    tools = make_bug_tools(sections)
    return run_agent(question, client, model, tools, build_bug_system_prompt(tools), **kw)

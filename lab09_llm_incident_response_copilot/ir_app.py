"""
ir_app.py - Sectra First Responder: a Gradio incident-response copilot.

The team chats with Sectra during an incident. Sectra uses the company's IR plan and
playbooks to walk them through the response, drafts the management notification (and only
"sends" it - simulated - after the team approves in chat), recommends the exact collection
commands, and reads back any artifacts the team uploads. Everything is a drill; no real email.

Config via environment (optional):
  PROVIDER / MODEL / OPENROUTER_API_KEY   (as in the other labs)
  KNOWLEDGE_DIR    folder of the plan + playbooks (.md/.txt/.pdf/.docx). Default: knowledge
  ORG              company name shown to the agent. Default: SectraTEK
"""
import os
import shutil
import tempfile
import gradio as gr
import irkit as ik

PROVIDER = os.environ.get("PROVIDER", "openrouter")
MODEL = os.environ.get("MODEL") or None
ORG = os.environ.get("ORG", "SectraTEK")
KNOWLEDGE_DIR = os.environ.get("KNOWLEDGE_DIR", "knowledge")

_client = None
_model = None


def get_client():
    global _client, _model
    if _client is None:
        _client, _model = ik.connect_model(PROVIDER, MODEL)
    return _client, _model


def _new_state():
    try:
        kn = ik.load_knowledge(KNOWLEDGE_DIR)
    except Exception:
        kn = {}
    return {"knowledge": kn, "evidence_root": tempfile.mkdtemp(prefix="evidence_"), "action_log": []}


def _fmt(args):
    return ", ".join(f"{k}={v!r}" for k, v in (args or {}).items())


def _log_md(state):
    log = (state or {}).get("action_log", [])
    if not log:
        return "*No actions yet. Sectra will record notifications and collection steps here (all simulated).*"
    return "### Action log (drill)\n" + "\n".join(f"- {e}" for e in log)


def _as_text(c):
    """Gradio can round-trip message content as a list of parts; coerce to a string."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join((x.get("text") or x.get("content") or "") if isinstance(x, dict) else str(x)
                        for x in c)
    return str(c or "")


def _pairs(history):
    out, pending = [], None
    for m in history or []:
        if m.get("role") == "user":
            pending = _as_text(m.get("content"))
        elif m.get("role") == "assistant" and pending is not None:
            out.append((pending, _as_text(m.get("content")).split("---")[-1].strip()))
            pending = None
    return out[-5:]


def load_playbooks(files, state):
    if not files:
        return state, _playbook_status(state)
    d = tempfile.mkdtemp(prefix="playbooks_")
    for f in files:
        if f and f.lower().endswith((".md", ".markdown", ".txt", ".pdf", ".docx")):
            shutil.copy(f, d)
    try:
        state = {**state, "knowledge": ik.load_knowledge(d)}
    except Exception as e:
        return state, f"Could not read those playbooks: {e}"
    return state, _playbook_status(state)


def _playbook_status(state):
    kn = (state or {}).get("knowledge", {})
    return f"**Playbooks loaded:** {', '.join(kn) if kn else '(none)'}"


def add_evidence(files, state):
    if not files:
        return "No artifacts added."
    root = state["evidence_root"]
    names = []
    for f in files:
        if f:
            shutil.copy(f, root)
            names.append(os.path.basename(f))
    return f"**Collected into the evidence folder:** {', '.join(names)}"


def on_user(message, history):
    if not message.strip():
        return "", history
    return "", (history or []) + [{"role": "user", "content": message}]


def on_bot(history, state):
    q = _as_text(history[-1]["content"])
    try:
        client, model = get_client()
    except Exception as e:
        history.append({"role": "assistant", "content": f"Could not connect to the model: {e}"})
        yield history, _log_md(state)
        return
    tools = ik.make_ir_tools(state["knowledge"], state["evidence_root"], state["action_log"], org=ORG)
    prompt = ik.build_ir_system_prompt(tools, org=ORG)
    trace = "*Checking the plan and playbooks...*\n\n"
    history = history + [{"role": "assistant", "content": trace}]
    yield history, _log_md(state)
    final = None
    try:
        for ev in ik.run_agent_iter(q, client, model, tools, prompt, max_steps=14, history=_pairs(history[:-2])):
            if "final_answer" in ev:
                final = ev
            else:
                th = (ev.get("thought") or "").strip()
                line = f"{ev['step']}. **{ev['action']}**(`{_fmt(ev['args'])}`)"
                trace += (f"{ev['step']}. _{th}_\n   **{ev['action']}**(`{_fmt(ev['args'])}`)\n\n"
                          if th else line + "\n\n")
                history[-1]["content"] = trace
                yield history, _log_md(state)
    except Exception as e:
        history[-1]["content"] = trace + f"\n\n**Model call failed:** {e}\n(Free models are rate-limited; try again.)"
        yield history, _log_md(state)
        return
    if final and final.get("final_answer"):
        cite = final.get("evidence_path")
        ans = final["final_answer"] + (f"\n\n`playbook: {cite}`" if cite else "")
    else:
        ans = "I could not find that in the plan or playbooks. Tell me the incident type, or ask about a specific step."
    history[-1]["content"] = trace + "\n---\n" + ans
    yield history, _log_md(state)


INTRO = (
    f"# Sectra First Responder\n"
    f"An incident-response copilot for **{ORG}** (training drill). Tell Sectra what you think is "
    "happening; it walks you through the response from the company's plan and playbooks, drafts the "
    "management notification (and only **sends it - simulated -** after you approve), recommends the "
    "exact collection commands, and reads the artifacts you upload.\n\n"
    f"*Model: `{PROVIDER}` / `{MODEL or 'default Qwen'}`  ·  All emails are simulated; nothing is really sent.*"
)

EXAMPLES = [
    "We think we have ransomware on a finance workstation.",
    "We're seeing large unusual uploads from one host - possible data theft.",
    "Draft the management notification.",
    "Approve - send it.",
    "What evidence should we collect, and how?",
    "We uploaded security_events.log - build a timeline of what happened.",
    "Pull the indicators out of dns_queries.csv and check them against the watch-list.",
    "What should we do to contain and eradicate this?",
    "Write the after-action report.",
]


def build_demo():
    with gr.Blocks(title="Sectra First Responder") as demo:
        state = gr.State(_new_state())
        gr.Markdown(INTRO)
        with gr.Row():
            with gr.Column(scale=2):
                chat = gr.Chatbot(height=430, show_label=False)
                msg = gr.Textbox(placeholder="Tell Sectra what's happening, or reply (e.g. 'approve')...",
                                 show_label=False)
                gr.Examples(examples=EXAMPLES, inputs=msg)
            with gr.Column(scale=1):
                pb = gr.Markdown(_playbook_status(_new_state()))
                pb_up = gr.File(label="Replace playbooks (.md / .txt / .pdf / .docx, optional)",
                                file_count="multiple",
                                file_types=[".md", ".markdown", ".txt", ".pdf", ".docx"],
                                type="filepath")
                ev_up = gr.File(label="Upload collected artifacts (logs, csv, db...)",
                                file_count="multiple", type="filepath")
                ev_status = gr.Markdown("*Collected artifacts appear here.*")
                action_log = gr.Markdown(_log_md(None))
        pb_up.change(load_playbooks, [pb_up, state], [state, pb])
        ev_up.change(add_evidence, [ev_up, state], [ev_status])
        msg.submit(on_user, [msg, chat], [msg, chat]).then(on_bot, [chat, state], [chat, action_log])
    return demo


def launch(**kwargs):
    opts = dict(theme=gr.themes.Soft())
    opts.update(kwargs)
    build_demo().launch(**opts)


if __name__ == "__main__":
    launch()

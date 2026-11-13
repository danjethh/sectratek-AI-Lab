"""
memory_app.py - Sectra Memory Analyst: a Gradio chat for memory forensics with Volatility 3.

Ask a question about the memory image in plain English. Sectra picks a Volatility plugin, runs it,
reads the output, and answers - citing the plugin and PID behind every claim. The right-hand panel
shows the case, the Volatility commands actually run, and the findings recorded so far.

Config via environment (optional):
  PROVIDER        groq (default) | openrouter | ollama
  MODEL           model id (default: the first free model your key can use, see agentkit.GROQ_MODELS)
  GROQ_API_KEY    your free Groq key (or OPENROUTER_API_KEY for openrouter)
  MEMORY_IMAGE    path to the memory image. Default: memory/cridex.vmem (downloaded by the notebook)
"""
import os
import gradio as gr
import memkit as mk

PROVIDER = os.environ.get("PROVIDER", "groq")
MODEL = os.environ.get("MODEL") or None
MEMORY_IMAGE = os.environ.get("MEMORY_IMAGE", "memory/cridex.vmem")
CASE_NAME = "case MF-2026-001"

_client = None
_model = None


def get_client():
    global _client, _model
    if _client is None:
        _client, _model = mk.connect_model(PROVIDER, MODEL)
    return _client, _model


def _new_state():
    # Plain data only: Gradio copies State per session, so tools are rebuilt each turn from these lists
    # (Volatility results stay cached on disk in .volcache, so rebuilding is instant).
    return {"findings": [], "ran": []}


def _tools(state):
    # compatible_only: the agent only gets plugins verified to return data on THIS image
    # (the check is cached, so this is instant after the first run)
    return mk.make_memory_tools(MEMORY_IMAGE, case_dir="case", cache_dir=".volcache",
                                findings=state["findings"], ran=state["ran"], compatible_only=True)


def _case_md():
    p = os.path.join("case", "case_brief.md")
    return open(p).read() if os.path.exists(p) else "*No case brief found.*"


def _fmt(args):
    return ", ".join(f"{k}={v!r}" for k, v in (args or {}).items())


def _as_text(c):
    """Gradio can round-trip message content as a list of parts; coerce to a string."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join((x.get("text") or x.get("content") or "") if isinstance(x, dict) else str(x) for x in c)
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


def _side_md(state):
    ran = state["ran"]
    f = state["findings"]
    parts = [f"**Image:** `{os.path.basename(MEMORY_IMAGE)}`"
             + ("" if os.path.exists(MEMORY_IMAGE) else "  \n:warning: *not found - run the download cell or set MEMORY_IMAGE*")]
    parts.append("### Volatility commands run\n" + ("\n".join(f"- `{c}`" for c in ran) if ran else "*None yet.*"))
    parts.append("### Findings recorded\n" + ("\n".join(f"{i}. {x['finding']}  \n   *{x['evidence']}*"
                                                      for i, x in enumerate(f, 1)) if f else "*None yet.*"))
    return "\n\n".join(parts)


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
        yield history, _side_md(state)
        return
    if not os.path.exists(MEMORY_IMAGE):
        history.append({"role": "assistant", "content": f"No memory image at `{MEMORY_IMAGE}`. Run the "
                        "download cell in the notebook first (or set MEMORY_IMAGE to your own image)."})
        yield history, _side_md(state)
        return
    all_tools = _tools(state)
    tools = mk.agent_tools(all_tools)
    prompt = mk.build_memory_system_prompt(all_tools, CASE_NAME)
    trace = "*Working the case with Volatility...*\n\n"
    history = history + [{"role": "assistant", "content": trace}]
    yield history, _side_md(state)
    final = None
    try:
        for ev in mk.run_agent_iter(q, client, model, tools, prompt, max_steps=12, history=_pairs(history[:-2])):
            if "final_answer" in ev:
                final = ev
            else:
                th = (ev.get("thought") or "").strip()
                call = f"**{ev['action']}**(`{_fmt(ev['args'])}`)"
                trace += f"{ev['step']}. _{th}_\n   {call}\n\n" if th else f"{ev['step']}. {call}\n\n"
                history[-1]["content"] = trace
                yield history, _side_md(state)
    except Exception as e:
        history[-1]["content"] = trace + f"\n\n**Model call failed:** {e}\n(Free tiers are rate-limited; try again.)"
        yield history, _side_md(state)
        return
    if final and final.get("final_answer"):
        cite = final.get("evidence_path")
        ans = final["final_answer"] + (f"\n\n`evidence: {cite}`" if cite else "")
    else:
        ans = "I could not reach a supported answer within my step limit. Try a narrower question (for example, about one PID)."
    history[-1]["content"] = trace + "\n---\n" + ans
    yield history, _side_md(state)


INTRO = (
    "# Sectra Memory Analyst\n"
    "A memory-forensics analyst working **case MF-2026-001**. Ask about the memory image in plain English; "
    "Sectra picks a **Volatility 3 plugin**, runs it, reads the output, and answers - citing the plugin and "
    "PID behind every claim. A suspicious hit is a lead until a second plugin backs it up.\n\n"
    f"*Model: `{PROVIDER}` / `{MODEL or 'auto-picked free model'}`  ·  Every plugin is read-only and runs once (cached).*"
)

EXAMPLES = [
    "What operating system is this, and when was memory captured?",
    "Show me the process tree. Is anything unusual?",
    "Is there evidence of injected code in any process?",
    "What did PID 1640 run, and what launched it?",
    "Are there any network indicators in memory, and which process holds them?",
    "Record what you have confirmed, then write the findings report.",
]


def _compat_md():
    if not os.path.exists(MEMORY_IMAGE):
        return ""
    compat = mk.check_plugins(MEMORY_IMAGE, ".volcache", verbose=False)
    ok = sum(1 for r in compat.values() if r["status"] == "ok")
    left = [f"`{n}` ({r['note']})" for n, r in compat.items() if r["status"] != "ok"]
    return (f"**Plugins working on this image:** {ok} of {len(compat)}"
            + ("  \nLeft out: " + "; ".join(left) if left else ""))


def build_demo():
    if os.path.exists(MEMORY_IMAGE):     # check plugin compatibility once, before the first question
        mk.check_plugins(MEMORY_IMAGE, ".volcache")
    with gr.Blocks(title="Sectra Memory Analyst") as demo:
        state = gr.State(_new_state())
        gr.Markdown(INTRO)
        with gr.Row():
            with gr.Column(scale=2):
                chat = gr.Chatbot(height=460, show_label=False)
                msg = gr.Textbox(placeholder="Ask about the memory image...", show_label=False)
                gr.Examples(examples=EXAMPLES, inputs=msg)
            with gr.Column(scale=1):
                with gr.Accordion("Case brief", open=False):
                    gr.Markdown(_case_md())
                gr.Markdown(_compat_md())
                side = gr.Markdown(_side_md(_new_state()))
        msg.submit(on_user, [msg, chat], [msg, chat]).then(on_bot, [chat, state], [chat, side])
    return demo


def launch(**kwargs):
    opts = dict(theme=gr.themes.Soft())
    opts.update(kwargs)
    build_demo().launch(**opts)


if __name__ == "__main__":
    launch()

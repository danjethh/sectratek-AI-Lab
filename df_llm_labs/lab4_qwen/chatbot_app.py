"""
chatbot_app.py - a Gradio chatbot over the synthetic Android device image.

Runs the same forensic agent as the lab, but as an interactive chat: students ask
questions in plain English and watch the agent navigate the image and answer with a
citation. Works in Colab (demo.launch(share=True)) and locally (python chatbot_app.py).

Config via environment variables (all optional):
  PROVIDER        'openrouter' (default) or 'ollama'
  MODEL           model id (defaults: openrouter qwen/qwen3-30b-a3b:free, ollama qwen3:8b)
  OPENROUTER_API_KEY   your free key (OpenRouter only)
  ALLOW_PYTHON    '1' to enable the optional, advanced run_python tool (off by default)
"""
import os
import gradio as gr
import agentkit as ak

PROVIDER = os.environ.get("PROVIDER", "openrouter")
MODEL = os.environ.get("MODEL") or None
ALLOW_PYTHON = os.environ.get("ALLOW_PYTHON", "0") == "1"

ak.build_image("android_image")
TOOLS = ak.make_tools("android_image", allow_python=ALLOW_PYTHON)
SYSTEM_PROMPT = ak.build_system_prompt(TOOLS)

_client = None
_model = None


def get_client():
    global _client, _model
    if _client is None:
        _client, _model = ak.connect_model(PROVIDER, MODEL)
    return _client, _model


def _fmt_args(args):
    return ", ".join(f"{k}={v!r}" for k, v in (args or {}).items())


def _history_pairs(history):
    """Gradio history -> agentkit [(user, assistant)] pairs. Tolerates both the
    'messages' format (list of {role, content}) and the old tuples format."""
    pairs, pending = [], None
    for m in history or []:
        if isinstance(m, dict):
            role, content = m.get("role"), m.get("content", "")
            if role == "user":
                pending = content
            elif role == "assistant" and pending is not None:
                pairs.append((pending, content.split("---")[-1].strip()))
                pending = None
        elif isinstance(m, (list, tuple)) and len(m) == 2:
            u, a = m
            pairs.append((u or "", (a or "").split("---")[-1].strip()))
    return pairs[-4:]  # last few turns is plenty of context


def respond(message, history):
    """Stream the agent's reasoning trace, then its final cited answer."""
    try:
        client, model = get_client()
    except Exception as e:
        yield f"Could not connect to the model: {e}"
        return
    pairs = _history_pairs(history)
    trace = "*Investigating the image...*\n\n"
    yield trace
    final = None
    try:
        for ev in ak.run_agent_iter(message, client, model, TOOLS, SYSTEM_PROMPT, history=pairs):
            if "final_answer" in ev:
                final = ev
            else:
                line = f"**{ev['action']}**(`{_fmt_args(ev['args'])}`)"
                if ev.get("thought"):
                    line = f"_{ev['thought']}_\n{line}"
                trace += f"{ev['step']}. {line}\n\n"
                yield trace
    except Exception as e:
        yield trace + f"\n\n**The model call failed:** {e}\n\n(Free models are rate-limited; wait a moment and try again.)"
        return
    if final and final.get("final_answer"):
        ans = f"### {final['final_answer']}\n\n`source: {final.get('evidence_path') or '(none cited)'}`"
    else:
        ans = ("I could not find that in the image. Try rephrasing, or name the kind of artifact you "
               "expect (an account, a message, an app, a Wi-Fi network).")
    yield trace + "\n---\n" + ans


EXAMPLES = [
    "Which email accounts are signed in on this device?",
    "What phone model is this and which Android version?",
    "How many contacts are saved?",
    "What is the most recent text message that was sent, and to whom?",
    "Which messaging or social apps are installed?",
    "What Wi-Fi networks has this device connected to?",
]


DESCRIPTION = (
    "A forensic agent over a synthetic Android extraction. Ask a plain-English question; the agent "
    "navigates the image with read-only tools and answers **with the exact file it used**.  \n"
    f"*Model: `{PROVIDER}` / `{MODEL or 'default Qwen'}`"
    + ("  ·  run_python tool: ON (advanced)*" if ALLOW_PYTHON else "*"))


def build_demo():
    return gr.ChatInterface(
        fn=respond,
        title="Ask the Device",
        description=DESCRIPTION,
        examples=EXAMPLES,
    )


def launch(**kwargs):
    opts = dict(theme=gr.themes.Soft())
    opts.update(kwargs)
    build_demo().launch(**opts)


if __name__ == "__main__":
    launch()

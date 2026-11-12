"""
bugreport_app.py - a Gradio chatbot that answers questions about an Android BUG REPORT.

Students can upload their OWN `adb bugreport` output (.txt or .zip), or use the bundled
synthetic sample. The agent navigates the report's sections and answers with the section
it used. Works in Colab (launch(share=True)) and locally (python bugreport_app.py).

Config via environment (optional):
  PROVIDER        'openrouter' (default) or 'ollama'
  MODEL           model id (defaults to a free Qwen on OpenRouter, qwen3:8b on Ollama)
  OPENROUTER_API_KEY   your free key (OpenRouter only)
  BUGREPORT_PATH  path to the sample bug report (default: sample_bugreport.txt)
"""
import os
import gradio as gr
import bugkit as bk

PROVIDER = os.environ.get("PROVIDER", "openrouter")
MODEL = os.environ.get("MODEL") or None
SAMPLE = os.environ.get("BUGREPORT_PATH", "sample_bugreport.txt")

_client = None
_model = None


def get_client():
    global _client, _model
    if _client is None:
        _client, _model = bk.connect_model(PROVIDER, MODEL)
    return _client, _model


def _load_sample_state():
    try:
        return {"sections": bk.load_report(SAMPLE), "name": "bundled sample"}
    except Exception:
        return {"sections": [("HEADER", "(no sample report found)")], "name": "none"}


def _fmt(args):
    return ", ".join(f"{k}={v!r}" for k, v in (args or {}).items())


def _pairs(history):
    out = []
    pending = None
    for m in history or []:
        if m.get("role") == "user":
            pending = m.get("content")
        elif m.get("role") == "assistant" and pending is not None:
            out.append((pending, (m.get("content") or "").split("---")[-1].strip()))
            pending = None
    return out[-4:]


def on_upload(filepath, state):
    if not filepath:
        return state, "No file chosen. Using the bundled sample."
    try:
        sections = bk.load_report(filepath)
        name = os.path.basename(filepath)
        return {"sections": sections, "name": name}, f"Loaded **{len(sections)} sections** from `{name}`."
    except Exception as e:
        return state, f"Could not read that file: {e}"


def on_user(message, history):
    if not message.strip():
        return "", history
    return "", (history or []) + [{"role": "user", "content": message}]


def on_bot(history, state):
    q = history[-1]["content"]
    try:
        client, model = get_client()
    except Exception as e:
        history.append({"role": "assistant", "content": f"Could not connect to the model: {e}"})
        yield history
        return
    sections = (state or _load_sample_state())["sections"]
    tools = bk.make_bug_tools(sections)
    prompt = bk.build_bug_system_prompt(tools)
    trace = "*Reading the bug report...*\n\n"
    history = history + [{"role": "assistant", "content": trace}]
    yield history
    final = None
    try:
        for ev in bk.run_agent_iter(q, client, model, tools, prompt, history=_pairs(history[:-2])):
            if "final_answer" in ev:
                final = ev
            else:
                trace += f"{ev['step']}. **{ev['action']}**(`{_fmt(ev['args'])}`)\n\n"
                history[-1]["content"] = trace
                yield history
    except Exception as e:
        history[-1]["content"] = trace + f"\n\n**Model call failed:** {e}\n(Free models are rate-limited; try again shortly.)"
        yield history
        return
    if final and final.get("final_answer"):
        ans = f"### {final['final_answer']}\n\n`section: {final.get('evidence_path') or '(none cited)'}`"
    else:
        ans = "I could not find that in the bug report. Try a different keyword, or ask about device info, apps, battery, Wi-Fi, accounts, or the log."
    history[-1]["content"] = trace + "\n---\n" + ans
    yield history


EXAMPLES = [
    "What phone model and Android version is this?",
    "Who is the account owner of this device?",
    "Which apps are installed?",
    "What is the battery level?",
    "What Wi-Fi networks are saved?",
    "Are there any errors or crashes in the system log?",
]


def build_demo():
    with gr.Blocks(title="SectraTEK - Ask the Bug Report") as demo:
        state = gr.State(_load_sample_state())
        gr.Markdown(
            "# Ask the Bug Report\n"
            "A forensic agent over an Android **bug report** (`adb bugreport`). Upload your own report "
            "(.txt or .zip) or use the bundled synthetic sample, then ask questions in plain English. "
            "The agent searches the report's sections and answers **with the section it used**.\n\n"
            f"*Model: `{PROVIDER}` / `{MODEL or 'default Qwen'}`*")
        with gr.Row():
            upload = gr.File(label="Upload a bug report (.txt or .zip)", file_types=[".txt", ".zip"],
                             type="filepath", scale=3)
            status = gr.Markdown("Using the **bundled sample** bug report.")
        chat = gr.Chatbot(height=430, show_label=False)
        msg = gr.Textbox(placeholder="Ask about the device, apps, battery, Wi-Fi, accounts, or the log...",
                         show_label=False)
        gr.Examples(examples=EXAMPLES, inputs=msg)
        upload.change(on_upload, [upload, state], [state, status])
        msg.submit(on_user, [msg, chat], [msg, chat]).then(on_bot, [chat, state], [chat])
    return demo


def launch(**kwargs):
    opts = dict(theme=gr.themes.Soft())
    opts.update(kwargs)
    build_demo().launch(**opts)


if __name__ == "__main__":
    launch()

# Sectra First Responder: an Incident-Response Chatbot over your Plan and Playbooks

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danjethh/sectratek-AI-Lab/blob/main/df_llm_labs/ir_first_responder/ir_chatbot_ui.ipynb)

> When an incident hits, the team calls **Sectra**. They say what they think is happening; Sectra walks
> them through the response from the company's **IR plan and playbooks**, drafts the management
> notification (and only "sends" it - simulated - once the team approves), recommends the exact
> collection commands, and reads back the artifacts the team uploads. Every step cites the playbook.

**Course:** AI for Cybersecurity and Digital Forensics
**Technique:** A retrieval-grounded, tool-using agent with a human in the loop
**Runtime:** Google Colab or local, free Qwen via OpenRouter (or local Ollama)

---

## What it does

This is a RAG + agent copilot for incident response. Its knowledge is the company's own plan and
playbooks; its actions are gated by the team's approval. A typical drill:

1. **Team:** "We think we have ransomware on a finance workstation."
2. **Sectra** finds the ransomware playbook, classifies it (SEV-1), and gives the first step
   (isolate the host, do **not** power it off), citing the playbook section.
3. **Sectra** offers to notify management. On request it **drafts** the email, pulling the template
   from the playbook, and asks the team to approve.
4. **Team:** "approve." **Sectra** records a **simulated** send to the management distribution list
   (no real email is ever sent) and moves on.
5. **Sectra** recommends the exact **collection** tools, commands, and paths from the playbook.
6. The team collects artifacts and **uploads** them; Sectra reads/searches them and answers
   (e.g. "the security log shows the audit log was cleared - Event 1102 - and shadow copies deleted").

## The tools

| Group | Tools | What they do |
|---|---|---|
| **Knowledge (read-only)** | `list_playbooks`, `search_playbooks`, `read_playbook` | Find and read the plan and playbooks. |
| **Actions (gated)** | `draft_email`, `send_email`, `recommend_collection` | Draft a notification (from the playbook template), **simulate** sending it only after approval, and give collection commands. |
| **Evidence (read-only)** | `list_evidence`, `read_evidence`, `search_evidence`, `run_sql` | Read and query the artifacts the team uploads. |

## Bring your own

- **Playbooks:** drop your own `.md` plan/playbooks into the `knowledge/` folder (or upload them in the
  UI). A sample plan plus ransomware/phishing/exfiltration playbooks are bundled.
- **Artifacts:** upload your own logs/CSV/SQLite into the evidence folder (or the UI). Two synthetic
  samples (`security_events.log`, `dns_queries.csv`) are bundled. Everything shipped is fictional.

## Two ways to run it

| File | What it is |
|---|---|
| `ir_chatbot_ui.ipynb` | **UI version** - a Gradio chat with playbook/evidence upload and a live action log. |
| `ir_first_responder_jupyter.ipynb` | **Jupyter version** - `talk("...")` in a cell; Sectra remembers the conversation so approvals work. |
| `ir_app.py` | The Gradio app as a script (`python ir_app.py`). |
| `irkit.py` | The IR tools, the system prompt, and the plan/playbook loader. |
| `agentkit.py` | The shared agent core (model connection, the think-act-observe loop). |
| `knowledge/`, `evidence/` | The bundled sample plan + playbooks, and the sample artifacts. |

## Design notes and recommendations (read these)

These are deliberate choices; keep them if you adapt the lab.

- **Human-in-the-loop for anything external.** The agent may *draft* a notification freely, but it may
  only *send* after the team approves in the chat, and even then the send is **simulated and logged** -
  the lab never wires real email. For production, keep the approval gate and put a real integration
  behind it; never let the model send on its own.
- **It recommends, it does not execute.** Sectra gives the collection commands and paths; a human runs
  them. An IR copilot should not be executing privileged commands on hosts during an incident.
- **Grounded and cited.** Every instruction is based on the plan/playbooks and names the section it came
  from, so the team can verify it. The model is told to say so plainly when the answer is not in the
  playbooks rather than invent one.
- **Read-only, sandboxed evidence.** Artifact tools can read and query but never modify evidence, and
  are confined to the evidence folder.
- **Keep an action log / timeline.** The UI shows every simulated notification and collection step; the
  Jupyter version exposes `ACTION_LOG`. A real response needs this timeline.
- **The model is an assistant, not the incident commander.** Decisions (declaring severity, isolating
  production, legal/customer notification) stay with people. Free models also vary run to run; re-run or
  rephrase if a step is missed.
- **Natural extensions:** a severity classifier, links to ticketing/Slack behind approval, more playbooks,
  and an "after-action" summary generated from the action log.

## Running locally with no API key (Ollama)

Install [Ollama](https://ollama.com), `ollama pull qwen3:8b`, then set `PROVIDER=ollama` before launching.
Nothing leaves your machine - useful when the playbooks or artifacts are sensitive.

## Credits

Lab design and code by Daniel Kwaku Ntiamoah Addai, SectraTEK Lab. Driven by an open-source **Qwen**
model via a free, OpenAI-compatible endpoint (OpenRouter) or local Ollama. All plans, playbooks, contacts,
and artifacts in this lab are synthetic.

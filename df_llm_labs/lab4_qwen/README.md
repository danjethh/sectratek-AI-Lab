# Practical 4: A Forensic Agent Over an Android Image

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danjethh/sectratek-AI-Lab/blob/main/df_llm_labs/lab4_qwen/04_lab_notebook.ipynb)

> Ask a plain-English investigation question over a whole device image and get an answer that is read
> from the real artifact and cites the exact file, instead of a confident guess from the model's memory.

**Course:** AI for Cybersecurity and Digital Forensics
**Technique:** A tool-using agent (the ReAct pattern), built from scratch
**Runtime:** Google Colab or any hosted Jupyter, free Qwen model via OpenRouter, no local install

---

## Abstract

This practical teaches the **agent** idea: a language model that does not answer from memory but instead
**acts**, calling tools to open the evidence, reading what it finds, and answering only from that. The
student builds a small forensic agent by hand over a synthetic Android extraction. The agent is given
three read-only tools (list a folder, read a file, run a SQL query), and a loop that lets a lightweight
**Qwen** model think, call one tool, observe the result, and repeat until it can answer, with the file it
used named as the citation. A side-by-side comparison shows the point: asked which accounts are on the phone, a plain
model invents a fluent, specific, wrong name; the agent walks the image, reads the real account database,
and answers with the artifact path. The whole thing is a few lines of plain Python, so every decision and
every source is visible. The discipline is the same one that runs through this course: say only what the
evidence supports, and show where it came from.

---

## Table of contents

1. [Background](#1-background)
2. [Problem statement](#2-problem-statement)
3. [Gaps this lab addresses](#3-gaps-this-lab-addresses)
4. [The solution: a tool-using agent](#4-the-solution-a-tool-using-agent)
5. [Methods and approach](#5-methods-and-approach)
6. [The device image](#6-the-device-image)
7. [Practical: running the lab](#7-practical-running-the-lab)
8. [Worked example](#8-worked-example)
9. [Discussion](#9-discussion)
10. [Learning outcomes and assessment](#10-learning-outcomes-and-assessment)
11. [Files in this lab](#11-files-in-this-lab)
12. [Credits](#12-credits)

---

## 1. Background

To answer a simple question from a phone image, such as *which accounts are signed in on this device?*, an examiner has to do
two things: **know which artifact holds the answer** (out of thousands of files in a full extraction), and
then **write SQL** to pull the record from the right table of the right database. This is precise and
defensible, and it is how the skill has always been taught. Its cost is that it needs an expert who
already knows the map of the device, and it has to be repeated by hand for every new question.

The tempting shortcut, asking a chatbot directly, is worse. The model was trained on the public web, not
on this phone, so when asked which accounts are on a device it cannot see, it does not say so: it invents a plausible,
fluent, and entirely fictional owner, with no file behind it.

---

## 2. Problem statement

> **How do we let a language model answer investigation questions about a specific device image,
> accurately and with a traceable source, instead of guessing?**

The difficulty is access. A general-purpose model knows Android and can write SQL fluently, but it cannot
open the files on this particular device. A bigger model does not fix that. What fixes it is giving the
model **tools** so it can open the evidence itself, and a loop so it can keep looking until it has the
answer, then cite the file it used.

---

## 3. Gaps this lab addresses

| Gap | Without an agent | With the agent |
|---|---|---|
| **Expert-bound search** | You must already know which file and table hold the answer. | The agent navigates the image on its own to find the artifact. |
| **Hallucinated specifics** | A plain model invents device details it cannot know. | The agent answers only from files it actually opened. |
| **No source** | You cannot check where an answer came from. | Every answer cites the exact file it was read from. |
| **Opaque frameworks** | A library hides the tool-calling loop. | The student builds the tools and the loop by hand. |

---

## 4. The solution: a tool-using agent

```
 Question --> [ Agent: think -> call ONE tool -> observe the result ] --> repeat
                                   |                                          |
                                   +---------------- until it can answer -----+
                                                     |
                                                     v
                   [ Answer, grounded in the files it opened, citing the exact artifact ]
```

An agent has two moves on repeat. **Act:** pick one read-only tool and call it. **Observe:** take the
result as a new fact and reason from it. It loops, think-act-observe, until it has enough evidence to
answer, and the answer names the file it came from. This think-act-observe cycle is the **ReAct** pattern
(Reason + Act).

---

## 5. Methods and approach

The notebook builds the agent in two visible pieces, the tools and the loop, then compares it against the
plain model.

| Piece | What it does |
|---|---|
| **The tools** | Five read-only Python functions: `list_dir(path)`, `read_file(path)` (handles text, JSON, and points to `run_sql` for databases), `run_sql(path, query)`, `find_files(name)`, and `search_text(keyword)`. All are sealed inside the image folder and cannot change evidence. An optional, off-by-default `run_python(code)` tool (Part D) lets the agent write its own code, to show the power and the risk. |
| **The protocol** | A system prompt that asks the model to reply with one small JSON object each turn: either a tool call, or a final answer with an `evidence_path`. |
| **The loop** | Ask the model for its next move, run that one tool, feed the result back as an observation, and repeat until it answers or hits a step limit. |
| **The guardrail** | Tools are read-only and path-sandboxed. The agent cannot write, and cannot leave the device, the way a loosely-scoped agent drifts into fetching a web page it was never meant to touch. |

**Why a boundary.** Keeping the toolbox small, read-only, and locked to the image is the forensic version
of handling an exhibit: look, never alter, and stay within the evidence. It is also what keeps the agent's
reasoning on the device instead of wandering off it.

**Runtime.** The agent is driven by a small, free, open-source **Qwen** model through OpenRouter (an
OpenAI-compatible endpoint), with the key entered via a hidden prompt and never saved. The notebook builds
the synthetic image itself, so it runs standalone in Colab with no clone and no install beyond a one-time
`pip install openai`.

---

## 6. The device image

A small, synthetic Android extraction (built by the notebook under `android_image/`), shaped like a real
one so the agent has somewhere to navigate. Everything in it is fictional.

| Artifact | Holds |
|---|---|
| `data/data/com.google.android.gm/databases/accounts.db` | The Google and app accounts signed in on the device |
| `data/data/com.android.providers.contacts/databases/contacts2.db` | Saved contacts |
| `data/data/com.android.providers.telephony/databases/mmssms.db` | SMS messages |
| `data/data/com.whatsapp/databases/msgstore.db` | WhatsApp messages |
| `data/system/packages.list` | Installed apps |
| `data/misc/wifi/WifiConfigStore.xml` | Saved Wi-Fi networks |
| `data/system/users/0/settings_secure.xml` | Device properties (android_id, device name) |
| `build.prop` | Model and Android version |

All accounts, numbers, and identifiers are fabricated for teaching.

---

## 7. Practical: running the lab

1. Click the **Open in Colab** badge at the top of this page.
2. Run **Part 0** (setup): install `openai`; connect to a free Qwen model (paste an OpenRouter key); build
   the synthetic Android image.
3. Run **Part A**: define the three read-only tools, the tool protocol, and the agent loop, then ask the
   first question (*which email accounts are signed in on this device?*) and watch the reasoning trace.
4. Run **Part B**: ask the same question with and without the agent, and compare.
5. Run **Part C**: ask your own investigation questions over the image.
6. Fill in the short write-up and save the notebook.

No local install is required. The agent uses a free model, so answers may vary slightly run to run; if it
takes a wrong turn or runs out of steps, re-run the cell or name the kind of artifact you expect.

---

## 8. Worked example

**Model alone (no device):**

> "Based on a typical Android device, the owner is most likely john.doe@gmail.com." - fluent, invented,
> and with no file to check.

**With the agent (read + cited):**

> "The signed-in accounts are nadia.okafor@gmail.com (Google) and a WhatsApp number." `[data/data/com.google.android.gm/databases/accounts.db]`
> - read from the real account database, with the exact file named so you can open and confirm it.

Same question, very different trust.

---

## 9. Discussion

**Access, not a bigger model.** The value of the agent is not a smarter model; it is that the model can
open the evidence and answer from what it actually read, and name the file.

**The boundary is the point.** Read-only, sandboxed tools are what keep the agent trustworthy. An agent
with loose or write-capable tools can alter evidence or wander off the device, which is unacceptable in
forensics. The lab makes the guardrail explicit.

**The same discipline.** As in the rest of the course, the honest answer is sometimes "I could not find
that in the image." An agent that searches the evidence and cites its source is more trustworthy than a
fluent one that answers from memory.

---

## 10. Learning outcomes and assessment

By the end of this lab a student can:

1. Explain what makes a model an **agent**: tools plus a think-act-observe loop.
2. Describe the ReAct cycle and what each step (think, act, observe) contributes.
3. Explain why the tools are kept read-only and sandboxed, and why that matters for evidence.
4. Read an agent's reasoning trace and judge whether its cited file supports the answer.

**Write-up:** one answer with its evidence path, checked against the source file; a comparison of the plain
model and the agent on the same question; and one sentence on why citing the file makes the answer safer.

---

## 11. Files in this lab

| Path | What it is |
|---|---|
| `04_lab_notebook.ipynb` | The hosted (Colab/OpenRouter) step-by-step teaching notebook |
| `04_lab_notebook_local.ipynb` | The same lab, but with a **local** Qwen via Ollama (download-to-PC, no API key) |
| `chatbot_ui.ipynb` | The agent as an interactive **chatbot with a UI** (Gradio; Colab gives a public link) |
| `chatbot_jupyter.ipynb` | The agent as a **chatbot run in the notebook** (`ask("...")`, no UI framework) |
| `chatbot_app.py` | The Gradio chatbot as a script, to run locally: `python chatbot_app.py` |
| `agentkit.py` | The shared agent core (model connection, tools, the think-act-observe loop) |
| `slides/SectraTEK_Practical4_Agent.pptx` | The lecture deck for the lab |
| `slides/SectraTEK_Practical4_Chatbots.pptx` | A short deck on the chatbot pieces (both chatbots, UI vs Jupyter, Colab vs Ollama) |
| `README.md` | This document |

The synthetic Android image is created by the code itself, so there is no evidence to download.

---

## 12. Running it other ways

- **On your own PC, no API key:** open `04_lab_notebook_local.ipynb` and follow it. It uses a local Qwen
  through [Ollama](https://ollama.com) (`ollama pull qwen3:8b`), so nothing leaves your machine. Run it in
  Jupyter on your computer, not in Colab (Colab cannot reach a model on your machine).
- **As a chatbot:** `chatbot_ui.ipynb` launches a real chat window; `chatbot_jupyter.ipynb` runs the chat
  inside the notebook. Both use the same agent. A sister chatbot that answers questions about an Android
  **bug report** (which you can generate from your own phone with `adb bugreport`) lives in
  [`../bug_report_agent/`](../bug_report_agent/).
- **Letting the agent write code:** Part D of the lab adds an optional `run_python` tool. It is off by
  default and blocks obvious writes, so you can see both what it enables and why it is risky on real evidence.

---

## 13. Credits

The lab design, the synthetic image, and the from-scratch agent are original, written for this course by
Daniel Kwaku Ntiamoah Addai, SectraTEK Lab. The idea of pointing a small local model at a whole Android
image and asking a plain-English question is due to Frank Xu. The agent is driven by an open-source
**Qwen** model (https://qwenlm.github.io/) served through a free, OpenAI-compatible endpoint (OpenRouter).

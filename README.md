<p align="center">
  <a href="course_overview/SectraTEK_Course_Overview.pdf"><img src="docs/img/cover.png" alt="SectraTEK AI Lab - Five Patterns, One Discipline (course overview cover)" width="900"></a>
</p>

# SectraTEK AI Lab: Agentic AI for Digital Forensics

> A hands-on teaching lab that uses agentic AI design patterns to make digital-forensic
> reasoning more disciplined, more defensible, and easier to learn. Every lab runs in a
> hosted notebook (Google Colab) with a free model endpoint, so students install nothing on
> their own machines.

**Course:** AI for Cybersecurity and Digital Forensics
**Author and instructor:** Daniel Kwaku Ntiamoah Addai, Mobile Threat Research Lead, SectraTEK Lab ([lab.sectratek.com](https://lab.sectratek.com))
**Status:** All ten labs available: `lab01`-`lab05` agentic AI patterns, `lab06`-`lab10` LLMs for forensics.

**New here?** Start with the [Course Overview deck](course_overview/) for a 12-slide tour of the five patterns and how the labs run. Then see [labs 06-10](#labs-06-10-llms-for-forensics): RAG, device and memory analysis agents, and an incident-response copilot.

---

## Abstract

Large language models can draft a forensic report in seconds, but a fast draft is not a
defensible one: models state inferences as facts, claim outcomes the evidence does not
establish, and hide uncertainty behind fluent prose. This repository teaches a set of
**agentic AI design patterns** that wrap a model in a disciplined process, so the model
checks its own work, calls real tools instead of guessing, plans before it answers, and
divides an investigation across cooperating roles. Each pattern is taught through one
synthetic mobile-forensics case. The labs are written for cybersecurity and digital-forensics
students who may be new to programming, and they run entirely in a hosted notebook with a free
model endpoint. The learning objective is not to automate the examiner, but to give the
examiner a faster, more honest assistant whose claims stay inside the evidence.

Alongside the five pattern labs, five standalone labs (06-10) apply language models to real forensic tasks:
a retrieval-augmented assistant over case reports, tool-using agents over an Android device image,
an Android bug report, and a Windows memory image (with Volatility 3), and an incident-response copilot
grounded in a company's own plan, playbooks, and ISO 27001 ISMS. Every one of them cites the evidence
behind each answer.

---

## Table of contents

1. [Background](#1-background)
2. [Problem statement](#2-problem-statement)
3. [Gaps in current practice](#3-gaps-in-current-practice)
4. [Our solution](#4-our-solution)
5. [Methods and approach](#5-methods-and-approach)
6. [Practical: how to run the labs](#6-practical-how-to-run-the-labs)
7. [Lab index](#7-lab-index)
8. [Discussion](#8-discussion)
9. [Limitations and ethics](#9-limitations-and-ethics)
10. [Credits and provenance](#10-credits-and-provenance)
11. [License](#11-license)

---

## 1. Background

Digital forensics is the practice of recovering, preserving, and interpreting data from
devices so that the result can withstand scrutiny, often in a legal setting. The discipline
rests on a few non-negotiable ideas: evidence integrity (the data is what it claims to be and
has not been altered), provenance (every finding traces back to a specific artifact), and
defensibility (a claim is only as strong as the evidence and the reasoning behind it).

Two forces now press on this discipline at once:

- **The volume problem.** A single modern phone can hold hundreds of thousands of artifacts.
  Examiners cannot read everything, so triage and summarization matter more each year.
- **The AI opportunity, and its risk.** Large language models (LLMs) can read, summarize, and
  draft at a scale no human can match. Used naively, they also produce confident, well-written
  conclusions that are not supported by the evidence. In forensics, a plausible-sounding but
  unsupported claim is worse than no claim at all.

**Agentic AI** is the bridge. Instead of asking a model for a single answer, an agent places
the model inside a structured loop with a goal and a role, so it can review, verify, plan, and
collaborate before it returns a result. The same design patterns that make general AI agents
more reliable turn out to map cleanly onto the habits of a careful investigator.

<p align="center">
  <img src="docs/img/chatbot_to_agent.png" alt="From a chatbot to an agent: a plain answer vs a model in a loop with a goal and a role" width="860"><br>
  <sub><em>The core idea: a plain chatbot answers once and nothing catches an error; an agent puts the model in a loop with a goal and a role, so it reviews and verifies before it answers.</em></sub>
</p>

---

## 2. Problem statement

> **How can we teach students to use LLMs in digital forensics without teaching them to trust
> an overconfident machine, and do it on hardware they already have?**

The problem has three parts:

1. **Rigor.** A forensic report must separate observation from inference, cite an artifact and
   a timestamp for every claim, and state what remains uncertain. A raw LLM does none of this
   by default.
2. **Pedagogy.** Students learning this for the first time need to *see* the reasoning process,
   not just a finished answer. They need a worked loop they can step through, then a reusable
   abstraction they can apply.
3. **Access.** Many students do not have a GPU, administrator rights on their laptops, or the
   patience to install a local model server. A lab that requires a local install excludes the
   very students it is meant to reach.

---

## 3. Gaps in current practice

| Gap | What goes wrong today | What a student needs instead |
|---|---|---|
| **Overclaiming** | LLM reports assert delivery, intent, or guilt that the artifacts never establish. | A process that forces each claim back to a named artifact and timestamp. |
| **Single-shot answers** | One prompt, one answer, no self-check. Errors ship unexamined. | A loop where the model critiques and revises before anyone reads the result. |
| **Local-install labs** | Existing agentic-AI labs assume a local model server (for example Ollama) and often a GPU. | A hosted notebook with a free endpoint, nothing installed locally. |
| **Opaque tooling** | "Magic" agent frameworks hide the loop, so students learn the library, not the idea. | A manual build of the loop first, then the packaged version. |
| **Missing forensic framing** | General agent tutorials use trivia tasks with no notion of evidence or defensibility. | Real, synthetic forensic cases with artifacts, chain of custody, and an evidence boundary. |

---

## 4. Our solution

**SectraTEK AI Lab** teaches five agentic AI design patterns, each through one synthetic
mobile-forensics case, with three design commitments:

1. **Evidence-bounded by construction.** Every lab is built around the discipline of separating
   observation, inference, and claim, and of citing an artifact for each statement. The AI is a
   critique and triage aid; the forensic judgment stays with a human.
2. **Hosted, zero-install.** Every notebook runs in Google Colab (or any hosted Jupyter) against
   a free, OpenAI-compatible model endpoint. Students open one notebook, paste one free key, and
   run. Nothing is installed on their own computer.
3. **See it, then reuse it.** Each lab first builds the pattern by hand, one cell at a time, so
   the student sees every model call. Then it runs the same workflow through a small reusable
   class, so the student learns the abstraction without the loop becoming magic.

<p align="center">
  <img src="docs/img/evidence_bounded.png" alt="Evidence-bounded reasoning: observation vs inference vs overclaim" width="860"><br>
  <sub><em>The discipline every lab trains: separate what the artifacts record (observation) from a reasonable interpretation (inference), and never claim what the evidence does not establish (overclaim).</em></sub>
</p>

### The five patterns

| Pattern | The investigator's habit it mirrors | Lab |
|---|---|---|
| **Reflection** | Draft, self-critique, revise. | [Lab 1](lab01_reflection_pattern/) |
| **Tool Use** | Inspect the artifact with a real tool instead of guessing. | [Lab 2](lab02_tool_use_pattern/) |
| **ReAct** | Reason one step, act, observe, repeat. | [Lab 3](lab03_react_pattern/) |
| **Planning** | Break a hard question into checkable steps. | [Lab 4](lab04_planning_pattern/) |
| **Multiagent** | Split roles, compare findings, reconcile. | [Lab 5](lab05_multiagent_pattern/) |

<p align="center">
  <img src="docs/img/five_patterns.png" alt="The five agentic patterns: Reflection, Tool Use, ReAct, Planning, Multiagent" width="900"><br>
  <sub><em>The five patterns build on each other: Reflection, Tool Use, ReAct, Planning, then Multiagent. Start at Lab 1 and go in order.</em></sub>
</p>

---

## 5. Methods and approach

### 5.1 Model runtime

The labs use a hosted, OpenAI-compatible endpoint. The default is the **Groq free tier**
(`https://api.groq.com/openai/v1`), which serves open models at no cost and needs no credit
card. The API key is collected inside the notebook with a hidden prompt (`getpass`) and is never
written into the file. Because the client is OpenAI-compatible, an instructor can point any lab
at a different endpoint (a campus server, a different provider, or a local Ollama for offline
rooms) by changing two values. See [docs/GROQ_SETUP.md](docs/GROQ_SETUP.md). The LLM-for-forensics
labs use the same approach: Groq or OpenRouter (free open models such as Qwen and Llama), or a local
Ollama model when the evidence must not leave the machine.

### 5.2 Lab structure

Every lab follows the same four-stage pedagogy:

1. **Pre-lab evidence analysis (optional, un-graded).** Students examine the raw artifacts as a
   group, build a timeline, and record a human baseline before any model is involved.
2. **Build the loop by hand.** The notebook walks the pattern one model call at a time, with a
   short *Purpose / Input / Output* note on each step.
3. **Run the packaged agent.** The same workflow runs through a small reusable class that mirrors
   the `agentic_patterns` library, so the student sees the abstraction.
4. **Evidence check.** The student answers a short set of questions that force each claim back to
   an artifact and name what remains uncertain.

<p align="center">
  <img src="docs/img/see_it_reuse_it.png" alt="See it, then reuse it: group analysis, build by hand, run the packaged agent, evidence check" width="900"><br>
  <sub><em>Every lab follows the same path: look at the raw evidence first, build the loop by hand so every model call is visible, run the same workflow through a small reusable class, then check each claim against an artifact.</em></sub>
</p>

### 5.3 Teaching data

The five pattern labs use **synthetic** cases built for teaching. Each ships an artifact manifest, a
chain of custody log, and case-specific artifacts (file events, messages, network, location, and so
on). Where a small **real public** sample exists with published ground truth, a lab uses it instead:
the memory-forensics lab downloads the public Cridex memory image at run time and verifies it against
pinned hashes, so students can check the AI's answers against a known result. Students can also point
the labs at their own files. No real personal data is stored anywhere in this repository.

---

## 6. Practical: how to run the labs

**Students (the fast path):**

1. New to the course? Skim the [Course Overview deck](course_overview/) first. Then open the lab you
   want (start with [Lab 1](lab01_reflection_pattern/)) and click the
   **Open in Colab** badge in its notebook.
2. Run the setup cells. When prompted, paste a free Groq API key
   (see [docs/GROQ_SETUP.md](docs/GROQ_SETUP.md)). The key is hidden and is not saved.
3. Work through Part A and Part B, then answer the evidence-check questions.
4. Save your notebook (`File -> Download -> Download .ipynb`, or save a copy to Drive) and submit
   as your instructor directs.

You do not need to install Python, clone this repository, or own a GPU. The notebook writes its
own data and defines everything it needs.

**Instructors:** see [docs/INSTRUCTOR_GUIDE.md](docs/INSTRUCTOR_GUIDE.md) for the teaching
sequence, the slide decks, assessment rubrics, and how to point the labs at a different model
endpoint.

---

## 7. Lab index

All ten labs sit at the top level of this repository, numbered in teaching order: `lab01` to `lab05`
teach the agentic AI patterns, and `lab06` to `lab10` apply language models to forensic tasks. Every lab
folder has its own `README.md`, a slide deck (PDF and PowerPoint), and an **Open in Colab** notebook.

### Labs 01-05: agentic AI patterns

| Lab | Folder | Pattern | Case | Materials |
|---|---|---|---|---|
| 01 | [lab01_reflection_pattern](lab01_reflection_pattern/) | Reflection | Suspected customer-data exfiltration (DF-2026-017) | Notebook, data, [slides](lab01_reflection_pattern/slides/) |
| 02 | [lab02_tool_use_pattern](lab02_tool_use_pattern/) | Tool Use | Stolen-vehicle sale preparation (TU-2026-004) | Notebook, data, [slides](lab02_tool_use_pattern/slides/) |
| 03 | [lab03_react_pattern](lab03_react_pattern/) | ReAct | Signal attempt during an unattended interval (RA-2026-009) | Notebook, data, [slides](lab03_react_pattern/slides/) |
| 04 | [lab04_planning_pattern](lab04_planning_pattern/) | Planning | Missing-phone timeline reconstruction (PL-2026-011) | Notebook, data, [slides](lab04_planning_pattern/slides/) |
| 05 | [lab05_multiagent_pattern](lab05_multiagent_pattern/) | Multiagent | Transmission and chain-of-custody review (MA-2026-022) | Notebook, data, [slides](lab05_multiagent_pattern/slides/) |

### Labs 06-10: LLMs for forensics

Standalone labs that put language models to work on forensic evidence. Each has its own deck, Colab
notebooks, and (for the chatbots) a Gradio chat UI.

<table>
  <tr>
    <td align="center" width="33%"><a href="lab06_llm_rag_case_reports/"><img src="lab06_llm_rag_case_reports/slides/img/cover.png" alt="Lab 06: RAG over DF case reports" width="100%"></a><br><sub><b>Lab 06</b> · RAG over case reports</sub></td>
    <td align="center" width="33%"><a href="lab07_llm_android_image_agent/"><img src="lab07_llm_android_image_agent/slides/img/cover.png" alt="Lab 07: agent over an Android image" width="100%"></a><br><sub><b>Lab 07</b> · Agent over an Android image</sub></td>
    <td align="center" width="33%"><a href="lab08_llm_bug_report_chatbot/"><img src="lab08_llm_bug_report_chatbot/slides/img/cover.png" alt="Lab 08: bug report chatbot" width="100%"></a><br><sub><b>Lab 08</b> · Bug report chatbot</sub></td>
  </tr>
  <tr>
    <td align="center"><a href="lab09_llm_incident_response_copilot/"><img src="lab09_llm_incident_response_copilot/slides/img/cover.png" alt="Lab 09: incident response copilot" width="100%"></a><br><sub><b>Lab 09</b> · Incident-response copilot</sub></td>
    <td align="center"><a href="lab10_llm_memory_forensics_volatility/"><img src="lab10_llm_memory_forensics_volatility/slides/img/cover.png" alt="Lab 10: memory forensics with Volatility 3" width="100%"></a><br><sub><b>Lab 10</b> · Memory forensics (Volatility 3)</sub></td>
    <td align="center" valign="middle"><sub>Practicals 1 and 2 (machine learning) live in their own repositories:<br><a href="https://github.com/danjethh/steg_analysis">steganalysis</a> and <a href="https://github.com/danjethh/audio_forensics">audio forensics</a>.</sub></td>
  </tr>
</table>

| Lab | Folder | Technique | What it teaches |
|---|---|---|---|
| 06 | [lab06_llm_rag_case_reports](lab06_llm_rag_case_reports/) | Retrieval-Augmented Generation | Build a RAG from scratch so a model answers questions about case reports, grounded in them and cited. |
| 07 | [lab07_llm_android_image_agent](lab07_llm_android_image_agent/) | Tool-using agent (ReAct) | An agent that lets a lightweight Qwen model walk an Android device image, answer a question, and cite the exact file it used. Includes chatbot versions. |
| 08 | [lab08_llm_bug_report_chatbot](lab08_llm_bug_report_chatbot/) | Tool-using agent (chatbot) | The same agent over an Android bug report students can pull from their own phone. |
| 09 | [lab09_llm_incident_response_copilot](lab09_llm_incident_response_copilot/) | Agent + plan, playbook, and ISMS grounding | An incident-response copilot that works from the company's IR plan, playbooks, and ISO 27001 ISMS, with approval-gated, simulated actions. |
| 10 | [lab10_llm_memory_forensics_volatility](lab10_llm_memory_forensics_volatility/) | Tool-using agent over Volatility 3 | A memory-forensics analyst whose toolset is Volatility's plugin list, working a real public memory image with a ground-truth answer key. |

---

## 8. Discussion

**Why Reflection comes first.** Self-review is the smallest agentic loop and the habit every
later pattern depends on. A student who can make a model critique and revise its own forensic
claim is ready to understand tool use, planning, and multi-agent review.

**What students actually learn.** The technical skill is wiring an LLM into a loop. The deeper
skill, the one that transfers to real casework, is the discipline of evidence-bounded writing:
saying "the artifacts show" instead of "the suspect did," and naming the boundary of what the
evidence can support.

**The role of the human.** None of these patterns make the model the examiner. They make the
model a faster, more honest assistant that removes obvious overreach before a qualified human
reads the report and owns the final judgment.

---

## 9. Limitations and ethics

- **Teaching-scale data.** The synthetic cases teach reasoning; they do not mirror the full complexity
  of a real acquisition. The real memory sample is a 2012 Windows XP image: small and well documented,
  but older than current systems (for example, Volatility 3's network plugin does not support XP).
- **Models change.** Hosted model availability and behavior shift over time. The notebooks
  default to a current model and recover gracefully if a model name is retired.
- **Not legal advice.** These labs teach method, not courtroom procedure. Real investigations are
  governed by law, policy, and qualified human examiners.
- **Responsible use.** The exfiltration and surveillance scenarios are teaching devices. They are
  framed from the examiner's side and must not be used to build or conceal real misconduct.

---

## 10. Credits and provenance

This course is adapted from **frankwxu/agentic-AI4-forensics**
(https://github.com/frankwxu/agentic-AI4-forensics), which provides the original course concept,
the forensic case design, and the lab sequence. We gratefully acknowledge that work.

The agent workflow code is adapted from **The Neural Maze's agentic-patterns-course**
(https://github.com/neural-maze/agentic-patterns-course) and is reused under the MIT License. The
original copyright and permission notice are preserved in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

The SectraTEK adaptation (hosted zero-install runtime, self-contained notebooks, the slide decks,
and this documentation) is by Daniel Kwaku Ntiamoah Addai, SectraTEK Lab. The LLM-for-forensics labs
(`lab06` to `lab10`) are original SectraTEK Lab work.

The memory-forensics lab uses [Volatility 3](https://github.com/volatilityfoundation/volatility3)
(Volatility Foundation, Volatility Software License), installed from PyPI at run time, and the public
Cridex memory sample listed on the Volatility Foundation's memory-samples page, downloaded at run time.
Neither is redistributed in this repository.

---

## 11. License

The adapted course materials in this repository are provided for educational use. Third-party
code retains its original license as recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
For any other use, contact SectraTEK Lab.

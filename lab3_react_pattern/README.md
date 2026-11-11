# Lab 3: The ReAct Pattern for Step-by-Step Verification

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danjethh/sectratek-AI-Lab/blob/main/lab3_react_pattern/03_lab_notebook.ipynb)

> Make the model show its work. It states a thought, calls one tool, reads the result, and only then
> decides the next step, so the whole chain of reasoning is visible and checkable.

**Course:** AI for Cybersecurity and Digital Forensics - [SectraTEK AI Lab](../README.md)
**Pattern:** ReAct (Thought -> Action -> Observation, repeated, then Response)
**Case:** Signal image-sending attempt during an unattended interval, `RA-2026-009`
**Runtime:** Google Colab or any hosted Jupyter, free Groq endpoint, no local install

---

## Abstract

This lab introduces the **ReAct Pattern**, a loop in which a model reasons out loud, takes one action,
observes the result, and repeats until it can answer. Where Lab 2 let a model call tools, ReAct adds
the missing half: a visible **Thought** before every **Action**, and an **Observation** that drives
the next thought. The student answers a narrow timing question about a phone left unattended: was there
an attempt to send an image through Signal during the interval, and what does the network evidence say
about delivery? The case is designed so that the obvious shortcut, "there was a Signal event, so the
image was sent," is wrong. By forcing one evidence check per turn, each driven by the last observation,
ReAct keeps the student from leaping past the gap between an **attempt** and a **delivery**. The student
walks the loop by hand (Part A), then runs the same case through a packaged `ReactAgent` (Part B).

---

## Table of contents

1. [Background](#1-background)
2. [Problem statement](#2-problem-statement)
3. [Gaps this lab addresses](#3-gaps-this-lab-addresses)
4. [The solution: the ReAct Pattern](#4-the-solution-the-react-pattern)
5. [Methods and approach](#5-methods-and-approach)
6. [The case: RA-2026-009](#6-the-case-ra-2026-009)
7. [Practical: running the lab](#7-practical-running-the-lab)
8. [Worked trace](#8-worked-trace)
9. [Discussion](#9-discussion)
10. [Learning outcomes and assessment](#10-learning-outcomes-and-assessment)
11. [Files in this lab](#11-files-in-this-lab)
12. [Credits](#12-credits)

---

## 1. Background

A timing question in forensics is answered by lining up facts in order: fix the window, place the
event, add the context, and only then conclude. An experienced examiner never leaps from a single log
entry to a verdict. They check one thing, see what it implies, and let that decide the next check.

Large language models do not do this by default. Given tools, a model may fire several calls at once,
or skip the reasoning entirely and state a confident conclusion. The **ReAct Pattern** (short for
Reason plus Act) imposes the examiner's discipline: before each tool call the model must write a
**Thought** saying what it needs and why, then take exactly one **Action**, then read the
**Observation** before thinking again. The reasoning becomes a trail a human can audit.

---

## 2. Problem statement

> **How do we get an AI to answer a narrow timing question without skipping the steps that keep the
> answer honest?**

The case is built around a trap. A Signal image-attachment attempt is logged at `14:16 UTC`, inside a
reported unattended interval of `14:10` to `14:25`. It is tempting to conclude the image was sent. But
mobile data was offline during the interval and only returned at `14:28`, after it ended. An attempt
can be logged with no connection. The right answer distinguishes a recorded **attempt** from a
confirmed **delivery**, and that distinction only survives if each fact is checked in turn.

---

## 3. Gaps this lab addresses

| Gap | Without ReAct | With ReAct |
|---|---|---|
| **Leaping to a verdict** | "A Signal event means the image was sent." | Each check is made and read before the next is chosen. |
| **Hidden reasoning** | A one-shot answer you cannot audit. | Every Thought, Action, and Observation is on the page. |
| **Attempt vs delivery** | The two claims are blurred. | The offline window is checked, so delivery stays unconfirmed. |
| **Uncontrolled tool use** | The model fires calls without a rationale. | One tool per turn, each justified by a thought. |

---

## 4. The solution: the ReAct Pattern

```
            +----------------- repeat until the evidence is enough -----------------+
            v                                                                        |
 Question -> [ Thought ] -> [ Action: one tool ] -> [ Observation ] -----------------+ -> Response
             (why I need      (call it)              (read the result,
              the next fact)                          shape the next thought)
```

Each turn is visible. The loop repeats until the model writes a final `<response>`. What lets each turn
build on the last is a simple **short-term memory**: a running `chat_history` list holding the
question, every thought, every tool call, and every observation, in order. Nothing is stored outside
that list, so the history is also the complete audit trail.

---

## 5. Methods and approach

The notebook is in two parts, by design.

- **Part A: walk the loop by hand.** You define three narrow tools, then run the loop one turn at a
  time with a `run_single_react_turn` helper. You watch the model's Thought, the one tool it calls, and
  the Observation it reads back, three turns, then a final four-part answer. The guided walkthrough
  fixes the tool order so each turn is easy to inspect.
- **Part B: hand the case to `ReactAgent`.** The packaged agent runs the same loop automatically over
  the same tools and question. Your job shifts to judging it: did it gather the same observations in a
  sensible order, and did it stay evidence-bounded?

**The three tools.**

| Tool | Arguments | What it returns |
|---|---|---|
| `get_incident_window` | none | The start and end of the unattended interval. |
| `get_message_attempt` | `app` | The Signal image-attachment attempt and its timestamp. |
| `get_network_restore_time` | none | When mobile data came back online. |

Each tool answers one question, so the loop must reason its way from one to the next.

**Runtime.** The notebook connects to a free, OpenAI-compatible endpoint (Groq by default, model
`llama-3.3-70b-versatile`). The key is entered with a hidden prompt and never saved. The notebook writes
the five case artifacts to a local `data/` folder itself, so it runs standalone in Colab with no clone
and no install. See [../docs/GROQ_SETUP.md](../docs/GROQ_SETUP.md).

---

## 6. The case: RA-2026-009

- **Device:** Samsung Galaxy A54, Android 14
- **Acquisition:** Cellebrite UFED, full file system; image hash recorded in the manifest
- **Scenario:** an outreach worker's phone was left unattended on a supply table for a short interval
- **The question:** during that interval, did the phone try to send an image through Signal, and what
  does the network evidence allow us to say about delivery?

### Observed event sequence (UTC)

| Time | What the records show |
|---|---|
| 14:10:00 | unattended interval starts (staff observation) |
| 14:15:58 | mobile data drops offline |
| 14:16:11 | Signal image-attachment attempt recorded |
| 14:25:00 | unattended interval ends |
| 14:28:02 | mobile data restored (after the interval) |

### The artifacts (`data/`)

| File | Contents |
|---|---|
| `artifact_manifest.json` | Case, device, and integrity metadata |
| `incident_window.csv` | Staff-observed start and end of the unattended interval |
| `messaging_events.csv` | The Signal image-attachment attempt and its time |
| `network_events.csv` | When mobile data went offline and was restored |
| `chain_of_custody.csv` | Acquisition and hash-verification log |

---

## 7. Practical: running the lab

1. Click the **Open in Colab** badge at the top of this page.
2. Run **Part 0** (setup): install the client, connect to Groq (paste a free key), write the case files,
   and load the ReAct framework.
3. Run **Part A**: walk the loop one turn at a time and read each Thought, Action, and Observation.
4. Run **Part B**: hand the case to `ReactAgent` and judge its run.
5. Write your own four-part, evidence-bounded answer.
6. Save and submit the notebook.

No local install is required. If the default model name is ever retired, the setup cell prints the
models available on your key.

---

## 8. Worked trace

| Turn | Thought | Action | Observation | Why it matters |
|---|---|---|---|---|
| 1 | I need the time window first. | `get_incident_window` | 14:10 to 14:25 UTC | Later events now have something to be compared against. |
| 2 | Is the Signal attempt inside it? | `get_message_attempt("Signal")` | attempt at 14:16 UTC | Inside the window, but data was offline at the time. |
| 3 | Did connectivity ever return? | `get_network_restore_time` | restored 14:28 UTC | After the window. An attempt, not a confirmed delivery. |

**Draft v1:** "There was a Signal event, so the image was sent during the unattended interval."

**Final v2:** "The artifacts show an attempt to send an image through Signal at 14:16:11 UTC, which is
inside the unattended interval (14:10 to 14:25). Mobile data was offline during the interval and was
restored at 14:28:02 UTC, after it ended, so the evidence supports an in-window attempt but does not
confirm successful delivery."

Each thought follows from the previous observation, and the final answer stops where the evidence does.

---

## 9. Discussion

**Reasoning you can audit.** ReAct's real product is not just the answer; it is the trail. A reviewer
can read the thoughts and observations in order and spot a wrong turn before it becomes a wrong verdict.

**ReAct versus Planning.** ReAct decides the next step only after seeing the last observation. Lab 4's
Planning Pattern writes a fuller plan up front and revises it. ReAct suits bounded questions where each
step depends on the one before; planning suits larger problems that benefit from decomposition.

**Attempt is not delivery.** The hardest habit here is stopping at what the records support. The phone
was offline during the attempt and reconnected only after the interval, so delivery stays unconfirmed.
Holding that line is the examiner's judgment, and ReAct makes it easy to defend.

---

## 10. Learning outcomes and assessment

By the end of this lab a student can:

1. Explain the roles of reason, action, observation, and response in a ReAct loop.
2. Choose the next tool call that reduces the most important remaining uncertainty.
3. Use one tool result to justify the next step in a bounded workflow.
4. Produce a final answer that cites observed evidence and states what remains unconfirmed.
5. Distinguish a ReAct loop from a planning workflow that uses broader decomposition and replanning.

**Required answer (both parts):** a ReAct step log; the unattended-interval evidence; the Signal timing
evidence with an inside-or-outside judgment; and a connectivity-aware conclusion that does not claim
confirmed delivery. Instructor guidance is in [../docs/INSTRUCTOR_GUIDE.md](../docs/INSTRUCTOR_GUIDE.md).

---

## 11. Files in this lab

| Path | What it is |
|---|---|
| `03_lab_notebook.ipynb` | The hosted (Colab/Groq) student notebook |
| `data/` | The five synthetic case artifacts |
| `slides/SectraTEK_Lab3_ReAct.pptx` | The lecture deck for this lab |
| `README.md` | This document |

---

## 12. Credits

The case design and lab concept are adapted from **frankwxu/agentic-AI4-forensics**
(https://github.com/frankwxu/agentic-AI4-forensics). The ReAct framework (`@tool`, `extract_tag_content`,
`ReactAgent`) is adapted from **The Neural Maze's agentic-patterns-course**
(https://github.com/neural-maze/agentic-patterns-course), MIT License; see
[../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). The hosted adaptation, notebook, slides, and
documentation are by Daniel Kwaku Ntiamoah Addai, SectraTEK Lab.

# Instructor Guide

Teaching notes for delivering the SectraTEK AI Lab course. This guide covers the lecture-to-lab
flow, timing, assessment, and how to adapt the labs to your environment.

---

## 1. Background and intent

Each lab pairs a short theory lecture with a hands-on notebook. The through-line of the course is
not "how to call an LLM," it is **evidence-bounded reasoning**: the habit of separating observation
from inference and citing an artifact for every claim. The agentic patterns are the vehicle; the
discipline is the destination. Keep returning students to the question "which artifact and timestamp
supports that sentence?"

---

## 2. Audience

The labs assume students who are learning cybersecurity or digital forensics and who may be new to
programming. The notebooks are written so a student can follow and run them after a theory lecture
without writing code from scratch. Where a student has no programming background, the pre-lab group
activity and the *Purpose / Input / Output* notes carry them through.

---

## 3. Teaching sequence per lab

**Labs 01-05 (agentic patterns).** Recommended 90-minute block:

| Phase | Time | What happens |
|---|---|---|
| Theory lecture | 25 min | Present the pattern and the case using the lab's slide deck. |
| Pre-lab group activity | 35 min | Students analyze the raw artifacts and record a human baseline (optional but valuable). |
| Notebook, Part A | 15 min | Build the loop by hand; discuss the draft and the critique. |
| Notebook, Part B | 10 min | Run the packaged agent; compare to Part A. |
| Evidence check and debrief | 5 min | Students answer the four questions; close on what stays with a human. |

If time is short, drop the pre-lab activity and run the notebook directly after the lecture. The
notebook is self-contained.

**Labs 06-10 (LLMs for forensics).** These have no Part A/Part B split; each is one notebook (Labs 07-10
also have a chat-UI version). A 90-minute block works as: deck (20 min), notebook walk-through (30 min),
students' own questions in the chat (25 min), then checking the AI against the evidence (15 min):

| Lab | What students check the AI against | Setup note |
|---|---|---|
| 06 RAG | The report passages it retrieved and cited | Downloads a small embedding model (~90 MB) once |
| 07 Android image | The file it cites in the synthetic image | Writes the synthetic image itself |
| 08 Bug report | The section it cites in the report | Bundled sample; a student's own report holds personal data |
| 09 IR copilot | The playbook section behind every step; the action log | Drill only: notifications and containment are simulated |
| 10 Memory | `answer_key.md` (verified ground truth) | Downloads the ~40 MB Cridex sample and pip-installs Volatility 3 |

In every LLM lab, point students at the `evidence_check` lines in the trace: they show the harness
sending back an answer that no tool output supports.

---

## 4. Slides

Each lab has a lecture deck under its `slides/` folder (for Lab 01,
`lab01_reflection_pattern/slides/SectraTEK_Lab01_Reflection.pptx`). The decks follow a single story
arc: background, how the work was done before AI, the problem, the discipline, the gap, the pattern,
the case, and the practical. They are designed for students who are new to the material.

---

## 5. Model runtime

The labs default to the Groq free tier. Before class, confirm students can reach
`https://console.groq.com/keys` on your network and create a key. If your institution blocks it,
retarget the labs to a permitted endpoint using the two-value change in
[GROQ_SETUP.md](GROQ_SETUP.md). If a default model is retired, the notebooks
move to the next model on their preference list on their own (`PREFERRED` in the Labs 01-07 setup cell,
`GROQ_MODELS` in `agentkit.py` for Labs 08-10) and print which one they chose.

---

## 6. Assessment (Lab 01 example; Labs 02-05 follow the same shape)

Score the model draft, the revised report, and the student's evidence-check answers with a shared
0 to 4 rubric across four dimensions:

- claim-to-evidence links,
- reasoning validity,
- timeline accuracy,
- uncertainty handling.

Suggested target attainment for a cohort:

- at least 80% of final-report claims map to explicit artifact evidence;
- zero major unsupported conclusions in final reports;
- at least 85% of timeline events correctly ordered and timestamped;
- average draft-to-revision improvement of at least 20% on the rubric.

Where staffing allows, double-score a sample, reconcile with a shared guide, and record both
target-attainment rates and average improvement.

---

## 7. Common student pitfalls

| Pitfall | Correction |
|---|---|
| Treating the model's draft as the answer | Reinforce that the draft is the thing to be criticized, not trusted. |
| Reading "copied to Telegram" as "delivered" | Walk the observation/inference/claim distinction on that exact event. |
| Accepting `[[OK]]` as "the conclusion is true" | `[[OK]]` means internally disciplined, not factually verified. |
| Pasting the API key into a code cell | Only use the hidden `getpass` prompt; never commit a key. |

---

## 8. Adapting and extending

- **Different case:** the Labs 01-05 notebooks read their artifacts from a `data/` folder they write
  themselves. To use your own synthetic case, replace those artifacts and update the case overview.
  Labs 06-10 read `reports/`, `android_image/`, a bug report, `knowledge/` + `evidence/`, or a memory
  image: replace those (each lab's README says how).
- **Different model:** change `BASE_URL` and the `PREFERRED` list in the setup cell (Labs 01-07), or
  pass `model=` to `connect_model` (Labs 08-10).
- **Offline room:** point the labs at a local Ollama endpoint (see GROQ_SETUP.md); this is the only
  configuration that requires a local install.

---

## 9. Credits

See the repository [README](../README.md) and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)
for provenance and licensing. The course is adapted from frankwxu/agentic-AI4-forensics, with agent
code from The Neural Maze's agentic-patterns-course (MIT).

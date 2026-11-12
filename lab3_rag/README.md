# Practical 3: Building a RAG over Digital-Forensics Reports

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danjethh/sectratek-AI-Lab/blob/main/lab3_rag/03_lab_notebook.ipynb)

> Ask plain-English questions over a pile of case reports and get an answer that is grounded in the
> reports and cites them, instead of a confident guess from the model's memory.

**Course:** AI for Cybersecurity and Digital Forensics
**Technique:** Retrieval-Augmented Generation (RAG), built from scratch
**Runtime:** Google Colab or any hosted Jupyter, free Groq endpoint, no local install

---

## Abstract

This practical teaches **Retrieval-Augmented Generation (RAG)**: a way to make a language model answer
from *your* documents rather than from its training memory. The student builds a small RAG system by
hand over six synthetic digital-forensics case reports, in four visible steps: chunk the reports into
passages, embed each passage as a vector that captures its meaning, retrieve the passages closest to a
question, and generate an answer from only those passages, with citations. A side-by-side comparison
shows the point: asked about a private case, a plain model invents a fluent, specific, wrong answer;
the RAG pipeline answers from the real report and names its source. The pipeline uses
`sentence-transformers` for embeddings and NumPy for retrieval, so every step is plain and inspectable,
with a hosted model (Groq) only for the final writing step. The discipline is the same one that runs
through this course: say only what the evidence supports.

---

## Table of contents

1. [Background](#1-background)
2. [Problem statement](#2-problem-statement)
3. [Gaps this lab addresses](#3-gaps-this-lab-addresses)
4. [The solution: Retrieval-Augmented Generation](#4-the-solution-retrieval-augmented-generation)
5. [Methods and approach](#5-methods-and-approach)
6. [The corpus](#6-the-corpus)
7. [Practical: running the lab](#7-practical-running-the-lab)
8. [Worked example](#8-worked-example)
9. [Discussion](#9-discussion)
10. [Learning outcomes and assessment](#10-learning-outcomes-and-assessment)
11. [Files in this lab](#11-files-in-this-lab)
12. [Credits](#12-credits)

---

## 1. Background

An examiner builds up many case reports over time, and the most useful questions cut across all of
them: *which cases involved ransomware?*, *what network indicators appear across the reports?* The
answers are buried in prose, and finding them means remembering which case, then re-reading it.

The obvious tools fall short. **Keyword search** matches letters, not meaning: a report about credential
theft may never contain the word "credentials" (it says "LSASS dump" or "Mimikatz"), so search misses
it. And asking a **chatbot directly** is worse: the model was trained on the public web, not your case
files, so when asked about a case it cannot know, it does not say so, it invents a plausible answer.

---

## 2. Problem statement

> **How do we let a language model answer questions about our own forensic reports, accurately and with
> sources, instead of guessing?**

The difficulty is grounding. A general-purpose model has broad knowledge but no access to your evidence.
A bigger model does not fix that. What fixes it is finding the few report passages that actually bear on
the question and handing the model only those, with an instruction to answer from them and cite them.

---

## 3. Gaps this lab addresses

| Gap | Without RAG | With RAG |
|---|---|---|
| **Search by letters** | Keyword search misses synonyms and paraphrases. | Retrieval matches by meaning, through embeddings. |
| **Hallucinated specifics** | A plain model invents case details it cannot know. | The model answers only from retrieved passages. |
| **No sources** | You cannot check where an answer came from. | Every claim cites the report it came from. |
| **Opaque frameworks** | A library hides the retrieval loop. | The student builds chunk/embed/retrieve by hand. |

---

## 4. The solution: Retrieval-Augmented Generation

```
 Question --> [ Retrieve the closest passages ] <-- your reports
                          |
                          v
              [ Generate an answer from ONLY those passages, with citations ]
```

RAG has two moves. **Retrieve:** find the report passages most related to the question. **Generate:**
give the model only those passages and ask it to answer from them and cite them. The model never
answers from memory, and every claim points back to a report you can open and check.

---

## 5. Methods and approach

The notebook builds the pipeline in four visible steps, then compares it against the plain model.

| Step | What it does |
|---|---|
| **Chunk** | Cut each report into short passages, each tagged with its source file (for citations). |
| **Embed** | Turn each passage into a vector with `all-MiniLM-L6-v2` (a small, free model that runs in the session). Similar meaning gives similar numbers. |
| **Retrieve** | Embed the question, then score passages by **cosine similarity** (a 0-to-1 closeness score); take the top few. |
| **Generate** | Build a prompt from the retrieved passages and ask the model to answer only from them, cite the report, and say "not covered" when the answer is absent. |

**Why embeddings.** An embedding turns text into numbers so that "the attacker dumped credentials from
LSASS" and "passwords were stolen from memory" sit close together even though they share no keyword.
That closeness is what retrieval uses, and it is the semantic win over keyword search.

**Runtime.** Embedding and retrieval run locally in the notebook (no key needed). Only the final
answer-writing step calls a hosted model (Groq free tier, `llama-3.3-70b-versatile`), with the key
entered via a hidden prompt and never saved. The notebook writes the six reports itself, so it runs
standalone in Colab with no clone and no install beyond a one-time `pip`.

---

## 6. The corpus

Six synthetic, fictional case reports (in `reports/`), chosen to span distinct forensic topics so
cross-case questions are meaningful:

| Report | Topic |
|---|---|
| `DF-2026-017_mobile_exfiltration.md` | Android customer-data exfiltration (Telegram/Gmail) |
| `DF-2026-021_windows_ransomware.md` | Windows ransomware, macro loader, shadow-copy deletion |
| `DF-2026-025_memory_credential_theft.md` | Memory forensics, Mimikatz-style LSASS credential dump |
| `DF-2026-030_ios_stalkerware.md` | iOS stalkerware, rogue profile, beaconing |
| `DF-2026-034_disk_deleted_recovery.md` | Disk image, file carving, anti-forensic wiping |
| `DF-2026-039_network_intrusion.md` | Phishing, lateral movement, DNS-tunnelling C2 |

All indicators (hashes, domains, addresses) are fabricated for teaching.

---

## 7. Practical: running the lab

1. Click the **Open in Colab** badge at the top of this page.
2. Run **Part 0** (setup): install `sentence-transformers`, `numpy`, `openai`; connect to Groq (paste a
   free key); save the six reports.
3. Run **Part A**: chunk the reports, embed them, retrieve for an example question, and generate a cited
   answer.
4. Run **Part B**: ask the same question with and without retrieval, and compare.
5. Run **Part C**: ask your own cross-case questions.
6. Fill in the short write-up and save the notebook.

No local install is required. The first `pip` takes about a minute (it downloads the embedding library),
and the embedding model (~90 MB) downloads once on first use.

---

## 8. Worked example

**Model alone (no reports):**

> "Case DF-2026-025 involved a phishing email that deployed Emotet, exfiltrating 2.4 GB over Tor." -
> fluent, specific, and entirely invented. No source to check.

**With RAG (retrieved + cited):**

> "DF-2026-025 used a Mimikatz-like tool to dump credentials from LSASS, kept alive by a scheduled task
> `[DF-2026-025_memory_credential_theft.md]`." - grounded in the real report, with a citation you can
> open.

Same question, very different trust.

---

## 9. Discussion

**Grounding, not a bigger model.** The value of RAG is not a smarter model; it is that the answer is
built from passages you can inspect, and every claim cites its source.

**Retrieval quality is the ceiling.** If retrieval fetches the wrong passages, the answer will be wrong
no matter how good the model is. That is why the lab makes you read the retrieved passages and their
scores, not just the final answer.

**The same discipline.** As in the rest of the course, the honest answer sometimes is "that is not
covered in the reports." A grounded system that admits what it does not know is more trustworthy than a
fluent one that never does.

---

## 10. Learning outcomes and assessment

By the end of this lab a student can:

1. Explain the four RAG steps (chunk, embed, retrieve, generate) and what each contributes.
2. Describe an embedding as "meaning as numbers" and why it beats keyword search.
3. Read retrieved passages and their similarity scores, and judge whether they support an answer.
4. Recognise and prefer a cited, grounded answer over a confident but unsourced one.

**Write-up:** one grounded answer with its citation checked against the source; one out-of-scope question
and whether the system admitted it; and one sentence on why retrieval makes answers more trustworthy.

---

## 11. Files in this lab

| Path | What it is |
|---|---|
| `03_lab_notebook.ipynb` | The hosted (Colab/Groq) student notebook |
| `reports/` | The six synthetic case reports (the knowledge base) |
| `slides/SectraTEK_Practical3_RAG.pptx` | The lecture deck for this lab |
| `README.md` | This document |

---

## 12. Credits

The case reports and lab design are original, written for this course by Daniel Kwaku Ntiamoah Addai,
SectraTEK Lab. Embeddings use the open **sentence-transformers** library
(https://www.sbert.net/) with the `all-MiniLM-L6-v2` model. The final answer-writing step uses a hosted,
OpenAI-compatible model (Groq free tier).

# DF-LLM-Labs: Lightweight LLMs for Digital Forensics

> Hands-on labs that put large language models to work on digital-forensic tasks, carefully. Every lab
> runs in a hosted notebook (Google Colab) with a free model endpoint, so students install nothing on
> their own machines.

**Course:** AI for Cybersecurity and Digital Forensics
**Author and instructor:** Daniel Kwaku Ntiamoah Addai, Mobile Threat Research Lead, SectraTEK Lab

---

## About

These practicals continue the course after the machine-learning labs (steganalysis and audio forensics)
and move to **language models**. The theme throughout is the same discipline the whole course teaches:
an AI is an assistant to the examiner, and its answers must stay inside, and point back to, the evidence.

Each lab is a self-contained folder: open the notebook from its **Open in Colab** badge, paste a free
model key when asked, and follow it step by step. Nothing is installed locally.

## Labs

| # | Lab | What it teaches |
|---|---|---|
| 3 | [RAG over DF reports](lab3_rag/) | Build a Retrieval-Augmented Generation system from scratch so a model answers questions about your case reports, grounded in them and with citations. |
| 4 | [Forensic agent over an Android image](lab4_qwen/) | Build a small agent that lets a lightweight Qwen model walk a whole device image, answer an investigation question, and cite the exact file its answer came from. Includes a local-Ollama version and an interactive chatbot (UI + in-notebook). |
| + | [Ask the Bug Report](bug_report_agent/) | The same agent as a chatbot over an Android **bug report** (`adb bugreport`), which students can generate from their own phone. UI and in-notebook versions. |

Lab numbering continues the course: Practical 1 (steganalysis) and Practical 2 (audio forensics) live
in their own repositories; Practicals 3 and 4 are here.

## How to run (students)

1. Open the lab folder you want (start with [lab3_rag](lab3_rag/)) and click the **Open in Colab** badge
   in its notebook.
2. Run the setup cells. When prompted, paste a free API key (the lab tells you where to get one). The key
   is hidden and is not saved into the notebook.
3. Work through the lab top to bottom and complete the short write-up.

You do not need to install Python, clone this repository, or own a GPU.

## Note on the data

Every case, report, and indicator in these labs is **synthetic**, written for teaching. No real personal
data is used anywhere in this repository.

<p align="center">
  <a href="slides/SectraTEK_Lab10_MemoryForensics.pdf"><img src="slides/img/cover.png" alt="Ask the Memory - lecture deck cover" width="880"></a>
</p>

# Lab 10: Ask the Memory, a memory-forensics agent over Volatility 3

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danjethh/sectratek-AI-Lab/blob/main/lab10_llm_memory_forensics_volatility/memory_agent_jupyter.ipynb)

> Ask a plain-English question about a memory image. An AI analyst picks the right Volatility plugin,
> runs it, reads the output, and answers, citing the plugin and the process ID behind every claim.

**Course:** AI for Cybersecurity and Digital Forensics (memory forensics)
**Technique:** A tool-using agent (ReAct) whose toolset is Volatility 3's plugin list
**Case:** Suspected compromise of a Windows XP workstation, `MF-2026-001` (real public memory image)
**Runtime:** Google Colab or any hosted Jupyter, Volatility 3, free Groq model, no local install
**Slides:** [lecture deck (PDF)](slides/SectraTEK_Lab10_MemoryForensics.pdf) : [PowerPoint](slides/SectraTEK_Lab10_MemoryForensics.pptx)

---

## Abstract

Memory forensics recovers what a computer was doing at the moment its RAM was captured: running
processes, code injected into them, and the addresses they were talking to, much of which never touches
the disk. The standard tool is **Volatility**, which answers each question with a different plugin. That
works, but it assumes the examiner already knows which of hundreds of plugins to run, and how to read
thousands of rows of output. This lab gives that plugin list to a language model **as its toolset**. The
analyst asks a question; the model picks one plugin and its arguments; the lab's code runs Volatility on
the image; the model reads the result, runs another plugin or answers, and cites the plugin and PID it
relied on. The case uses the public **Cridex** memory image, a real Windows XP banking-trojan infection with
published ground truth, so students can check every claim the AI makes against a known answer.

---

## Table of contents

1. [Background](#1-background)
2. [Problem statement](#2-problem-statement)
3. [The idea: the plugin list is the toolset](#3-the-idea-the-plugin-list-is-the-toolset)
4. [Methods: the toolset and its guardrails](#4-methods-the-toolset-and-its-guardrails)
5. [The case and the memory image](#5-the-case-and-the-memory-image)
6. [Practical: running the lab](#6-practical-running-the-lab)
7. [Worked example](#7-worked-example)
8. [Checking the AI against the ground truth](#8-checking-the-ai-against-the-ground-truth)
9. [Discussion and limits](#9-discussion-and-limits)
10. [Files in this lab](#10-files-in-this-lab)
11. [Credits and data sources](#11-credits-and-data-sources)

---

## 1. Background

A disk image shows what was stored. A memory image shows what was **running**: every process and who
started it, the DLLs each one loaded, code that malware injected into a legitimate process, open handles,
and network addresses held in memory. Much of this exists only in RAM and is lost when the machine powers
off, which is why responders capture memory first.

Volatility is the standard open-source framework for reading a memory image. An examiner runs one plugin
per question (`windows.pstree` for the process tree, `windows.malfind` for injected code, and so on), reads
the table it prints, and cross-checks with a second plugin before concluding.

## 2. Problem statement

Even a small 512 MB image of one old workstation produces a lot to read: 17 processes, 738 loaded DLLs,
1,174 file objects, and 4,451 open handles. Knowing which plugin answers which question takes training.
The tempting shortcut, asking a chatbot what is in the memory, is worse: it answers fluently and
specifically without ever running a plugin, so its diagnosis has nothing behind it.

## 3. The idea: the plugin list is the toolset

<p align="center">
  <img src="slides/img/plugin_toolset.png" alt="Volatility plugins become the agent's tools" width="860"><br>
  <sub><em>Volatility already lists everything an examiner can do. That list becomes the model's toolset: it chooses a plugin and its arguments, and the lab's code runs the real Volatility command.</em></sub>
</p>

The model never sees memory directly. It can only act by choosing a plugin from a fixed list; the lab's
code runs `vol -r json -f <image> <plugin>` and hands back the result. It loops (think, run one plugin,
read the output) until it can answer, and the answer names the plugin and PID it relied on.

<p align="center">
  <img src="slides/img/loop.png" alt="Pick a plugin, run Volatility, read the output, cite the answer" width="860"><br>
  <sub><em>One plugin per step, with the model's one-line reasoning shown each time, so the analyst (or a reviewer) can follow the trail.</em></sub>
</p>

## 4. Methods: the toolset and its guardrails

| Group | Tools (Volatility plugin behind each) |
|---|---|
| **Processes** | `info`, `pslist`, `pstree`, `psscan`, `psxview`, `cmdline` |
| **Code and modules** | `malfind`, `dlllist(pid)`, `ldrmodules(pid)` |
| **Objects** | `handles(pid)`, `mutantscan`, `filescan(keyword)`, `svcscan`, `hivelist`, `getsids`, `envars(pid)` |
| **Network** | `netscan` (Windows Vista and later), `search_memory` (`windows.vadregexscan`, any Windows) |
| **The case** | `case_brief`, `record_finding(finding, evidence)`, `findings_report` |

Guardrails, built into `memkit.py`:

- **Whitelist, read-only, no shell.** Only the plugins above can run; arguments are validated (a PID must be
  a number) and passed straight to Volatility, never through a shell.
- **Only plugins that work on this image.** Not every plugin supports every image. Before the agent
  starts, `check_plugins()` runs each whitelisted plugin once and keeps only the ones that return data. On
  the Cridex XP image 16 of 17 work; `netscan` is left out ("This version of Windows is not supported: 5.1"),
  and the agent is told to use `search_memory` for network indicators. A student's own Windows 10 image
  would keep `netscan`. A plugin that runs but finds nothing is also left out, and reported to the agent as
  a result ("nothing found"), so it never wastes a step on a plugin that cannot answer.
- **Run once, cached.** Each plugin runs once per image (the check above does this); later questions reuse
  the cached JSON, so answers are fast.
- **Filtered and capped.** Heavy plugins require a PID or keyword; every result is capped so the model is
  never flooded.
- **Cite or do not claim.** Every answer must name the plugin and PID. A `malfind` hit is a lead until a
  second plugin supports it.
- **Checked by the harness.** Limiting the tools to the image limits what the model can *look at*, not what
  it can *say*. In testing, a model answered "is anything unusual?" without running a plugin and invented a
  hidden "PID 4321 unknown.exe" loading "malicious.dll". So before an answer is accepted, the agent loop
  checks it: a plugin must have run for the question, and every PID, IP address, memory address, and file
  name in the answer must appear in output a plugin actually returned. Otherwise the answer is sent back
  (you see `evidence_check` in the trace); if the model still cannot back it, the answer arrives marked
  UNVERIFIED. The check cannot catch a wrong reading of real evidence, which is why the answer key exists.

## 5. The case and the memory image

The case brief (`case/case_brief.md`) describes a clerk whose Windows XP workstation slowed down and whose
banking session "behaved strangely" after they opened a PDF; IT captured RAM before isolating it.

The memory image is the public **Cridex** sample (`cridex.vmem`): a real infection captured in 2012 and
used for years to teach memory forensics.

| | |
|---|---|
| Download | about 40 MB (zip), 512 MB unpacked; fetched by the notebook |
| Integrity | SHA-256 of the zip and MD5 of the image (`7494f3b77db1525c1974f5380744ae46`) are both enforced: a mismatch stops the notebook |
| System | Windows XP SP3, 32-bit (PAE), captured 2012-07-22 02:45 UTC |
| Tested with | Volatility 3 2.28.2 (the notebooks pin this version, so the answer key stays valid) |

**Use your own image:** set `MEMORY_IMAGE` in the notebook to its path. On Windows Vista and later, the
`netscan` network plugin also works.

## 6. Practical: running the lab

1. Click **Open in Colab** at the top. The notebook installs Volatility 3, writes the lab code, and downloads
   and verifies the image. Nothing is installed on your own computer.
2. Run Volatility **by hand** first (`windows.info`, `windows.pstree`) to see the raw tool.
3. Run the plugin check: it tests every plugin on the image (about 90 seconds, once) and shows which ones
   the agent will get.
4. Paste a free Groq API key when asked (create one at console.groq.com), then ask Sectra the case questions
   with `talk("...")` and watch which plugin it chooses for each.
5. Print the findings report, then compare every claim with the answer key.

For a chat window instead, open `memory_agent_ui.ipynb` (Colab prints a public link). The first plugin run
downloads Windows symbol files (about a minute); after that, answers are quick.

## 7. Worked example

<p align="center">
  <img src="slides/img/worked.png" alt="Three plugins to a bounded finding" width="860"><br>
  <sub><em>pstree, malfind, and search_memory lead to one bounded, cited finding; malfind's hits in csrss.exe and winlogon.exe are recognised as benign.</em></sub>
</p>

Asked *"Is there evidence of injected code, and is this machine talking to anything?"*, the agent runs:

1. `pstree`: `reader_sl.exe` (PID 1640) was launched by `explorer.exe` (PID 1484), whose parent is gone.
2. `malfind`: a PE file (MZ header) in writable, executable memory in 1484 and 1640. The 12 hits in
   `csrss.exe` and `winlogon.exe` have no PE header, which is typical of benign system memory.
3. `search_memory(kind="ip")`: `41.168.5.140:8080`, `188.40.0.138:8080`, and `125.19.103.198:8080` inside
   `explorer.exe` (1484).

Finding: injected code in explorer.exe and reader_sl.exe, holding command-and-control style addresses.
Evidence: `windows.malware.malfind` and `windows.vadregexscan`, PIDs 1484 and 1640.

## 8. Checking the AI against the ground truth

[`answer_key.md`](answer_key.md) lists the verified answer to each case question, with the plugin that
proves it. The agent never reads that file. After working the case, compare:

- Did the agent treat the csrss/winlogon `malfind` hits as findings, or recognise them as benign?
- Did it **name the malware family**? Memory shows injection and addresses; naming it "Cridex" relies on
  outside threat intelligence, which the agent should say.
- Which claims did it corroborate with a second plugin?

## 9. Discussion and limits

- **No XP network plugin.** Volatility 3's `netscan` supports Windows Vista and later only. On this XP image,
  `search_memory` finds the addresses inside the process, but memory alone cannot prove a connection
  succeeded (Volatility 2's `connscan` attributed the connection to PID 1484 in public write-ups).
- **The agent assists; the examiner decides.** It removes the typing and the plugin hunt, not the judgment.
- **Free models vary.** Re-run or rephrase if a step is missed; every claim is checkable against the cited
  plugin output.

## 10. Files in this lab

| File | What it is |
|---|---|
| `memory_agent_jupyter.ipynb` | The main lab: run Volatility by hand, then work the case with `talk("...")`. |
| `memory_agent_ui.ipynb` | The same analyst as a Gradio chat window. |
| `memkit.py` | The toolset (one tool per whitelisted plugin), the runner, guardrails, and the system prompt. |
| `memory_app.py` | The Gradio app (optional local run, needs Python with volatility3 + gradio + openai): `python memory_app.py`. |
| `agentkit.py` | The shared agent core (the think-act-observe loop), as in the other labs. |
| `case/case_brief.md` | The case: what happened, what was collected, the questions. |
| `answer_key.md` | The ground truth, for checking the AI's answers. |
| `slides/` | The lecture deck ([PDF](slides/SectraTEK_Lab10_MemoryForensics.pdf) / [PPTX](slides/SectraTEK_Lab10_MemoryForensics.pptx)). |

The memory image is downloaded at run time and is never stored in this repository.

## 11. Credits and data sources

Lab design and code by Daniel Kwaku Ntiamoah Addai, SectraTEK Lab. Memory analysis by
[Volatility 3](https://github.com/volatilityfoundation/volatility3) (Volatility Foundation, Volatility
Software License), installed from PyPI at run time. The Cridex memory image is a widely used public teaching
sample listed on the Volatility Foundation's memory-samples page; the notebook downloads it from the public
mirror [Divinemonk/memory_forensics_with_volatility](https://github.com/Divinemonk/memory_forensics_with_volatility/releases/tag/mem_sample)
(release `mem_sample`, MIT licensed) and verifies it against pinned hashes. The case story is a fictional framing for the class.

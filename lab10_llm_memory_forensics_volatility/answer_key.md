# Answer key: Case MF-2026-001 (Cridex memory image)

For students and instructors to **compare the agent's answers against**. The agent never reads this
file (its tools only see the memory image and `case/case_brief.md`).

Every result below was reproduced with Volatility 3 (2.28.2) on `cridex.vmem`
(MD5 `7494f3b77db1525c1974f5380744ae46`). Items marked *(public write-ups)* come from widely published
analyses of this sample and were not independently confirmed here.

| # | Question | Ground truth | Plugin |
|---|---|---|---|
| 1 | OS and capture time | Windows XP SP3, 32-bit (PAE), build 2600; captured 2012-07-22 02:45:08 UTC | `windows.info` |
| 2 | Processes and tree | 17 processes. `explorer.exe` (PID 1484) has parent PID 1464, which is not running. `reader_sl.exe` (PID 1640) is a child of explorer.exe | `pslist`, `pstree` |
| 3 | Unusual process | `reader_sl.exe` (1640): Adobe Reader's speed-launcher, normally harmless, started by explorer. It stands out because malfind finds injected code in it (row 4), not because of its name | `pstree`, `cmdline`, `malfind` |
| 4 | Injected code | `malfind` finds an injected **PE file (MZ header) in RWX memory** in **explorer.exe (1484) at 0x1460000** and **reader_sl.exe (1640) at 0x3d0000**. The csrss.exe (584) and winlogon.exe (608) hits are **benign false positives** (no PE header). `ldrmodules` corroborates both: each region is in **none** of the three loader lists (InLoad, InInit, InMem all False) and has no file behind it. | `malfind`, `ldrmodules` |
| 5 | Network indicators | `41.168.5.140:8080`, `188.40.0.138:8080`, and `125.19.103.198:8080` found **inside explorer.exe (1484)** process memory (a fragment also in reader_sl.exe, 1640). These are Cridex command-and-control addresses *(public write-ups)* | `search_memory` (`windows.vadregexscan`) |
| 6 | Limits | Memory shows injected code and C2 addresses, not who sent the PDF, what was stolen, or whether a connection succeeded. Volatility 3 cannot list XP network connections (Volatility 2's `connscan` attributed the C2 connection to PID 1484 *(public write-ups)*). Next: disk image, network logs, dump and analyse the injected PE | - |

**Malware family:** Cridex (a banking trojan, predecessor of Dridex) *(public write-ups)*. The memory
alone shows injection and C2 addresses; naming the family relies on threat intelligence, which is the
kind of claim the agent should flag as needing outside confirmation.

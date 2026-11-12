# Case MF-2026-001: Strange behaviour on an accounts workstation (training case)

## What happened
A clerk in the accounts office of a small firm reported that their Windows XP workstation became slow
and that their online-banking session "behaved strangely" shortly after they opened a PDF attachment.
The workstation was not shut down. IT captured a copy of its physical memory (RAM) before isolating it.

## What was collected
- One memory image: `cridex.vmem` (512 MB, captured 2012-07-22).
- No disk image, no network capture. Memory is the only evidence in this case.

## What the investigator needs answered
1. What operating system is this, and when was memory captured?
2. Which processes were running, and which process launched which?
3. Is any process unusual for this system? Why?
4. Is there evidence of code injected into a running process? Which ones?
5. Are there any network indicators (addresses the machine was talking to)? Which process holds them?
6. What can the memory evidence NOT tell us, and what would you collect next?

## Ground rules
- Every finding must cite the Volatility plugin and the PID it came from.
- A suspicious result is a lead. Corroborate it with a second plugin before you call it a finding.
- This is a training case. The memory image is the public Cridex teaching sample; the story above is a
  fictional framing for the class.

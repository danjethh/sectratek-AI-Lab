# Case DF-2026-025: Memory Forensics and Credential Theft

*Synthetic teaching report. All names, systems, and indicators are fictional.*

Examiner: Analyst B, SectraTEK Lab
Device: HP EliteBook laptop (Windows 10)
Acquisition: live RAM capture (16 GB), analyzed with Volatility 3

## Summary
A laptop suspected of credential theft was captured while powered on. Memory analysis found a
credential-dumping tool resident in memory and signs that domain credentials were harvested.

## Key findings
- A process named svch0st.exe (note the zero) was running from a user profile, not System32.
- Strings consistent with Mimikatz (sekurlsa, logonpasswords) were present in that process.
- The LSASS process had an unusual handle opened by svch0st.exe, consistent with a memory read.
- A scheduled task re-launched the tool at logon for persistence.

## Indicators
- Malicious process: svch0st.exe (PID 4821)
- Parent process: powershell.exe launched from a macro
- Persistence: scheduled task "WindowsUpdateHelper"
- Observed technique: LSASS memory access for credential extraction

## Conclusion
The evidence supports in-memory credential dumping of domain accounts via a Mimikatz-like tool.
Harvested credentials may enable lateral movement. Recommend a domain-wide password reset and
review of authentication logs for pass-the-hash activity.

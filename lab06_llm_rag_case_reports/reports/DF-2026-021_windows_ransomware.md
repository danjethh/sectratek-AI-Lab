# Case DF-2026-021: Windows Ransomware Incident

*Synthetic teaching report. All names, systems, and indicators are fictional.*

Examiner: Analyst C, SectraTEK Lab
Device: Dell OptiPlex workstation (Windows 11)
Acquisition: E01 disk image, FTK Imager

## Summary
A finance workstation was encrypted by ransomware. Hundreds of documents were renamed with a
.lxk extension and a ransom note, README_RECOVER.txt, was dropped in every affected folder.

## Key findings
- Initial access via a malicious macro in an email attachment, invoice_8841.xlsm.
- The macro downloaded a loader from a staging host and executed it from %TEMP%.
- Volume Shadow Copies were deleted with vssadmin to prevent recovery.
- Encryption began 2026-03-04 22:11 UTC and ran for roughly 40 minutes.

## Indicators
- Ransom note filename: README_RECOVER.txt
- Encrypted extension: .lxk
- Bitcoin address in note: 1FakeRansomAddr00000000000000000000
- Loader SHA-256: 9a1d4c0b7e2f5a6c8d3b1e0f4a7c9d2b6e5f8a1c3d7b2e9f0a4c6d8b1e3f5a7c
- Staging host: updates.fake-cdn-host.example

## Conclusion
The incident is consistent with a macro-delivered ransomware loader that disabled local
recovery before encrypting user documents. Behavior resembles common LockBit-style tooling, but
attribution is not confirmed. No evidence of data exfiltration was found in the available logs.

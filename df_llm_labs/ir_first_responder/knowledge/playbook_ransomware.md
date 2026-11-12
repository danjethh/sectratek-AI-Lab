# Ransomware Playbook (SYNTHETIC, for training)

## Classification
Ransomware is a SEV-1 (Critical) incident. Notify management immediately (see template below).

## Indicators
- Files renamed with an unusual extension; ransom notes (e.g. README_RESTORE.txt) in folders.
- Mass file-modification alerts; shadow copies (VSS) deleted; backups failing.
- Security log 1102 (log cleared) or many 4688 process-creation events spawning encryptors.

## Immediate response (first 15 minutes)
1. Declare SEV-1 and assign an Incident Commander.
2. ISOLATE the affected host(s) from the network. Do NOT power off (memory is evidence).
3. Disable the compromised user/service accounts (IT on-call).
4. Notify management using the template in this playbook.

## Management notification template
To: management@northwind.example
Subject: SEV-1 Security Incident - Suspected Ransomware
Body:
Team, the security team has declared a SEV-1 incident: suspected ransomware affecting one or
more endpoints. Affected systems are being isolated now, and evidence is being preserved. We
have engaged the incident-response plan and will provide an update within 60 minutes or sooner
on any material change. No customer action is required at this time.

## Evidence collection
Collect, in this order, before eradication. Use an external, write-protected drive at E:\IR.
- Memory image (volatile - do first):   winpmem.exe -o E:\IR\mem.raw
- Windows event logs:                   wevtutil epl Security E:\IR\Security.evtx
                                         wevtutil epl System E:\IR\System.evtx
- NTFS artifacts:                        collect $MFT, $LogFile, and C:\Windows\Prefetch\*.pf
- Program execution:                     C:\Windows\appcompat\Programs\Amcache.hve
- Ransom note + a few encrypted samples (do not open macros).
Hash every artifact (sha256) and record it in the action log.

## Containment and eradication
- Block the malware's C2 domains/IPs at the firewall.
- Rebuild affected hosts from known-good images; restore data from offline backups only after
  confirming the backups are clean.

## Recovery
- Reset credentials for all accounts used on affected hosts. Monitor for re-infection for 14 days.

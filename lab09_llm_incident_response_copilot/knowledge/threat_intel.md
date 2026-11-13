# SectraTEK - Threat Intelligence (SYNTHETIC, for training)

This is the company's small internal watch-list. The incident copilot compares indicators it extracts
from collected artifacts against this list (the `check_indicators` tool). Everything here is fictional
and exists only for the Sectra First Responder lab.

## Known-bad indicators
These have been seen in prior SectraTEK incidents or came from a trusted sharing group. Treat a match as
high-signal and tie it back to the relevant playbook. Format is one indicator per line: the value, then
two or more spaces, then a short note.

- exfil-sync.example          domain   Known data-exfiltration / DNS-tunnelling C2. Any subdomain counts.
- su.exe                  file     Dropper/loader used to install a persistence service.
- SysUpdateSvc            service  Fake "update" service used for persistence.
- 203.0.113.47          ip       C2 node seen in a prior exfiltration case.
- README_RESTORE.txt      file     Ransom note filename seen in a prior ransomware case.
- update-sync.example         domain   Look-alike callback domain from a prior phishing-to-malware case.
- 198.51.100.90            ip       Credential-phishing landing-page host seen before.

## How to use this list
The copilot extracts candidate indicators (domains, IPs, file names, services) from the artifacts the
team collects, then checks them against the values above. A match is a lead, not proof: confirm it in the
evidence and record it in the incident timeline. New confirmed indicators from an incident should be
added here during the after-action review so the next response is faster.

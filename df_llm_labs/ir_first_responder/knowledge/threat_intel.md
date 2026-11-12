# Northwind Labs - Threat Intelligence (SYNTHETIC, for training)

This is the company's small internal watch-list. The incident copilot compares indicators it
extracts from collected artifacts against this list. Everything here is fictional.

## Known-bad indicators
These have been seen in prior incidents or came from a trusted sharing group. Treat a match as
high-signal and tie it back to the relevant playbook.

- exfil-sync.net          domain   Known data-exfiltration / DNS-tunnelling C2. Any subdomain counts.
- su.exe                  file     Dropper/loader used to install a persistence service.
- SysUpdateSvc            service  Fake "update" service used for persistence.
- 185.220.101.47          ip       C2 node seen in a prior exfiltration case.
- README_RESTORE.txt      file     Ransom note filename seen in a prior ransomware case.

## How to use a match
- A hit on a C2 domain or IP supports the data-exfiltration playbook: contain the host, block the
  indicator at the firewall, and preserve DNS/proxy logs.
- A hit on su.exe or SysUpdateSvc supports persistence/eradication: identify every host with the
  service and remove it during eradication.

## Notes
This list is intentionally tiny for the drill. A real programme would pull from a threat-intel
platform and would include hashes, certificate fingerprints, and expiry dates.

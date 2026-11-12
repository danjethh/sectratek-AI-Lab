# Case DF-2026-039: Network Intrusion and Lateral Movement

Examiner: Analyst A, SectraTEK Lab
Scope: corporate network, endpoint and PCAP review
Acquisition: endpoint logs plus full packet capture (Zeek + Suricata)

## Summary
An intrusion began with a phishing email and progressed to lateral movement and command-and-
control over DNS. Two servers were accessed before containment.

## Key findings
- Initial access: a phishing link harvested a user's credentials on a lookalike login page.
- The attacker used valid credentials over VPN during off-hours.
- Lateral movement used SMB and remote service creation between workstations.
- Command-and-control used DNS tunnelling with long, encoded subdomains.

## Indicators
- Phishing domain: login.fake-sso-portal.com
- C2 technique: DNS tunnelling (encoded TXT queries)
- C2 domain: c2.fake-telemetry-dns.net
- Lateral movement: SMB plus remote service creation (technique T1021)

## Conclusion
The evidence supports a credential-phishing intrusion followed by hands-on-keyboard lateral
movement and DNS-based C2. No ransomware or encryption was observed. Recommend credential
resets, DNS egress monitoring, and review of the two accessed servers for data staging.

# Northwind Labs - Incident Response Plan (SYNTHETIC, for training)

## Purpose and scope
This plan governs how Northwind Labs responds to suspected security incidents on corporate
endpoints, servers, and cloud accounts. It is deliberately simple and is used for drills.

## Severity levels
- SEV-1 (Critical): active ransomware, confirmed data theft, or business-down. Notify management immediately.
- SEV-2 (High): credential compromise, malware on a single host, confirmed phishing with clicks.
- SEV-3 (Low): suspicious email reported, single blocked alert, policy violation.

## Roles
- Incident Commander (IC): owns the response and decisions.
- Communications Lead: handles management and, if needed, customer/legal messaging.
- Forensics Lead: collects and analyses evidence.
- IT On-call: performs containment actions (isolation, disabling accounts).

## Key contacts
- Management distribution list: management@northwind.example
- Legal: legal@northwind.example
- Security on-call: soc@northwind.example
- IT on-call: itoncall@northwind.example

## Response phases
1. Identify: confirm the incident and classify severity.
2. Contain: stop the spread (isolate hosts, disable accounts) without destroying evidence.
3. Eradicate: remove the attacker's foothold.
4. Recover: restore services from known-good state and monitor.
5. Notify: inform management (always for SEV-1/SEV-2); legal and customers per Legal's guidance.
6. Lessons learned: write up the timeline and improvements within 5 business days.

## When to escalate
- Escalate to SEV-1 and notify management immediately on: ransomware/encryption, confirmed
  exfiltration of customer data, or compromise of a privileged/admin account.

## Golden rules
- Preserve evidence before changing a system: do NOT power off a suspected ransomware host
  (you lose memory); isolate it from the network instead.
- Keep an action log with timestamps.
- Notify management before taking externally visible action.

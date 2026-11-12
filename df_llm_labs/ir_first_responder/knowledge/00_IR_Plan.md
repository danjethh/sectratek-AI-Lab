# SectraTEK - Incident Response Plan (SYNTHETIC, for training)

Document owner: SectraTEK Security Operations Centre (SOC). Version 3.0. Review cycle: every 6 months
and after every SEV-1. This plan is fictional and exists only for the Sectra First Responder lab.

## Purpose and scope
This plan governs how SectraTEK detects, responds to, and recovers from security incidents affecting
corporate endpoints, servers, mobile devices, and cloud/identity services. It applies to all staff,
contractors, and automated systems. It defines severity, roles, the response lifecycle, escalation and
notification rules, evidence handling, and legal obligations. The goal is a response that is fast,
consistent, and defensible: every decision is recorded and every piece of evidence is preserved so the
scope can be measured and, if needed, presented to auditors, regulators, or a court.

## Severity levels and response times
Severity is assigned by the first responder using these definitions and is re-checked as facts change.
- SEV-1 (Critical): active ransomware, confirmed data theft, business-down outage, or any confirmed
  compromise of a privileged/admin account. Engage the Incident Commander and notify management
  immediately. Target: acknowledge in 15 minutes, response team engaged in 30 minutes.
- SEV-2 (High): malware on a single host, confirmed phishing with clicks or entered credentials,
  single-user account compromise, suspected data exposure of limited scope. Target: acknowledge in 1
  hour, contain within the business day.
- SEV-3 (Medium): a reported suspicious email with no clicks, one blocked alert, a policy violation, a
  single failed-login spike that was auto-blocked. Target: triage within 1 business day.
- SEV-4 (Low / informational): near-miss, scan noise, or a finding raised for awareness. Log and review.
When unsure between two levels, choose the higher one and downgrade later with a documented reason.

## Roles and responsibilities (RACI)
- Incident Commander (IC): owns the response and all decisions; declares severity; the only role that
  can authorise containment of production systems. Accountable for the whole incident.
- SOC Analyst / First Responder: triages the alert, classifies the incident, collects evidence, runs
  the analysis. Responsible for the hands-on work.
- Forensics Lead: preserves and analyses host, memory, and mobile evidence; maintains chain of custody.
- Communications Lead: drafts and sends management, customer, and (with Legal) regulator messaging.
- IT On-call: performs containment actions the IC approves (isolate host, disable account, block IOC).
- Legal and Privacy Counsel: decides breach-notification and regulatory obligations; consulted on SEV-1.
- Executive Sponsor (CISO): informed on every SEV-1; approves external/customer notification.
Consulted: Legal, HR (insider cases), Comms. Informed: affected business owners, Executive Sponsor.

## The response lifecycle (NIST SP 800-61 / SANS PICERL)
1. Preparation: maintain this plan, the playbooks, logging, backups, and on-call rotas; run drills.
2. Detection and analysis: confirm the alert is a real incident, classify it, and scope it from evidence.
3. Containment: limit the damage. Short-term (isolate the host now) then long-term (rebuild clean).
4. Eradication: remove the root cause - malware, persistence, and attacker access.
5. Recovery: restore from known-clean backups, validate, and monitor for recurrence before closing.
6. Post-incident: write the after-action report; capture lessons learned; update controls and playbooks.
Evidence is preserved before any destructive containment, so scope can always be reconstructed.

## Escalation and notification matrix
- SEV-1: IC + CISO immediately; management within 30 minutes; Legal engaged; Comms on standby for
  customer/regulator messaging. Use the notification template in the relevant playbook.
- SEV-2: IC and SOC lead; management notified within 2 hours if customer data or a privileged account
  is involved; otherwise summarised in the daily report.
- SEV-3 / SEV-4: handled by the SOC; summarised in the daily and weekly reports. No management page.
Escalate upward whenever scope, data sensitivity, or business impact grows. Never wait for certainty to
escalate a SEV-1.

## Communications protocol
Use the out-of-band channel (the incident bridge and the SOC phone tree), never the potentially
compromised corporate email or chat, until containment is confirmed. One Communications Lead speaks for
the incident. Hold external statements until Legal and the CISO approve. Record every notification (who,
what, when) in the incident ticket.

## Evidence handling and chain of custody
Preserve before you change: capture volatile data (memory, network state) and logs before isolating or
rebuilding. Record for each artifact: what it is, where and when it was collected, by whom, and its hash.
Store evidence read-only in the case folder; work from copies. Do not power off a host under active
ransomware (memory is evidence) unless the IC directs it. Maintain an unbroken custody log so the
evidence is admissible.

## Legal and regulatory obligations
Confirmed theft or exposure of personal data triggers breach-notification duties with hard deadlines
(for example, many regimes require regulator notification within 72 hours of becoming aware). Legal
owns this decision; the SOC's job is to give Legal an accurate, evidenced scope quickly. Preserve
evidence to the legal standard from the first minute, because an incident can become litigation.

## Authority to act
The IC authorises containment of production systems. The SOC may take read-only investigative steps at
any time without further approval. Any action with an external side effect (notifying people, opening
tickets, paging on-call, blocking at the firewall, disabling accounts) requires explicit approval and
is logged. Automated copilots may draft and recommend freely but must not act without a human's yes.

## Drill cadence and maintenance
Run a tabletop drill quarterly and a technical drill twice a year. After every SEV-1 and every drill,
update this plan and the playbooks within two weeks. Keep the contact tree and tool list current.

## Contact tree (synthetic)
- SOC / first responders: soc@sectratek.example
- Incident Commander on-call: ic@sectratek.example
- Forensics Lead: forensics@sectratek.example
- Communications Lead: comms@sectratek.example
- Legal and Privacy: legal@sectratek.example
- Management distribution: management@sectratek.example

# Ransomware Playbook (SYNTHETIC, for training)

SectraTEK SOC playbook for suspected or confirmed ransomware on an endpoint or server. Use with the
IR Plan. Everything here is fictional and for the Sectra First Responder drill.

## Classification
Ransomware is a SEV-1 (Critical) incident. Notify management immediately (see the notification template
below) and engage an Incident Commander. If the encryptor is still running or has spread beyond one
host, keep it SEV-1 and widen the response; do not downgrade until spread is ruled out from evidence.

## Indicators
- Files renamed with an unusual or random extension; ransom notes dropped in many folders (a common
  filename seen before is README_RESTORE.txt).
- Mass file-modification alerts in a short window; volume shadow copies (VSS) deleted; backup jobs
  suddenly failing.
- Windows Security log 1102 (audit log cleared), bursts of 4688 process-creation events launching
  scripting or archive tools, or a service installed for persistence.
- An interactive logon from an internal host that had just produced many failed-logon (4625) events,
  suggesting a brute force that finally succeeded.

## Immediate response (first 15 minutes)
1. Declare SEV-1 and assign an Incident Commander. Open the incident bridge (out-of-band).
2. ISOLATE the affected host(s) from the network. Do NOT power off - memory is evidence and may hold
   keys or the encryptor's state. Isolation stops spread without destroying that evidence.
3. Disable the compromised user and service accounts (IT on-call, with IC approval).
4. Identify whether backups are intact and offline; protect them from the attacker immediately.
5. Notify management using the template in this playbook, and engage Legal (data theft often precedes
   ransomware, so a breach may also apply).

## Evidence collection
Preserve before eradicating. Collect, hashing each item and recording custody:
- Volatile first: a memory image of the affected host, and current network connections and process list.
- The ransom note file and a sample of encrypted files (for identification of the ransomware family).
- Windows Event Logs (Security, System, Application), especially IDs 1102, 4624, 4625, 4688, 7045.
- The affected user's command history and any dropped binaries from Downloads/Temp.
- Firewall and DNS logs around the event window, to find command-and-control or exfiltration traffic.
Work from read-only copies in the case folder; never analyse the only copy.

## Containment
- Short-term: keep the host isolated at the switch/firewall; block any identified C2 domains and IPs;
  disable the involved accounts and rotate their credentials.
- Long-term: segment the affected subnet, force a password reset for any accounts seen on the host, and
  hunt for the same indicators on other hosts before reconnecting anything.
Containment actions are run by IT on-call after the IC approves; the copilot may only simulate them.

## Eradication
- Remove persistence: the installed service, scheduled tasks, run keys, and any dropped loaders.
- Rebuild affected hosts from a known-good image rather than cleaning in place - ransomware rarely comes
  alone, and a cleaned host cannot be trusted.
- Reset all credentials used on the host, including any cached domain or service accounts.
- Confirm the initial access vector is closed (patched, reconfigured, or the account secured) so the
  attacker cannot simply return.

## Recovery
- Restore data only from backups taken before the compromise and verified clean; never pay without
  Legal/Exec direction and never restore onto an un-rebuilt host.
- Validate restored systems (integrity, function) in a monitored state before returning them to service.
- Monitor the environment closely for recurrence for at least two weeks: watch for the same indicators,
  new persistence, and repeat brute-force attempts.
- Close the incident only when the IC confirms eradication held and business function is restored.

## Management notification template
To: management@sectratek.example
Subject: SEV-1 Security Incident - Suspected ransomware
Team, the SOC is responding to a suspected ransomware incident affecting [host/business area]. The
affected system(s) have been isolated and the response team is following the IR plan. At this stage we
have [one-line factual status]. We are preserving evidence, assessing scope and backups, and have
engaged Legal. We will send the next update within 60 minutes or sooner on any material change.
Incident Commander: [name]. Reference: [ticket].

## MITRE ATT&CK reference (for analysts)
Common techniques: Valid Accounts (T1078), Brute Force (T1110), Command and Scripting Interpreter
(T1059), Inhibit System Recovery / delete shadow copies (T1490), Data Encrypted for Impact (T1486),
Indicator Removal / clear logs (T1070). Use these to guide the hunt, not as proof.

## Decision points
- Is spread confirmed contained? If not, stay SEV-1 and widen isolation.
- Are clean offline backups available? This decides the recovery path.
- Is there evidence of data theft before encryption? If yes, trigger the data-exfiltration playbook and
  breach assessment in parallel.

## After-action
Record the timeline, root cause, dwell time, what worked, and what to improve. Feed fixes (patching,
MFA, backup hardening, segmentation) back into Preparation and update this playbook.

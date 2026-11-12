# Phishing Playbook (SYNTHETIC, for training)

SectraTEK SOC playbook for reported phishing, credential harvesting, and malicious attachments. Use
with the IR Plan. Fictional, for the Sectra First Responder drill.

## Classification
A reported phishing email with no clicks and no entered credentials is SEV-3. If a user entered
credentials on a linked page, or opened/ran an attachment, treat it as SEV-2 and notify management.
If the compromised account is privileged, or many users are affected, escalate to SEV-1.

## Indicators
- A reported suspicious email; a mismatched sender and display name; a look-alike or newly registered
  sender domain; urgent or threatening language pushing the user to act fast.
- A user reports entering their password on a linked page, or opening an attachment that asked to enable
  content or macros.
- Mail-gateway alerts; an unusual sign-in location or new device for a user shortly after the email;
  a mailbox rule created to auto-forward or hide messages (a classic post-compromise move).

## Immediate response
1. Ask the reporting user NOT to delete the email; have them forward it as an attachment to
   soc@sectratek.example so headers are preserved.
2. If credentials were entered: reset that user's password and revoke all active sessions and tokens
   (IT on-call), then check for and remove any attacker-created mailbox forwarding rules.
3. Search the mail system for every recipient of the same message and quarantine/recall it.
4. If an attachment was opened or run, isolate that host and treat it as possible malware (pivot to the
   ransomware/malware response for evidence collection).
5. Notify management if this is SEV-2 or above, using the template below.

## Evidence collection
- The original email as an attachment, with full headers (sender IP, authentication results, path).
- The URLs and any attachment, detonated only in a safe sandbox, never on a corporate host.
- Sign-in and audit logs for the affected account: successful and failed logins, locations, devices,
  MFA prompts, and any new mailbox rules or OAuth app grants.
- If an attachment ran: host logs, process creation events, and any dropped files (preserve and hash).
Record custody for every item and work from copies.

## Containment
- Quarantine the phishing message across all mailboxes; block the sender domain and any payload URLs.
- Disable or force-reset the affected account; revoke sessions and tokens; remove malicious mailbox
  rules and unauthorised OAuth grants.
- If a host was involved, isolate it at the network until it is cleared.
IT on-call runs these with IC approval; the copilot may only simulate them.

## Eradication
- Remove the malicious mailbox rules, OAuth app consents, and any persistence on an affected host.
- Reset credentials for the affected user and any shared/service account they could reach.
- Close the delivery gap: tune the mail gateway, block the look-alike domain, and brief the user.

## Recovery
- Restore normal access once the account is secured and sessions are clean; monitor the account and the
  mailbox for re-compromise (new rules, odd sign-ins) for at least a week.
- Confirm no onward movement occurred from the account before closing.
- Record the lure and send a short, blameless awareness note to the affected team.

## Management notification template
To: management@sectratek.example
Subject: Security Incident - Phishing with credential compromise
Team, the SOC is responding to a phishing incident in which [N] user(s) [entered credentials / ran an
attachment]. Affected account(s) have been reset and sessions revoked; the message has been quarantined
across the organisation. Current scope: [one-line factual status]. We are reviewing sign-in logs for any
further access and will update within 60 minutes or on any material change. Incident Commander: [name].
Reference: [ticket].

## MITRE ATT&CK reference (for analysts)
Common techniques: Phishing (T1566), Valid Accounts (T1078), Steal Web Session Cookie (T1539), Email
Collection / mailbox rules (T1114), Account Manipulation (T1098). Use to guide the hunt.

## Decision points
- Were credentials actually entered, or only exposed? This sets SEV-2 vs SEV-3.
- Is the account privileged or widely shared? If yes, escalate and widen the hunt.
- Did an attachment execute? If yes, run the malware/ransomware evidence steps on the host in parallel.

## After-action
Capture the lure, the delivery gap it exploited, and detection timing. Feed improvements (gateway rules,
MFA coverage, user training) back into Preparation and update this playbook.

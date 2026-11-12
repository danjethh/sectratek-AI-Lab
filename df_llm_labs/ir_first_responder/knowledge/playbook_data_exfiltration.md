# Data Exfiltration Playbook (SYNTHETIC, for training)

SectraTEK SOC playbook for suspected or confirmed theft of customer or sensitive data, including
DNS-tunnelling and cloud-upload exfiltration. Use with the IR Plan. Fictional, for the Sectra drill.

## Classification
Suspected or confirmed theft of customer or sensitive data is SEV-1. Notify management and Legal
immediately: data-breach notification deadlines may start the moment SectraTEK becomes aware. Keep it
SEV-1 until the scope of data moved is bounded by evidence.

## Indicators
- Large or unusual outbound transfers to an unfamiliar host; a spike in DNS queries to a single rare
  domain or many random subdomains of it (a sign of DNS tunnelling).
- Cloud-storage uploads outside normal business use; access to sensitive shares by an account that does
  not normally touch them; archiving tools (7-Zip, rar) running just before an upload.
- Activity outside the user's normal hours, or a burst of reads across many sensitive files.

## Immediate response
1. Declare SEV-1 and engage Legal early (breach obligations may apply with hard deadlines).
2. Identify the account and host involved; prepare to disable the account and isolate the host.
3. PRESERVE network and host evidence BEFORE blocking, so the volume and nature of data moved can be
   measured - blocking first can destroy the record of what left.
4. Then contain: isolate the host, disable the account, and block the destination domain/IP.
5. Notify management and Legal using the template below.

## Evidence collection
- Firewall, proxy, and DNS logs for the host across the event window: destinations, bytes out, and
  query volume per domain (to quantify what was tunnelled or uploaded).
- NetFlow or packet capture if available, to size the transfer.
- Host artifacts: the archiving-tool execution, the staged archive, command history, and any uploader
  binary or script (preserve and hash each).
- Access logs for the sensitive shares or database: which records the account touched and when.
Measuring scope is the goal: Legal needs an evidenced count of what data left, not a guess.

## Containment
- Block the exfiltration destination (domain and IP) at the firewall/DNS; isolate the involved host.
- Disable the account and rotate its credentials; revoke tokens and keys it held.
- If a service or API key was used, rotate it and review what else it could reach.
IT on-call runs these after the IC approves; the copilot may only simulate them.

## Eradication
- Remove the staging archive, the uploader/tunnelling tool, and any persistence that enabled access.
- Close the access path: revoke the over-broad permissions, reset the account, and fix the control that
  let a non-owner reach the sensitive data.
- Confirm no secondary channels (a second account, a scheduled job) remain.

## Recovery
- Restore normal service once the path is closed and credentials rotated; monitor the destination
  indicators, the account, and the sensitive shares for renewed activity for at least two weeks.
- Give Legal the final evidenced scope so any required regulator/customer notification can be completed
  within the deadline.
- Close only when the IC confirms the channel is shut and scope is documented.

## Management notification template
To: management@sectratek.example
Subject: SEV-1 Security Incident - Suspected data exfiltration
Team, the SOC is responding to suspected exfiltration of [data type] from [system/host]. We have
preserved network and host evidence and are measuring the volume and nature of data that left before
fully blocking the channel. Legal is engaged to assess notification obligations. Current scope: [one-line
factual status]. We will update within 60 minutes or on any material change. Incident Commander: [name].
Reference: [ticket].

## MITRE ATT&CK reference (for analysts)
Common techniques: Exfiltration Over C2 Channel (T1041), Exfiltration Over Alternative Protocol / DNS
(T1048), Archive Collected Data (T1560), Automated Exfiltration (T1020), Valid Accounts (T1078).

## Decision points
- Is the data personal or regulated? This drives Legal's notification clock.
- Can the volume moved be measured from logs? If not, preserve more before blocking.
- Was the access authorised but misused (insider) or external? This changes containment and HR/Legal.

## After-action
Record what data left, the channel, dwell time, and how it was detected. Feed improvements (egress
filtering, DLP, least-privilege on sensitive shares, DNS monitoring) back into Preparation and update
this playbook.

# Data Exfiltration Playbook (SYNTHETIC, for training)

## Classification
Suspected or confirmed theft of customer or sensitive data is SEV-1. Notify management and Legal
immediately.

## Indicators
- Large outbound transfers to unfamiliar hosts; spikes in DNS to a single rare domain (possible
  DNS tunnelling); cloud-storage uploads outside business use.
- Access to sensitive shares by an account that does not normally touch them.
- Security alerts for archiving tools (7-Zip, rar) running before an upload.

## Immediate response
1. Declare SEV-1; engage Legal (data-breach obligations may apply).
2. Identify the account and host involved; disable the account and isolate the host.
3. Preserve network and host evidence before blocking, so the scope can be measured.
4. Notify management and Legal using the template below.

## Management notification template
To: management@northwind.example
Subject: SEV-1 Security Incident - Suspected Data Exfiltration
Body:
Team, we are investigating a suspected exfiltration of sensitive data. The involved account has
been disabled and the host isolated. Evidence is being preserved so we can determine what, if
anything, left the environment. Legal has been engaged. We will provide an assessment within 2
hours; please avoid external statements until then.

## Evidence collection
- Proxy and firewall logs for the host (export E:\IR\exfil\proxy.csv, firewall.csv).
- DNS query logs for the host (look for high-volume or long subdomains - DNS tunnelling).
- EDR process tree and file-access history for the account.
- The destination domains/IPs and byte counts, to size the transfer.
Commands/examples:
- Review DNS: filter dns_queries.csv for the host and sort by query count.
- Netflow: sum bytes_out grouped by destination IP.

## Containment and recovery
- Block the destination domains/IPs; revoke the account's tokens and keys.
- Work with Legal on notification duties. Preserve everything; do not wipe until Legal clears it.

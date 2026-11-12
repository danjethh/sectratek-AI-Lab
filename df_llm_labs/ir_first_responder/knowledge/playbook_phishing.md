# Phishing Playbook (SYNTHETIC, for training)

## Classification
A reported phishing email with no clicks is SEV-3. If a user entered credentials or ran an
attachment, treat it as SEV-2 and notify management.

## Indicators
- Reported suspicious email; mismatched sender/display name; look-alike domain.
- A user reports entering their password on a linked page, or opening an attachment.
- Mail gateway alerts; one user with an unusual sign-in location right after the email.

## Immediate response
1. Ask the user not to delete the email; have them forward it as an attachment to soc@northwind.example.
2. If credentials were entered: reset that user's password and revoke active sessions (IT on-call).
3. Search the mail system for other recipients of the same message and quarantine it.
4. If an attachment was run, isolate the host and treat as possible malware (see ransomware playbook).

## Management notification template
To: management@northwind.example
Subject: SEV-2 Security Incident - Phishing with possible credential compromise
Body:
Team, a phishing email reached staff and at least one user may have entered credentials. We have
reset the affected account, revoked its sessions, and are removing the message from other mailboxes.
No evidence of further access yet. We will update within 60 minutes.

## Evidence collection
- The reported email, saved as .eml (keep full headers).  Path: E:\IR\phish\message.eml
- Mail gateway logs for the sender/subject (export to E:\IR\phish\gateway.csv).
- Sign-in logs for the affected user (export the last 7 days).
- If a link was visited: proxy/DNS logs for the look-alike domain.

## Containment and recovery
- Block the sender domain and the phishing URL at the gateway and proxy.
- Enforce MFA re-registration for the affected user. Monitor the account for 7 days.

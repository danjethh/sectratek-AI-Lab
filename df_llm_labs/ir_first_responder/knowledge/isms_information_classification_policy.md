# SectraTEK - Information Classification Policy (SYNTHETIC, for training)

Part of the SectraTEK ISO/IEC 27001 ISMS (aligns with Annex A control A.5.12, Classification of
information). Defines how information is classified and handled, which drives how seriously an incident
is treated and what notification obligations apply. Fictional, for the Sectra First Responder lab.

## Classification levels
- Restricted: most sensitive. Customer PII, cardholder data, credentials, authentication systems. Loss
  causes severe harm and regulatory exposure. Any incident touching Restricted data is at least SEV-1.
- Confidential: internal-only business data (finance, HR, internal documents). Loss causes significant
  harm. Incidents are SEV-1 or SEV-2 depending on scope.
- Internal: routine internal information not meant for the public. Limited harm if exposed.
- Public: approved for public release. No confidentiality impact.

## Handling rules
- Restricted and Confidential data is encrypted at rest and in transit, access is least-privilege, and
  access is logged and reviewed.
- Data may only be stored on approved systems in the asset register. Moving Restricted data to an
  unapproved location is itself a reportable incident.

## Breach and notification implications
- A confirmed compromise of Restricted personal data triggers the breach-notification process (see the
  Incident Management Policy): Legal assesses regulator and customer notification against the legal
  deadline. The classification of the data involved, not the size of the incident, drives this.
- Confidential business data exposure is reported to management; customer/regulator notification is
  assessed with Legal only if personal or contractual data is involved.

## How the copilot should use this
When an incident involves an asset, use its classification (from the asset register) to set the minimum
severity and to flag whether the breach-notification process may be triggered. Recommend involving Legal
early whenever Restricted personal data may be affected.

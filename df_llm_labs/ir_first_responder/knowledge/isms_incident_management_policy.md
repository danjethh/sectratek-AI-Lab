# SectraTEK - Incident Management Policy (SYNTHETIC, for training)

Part of the SectraTEK ISO/IEC 27001 ISMS. This policy sits above the operational IR plan and playbooks
and aligns with Annex A controls A.5.24-A.5.28 (incident management planning, assessment, response,
learning, and evidence). The IR plan and playbooks must stay consistent with this policy. Fictional,
for the Sectra First Responder lab.

## Purpose and scope
Ensure security incidents are reported, assessed, and responded to consistently, that evidence is
preserved, and that lessons improve the ISMS. Applies to all staff, systems, and third parties.

## Reporting and assessment (A.5.24 / A.5.25)
- All suspected incidents are reported to the SOC without delay via the incident channel.
- The SOC assesses and classifies each event using the IR plan's severity scale, informed by the
  classification and criticality of the assets involved (asset register).

## Response (A.5.26)
- Response follows the IR plan and the relevant playbook. Containment of production systems requires
  Incident Commander authorisation. Actions with external effect are approved and logged.

## Collection of evidence (A.5.28)
- Evidence is preserved before any destructive action, with recorded chain of custody, so it is
  admissible and the scope is defensible. Volatile data is captured first.

## Communication and notification
- Internal: management is notified for SEV-1 and SEV-2 incidents per the IR plan's matrix.
- External: customer, regulator, and partner notification is decided by Legal, driven by data
  classification and legal deadlines. No external statement is made without Legal and CISO approval.

## Learning from incidents (A.5.27)
- Every SEV-1 and every drill produces an after-action review within the stated window. Findings update
  the risk register, the controls, and the playbooks.

## How the copilot should use this
Keep all guidance within this policy: report and classify using asset context, preserve evidence before
containment, gate external actions on approval, and involve Legal for notification when classification
requires it. Cite this policy when explaining why a step is required.

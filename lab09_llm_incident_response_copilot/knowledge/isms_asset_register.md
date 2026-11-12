# SectraTEK - ISMS Asset Register and Business Impact (SYNTHETIC, for training)

Part of the SectraTEK ISO/IEC 27001 Information Security Management System (ISMS). This register records
information assets, their owners, classification, criticality, and recovery objectives. The incident
copilot consults it so its guidance matches the business value of the asset involved. All data is
fictional and exists only for the Sectra First Responder lab.

## Classification and criticality scale
- Classification (confidentiality): Restricted > Confidential > Internal > Public.
- Criticality (business impact if lost or down): Critical > High > Medium > Low.
- RTO = recovery time objective (how fast it must be back). RPO = recovery point objective (tolerable
  data loss). MTD = maximum tolerable downtime.

## Asset register
Each row: Asset ID | Asset and aliases | Owner | Classification | Criticality | Business function | Location | RTO / RPO

| Asset ID | Asset and aliases | Owner | Classification | Criticality | Business function | Location | RTO / RPO |
|---|---|---|---|---|---|---|---|
| FIN-WS-04 | Finance workstation; finance PC; AP workstation; accounts payable PC | Finance Operations | Confidential | High | Accounts-payable and payroll preparation | HQ, Finance floor | 4h / 1h |
| DC-01 | Domain controller; Active Directory; AD | IT Infrastructure | Restricted | Critical | Identity and authentication for all staff | HQ data centre | 1h / 15m |
| DB-CUST-01 | Customer database; CRM database; customer data server | Data Platform | Restricted | Critical | Holds customer PII and account records | Cloud (primary region) | 2h / 15m |
| PAY-GW-01 | Payment gateway; billing gateway | Finance Systems | Restricted | Critical | Processes customer card payments | Cloud (PCI segment) | 1h / 5m |
| MAIL-365 | Email; Microsoft 365 tenant; Exchange Online | IT Infrastructure | Confidential | High | Corporate email and collaboration | SaaS (Microsoft 365) | 4h / 1h |
| FS-01 | File server; shared drive; departmental shares | IT Infrastructure | Confidential | High | Shared documents incl. Finance and HR folders | HQ data centre | 8h / 4h |
| BKP-01 | Backup server; backup repository | IT Infrastructure | Confidential | High | Offline and immutable backups for all systems | HQ data centre (segmented) | 8h / 24h |
| VPN-GW-01 | VPN gateway; remote-access gateway | IT Infrastructure | Confidential | High | Remote staff access | HQ edge | 4h / n/a |
| HR-APP-01 | HR system; HRIS | Human Resources | Restricted | High | Employee records and payroll data | SaaS | 24h / 8h |
| EXEC-LT-02 | CEO laptop; executive laptop | IT Infrastructure | Restricted | High | Executive device, high-value phishing target | Mobile | 8h / 4h |
| WEB-01 | Public website; marketing site | Marketing | Public | Medium | Public web presence | Cloud (DMZ) | 12h / 12h |
| KIOSK-03 | Reception kiosk; lobby kiosk | Facilities | Public | Low | Visitor sign-in | HQ lobby | 48h / n/a |

## How the copilot should use this
When the team names a host, account, or system, look it up here by name or alias and report its owner,
classification, criticality, and RTO/RPO. Let that raise or confirm severity (an incident on a Critical
or Restricted asset is at least SEV-1), decide who must be notified, and set the recovery priority. If
an asset is not listed, say so and ask the owning team; do not guess its criticality.

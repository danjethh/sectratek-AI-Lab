# SectraTEK - ISMS Risk Register (SYNTHETIC, for training)

Part of the SectraTEK ISO/IEC 27001 ISMS. Records the information-security risks the organisation has
assessed, their rating, and how they are being treated. The incident copilot uses it to tie an active
incident back to a known risk and its treatment. Fictional, for the Sectra First Responder lab.

## Rating scale
Risk rating = Likelihood x Impact, expressed as Critical / High / Medium / Low. Treatment options:
Mitigate, Transfer, Avoid, Accept.

## Risk register
| Risk ID | Risk | Affected assets | Likelihood | Impact | Rating | Treatment | Owner |
|---|---|---|---|---|---|---|---|
| R-01 | Ransomware encrypts endpoints or servers, halting operations | FIN-WS-04, FS-01, DC-01 | Medium | Critical | High | Mitigate: EDR, offline immutable backups (BKP-01), segmentation, user training | CISO |
| R-02 | Theft of customer PII (exfiltration) | DB-CUST-01, FS-01 | Medium | Critical | High | Mitigate: DLP, egress filtering, least privilege, monitoring | Data Platform |
| R-03 | Credential phishing leading to account takeover | MAIL-365, EXEC-LT-02 | High | High | High | Mitigate: MFA, mail filtering, awareness; Transfer: cyber insurance | IT Infrastructure |
| R-04 | Compromise of privileged/admin accounts | DC-01 | Low | Critical | High | Mitigate: PAM, tiered admin, MFA, logging | IT Infrastructure |
| R-05 | Payment-system compromise / card data exposure | PAY-GW-01 | Low | Critical | High | Mitigate: PCI DSS controls, network isolation | Finance Systems |
| R-06 | Backup failure or compromise during an incident | BKP-01 | Low | High | Medium | Mitigate: immutable, segmented, tested restores | IT Infrastructure |
| R-07 | Insider misuse of access to sensitive data | HR-APP-01, FS-01 | Low | High | Medium | Mitigate: least privilege, access reviews, logging | HR / IT |

## How the copilot should use this
When an incident matches a known risk, name the Risk ID and its treatment so the team can see whether a
planned control held or failed, and so the lesson can be fed back into the risk register at the
after-action review. A control that failed is a risk-treatment gap to raise, not just an incident note.

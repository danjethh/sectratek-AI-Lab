# SectraTEK - Statement of Applicability, selected controls (SYNTHETIC, for training)

An extract of the SectraTEK ISO/IEC 27001:2022 Statement of Applicability (SoA), limited to the Annex A
controls most relevant to incident response. The copilot can map an incident to the controls that
should have prevented or detected it, and to those that govern the response. Fictional, for the lab.

## Selected Annex A controls (2022)
| Control | Name | Status | Relevance to incidents |
|---|---|---|---|
| A.5.7 | Threat intelligence | Implemented | Feeds the watch-list used to recognise known-bad indicators |
| A.5.24 | Information security incident management planning and preparation | Implemented | The IR plan and playbooks exist and are drilled |
| A.5.25 | Assessment and decision on information security events | Implemented | Severity classification using asset context |
| A.5.26 | Response to information security incidents | Implemented | Playbook-driven, approval-gated response |
| A.5.27 | Learning from information security incidents | Implemented | After-action review updates the ISMS |
| A.5.28 | Collection of evidence | Implemented | Chain-of-custody evidence handling |
| A.8.7 | Protection against malware | Implemented | EDR / anti-malware on endpoints and servers |
| A.8.13 | Information backup | Implemented | Offline, immutable, tested backups (BKP-01) |
| A.8.15 | Logging | Implemented | Security logs retained for detection and investigation |
| A.8.16 | Monitoring activities | Implemented | Alerting on anomalous activity |
| A.5.14 | Information transfer | Implemented | Controls on data egress, relevant to exfiltration |

## How the copilot should use this
When useful, name the control an incident relates to: the control that failed (a prevention/detection
gap to raise at the after-action review) or the control governing the response (for example A.5.28 for
evidence). Keep this to a brief, relevant reference, not a full audit.

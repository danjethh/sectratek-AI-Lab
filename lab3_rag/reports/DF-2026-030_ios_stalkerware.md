# Case DF-2026-030: iOS Stalkerware Assessment

Examiner: Analyst A, SectraTEK Lab
Device: Apple iPhone 13 (iOS 17)
Acquisition: logical + sysdiagnose, analyzed with MVT and manual review

## Summary
A personal iPhone was examined after the owner reported being tracked. The device showed signs
consistent with a commercial monitoring app (stalkerware), including a configuration profile and
periodic background network beaconing.

## Key findings
- A configuration profile granted VPN and web-filter permissions, installed outside MDM.
- Periodic HTTPS beacons every 15 minutes to a monitoring back-end during charging hours.
- Elevated background location and microphone access by a non-App-Store helper process.
- The app icon was hidden from the home screen.

## Indicators
- Beacon domain: sync.fake-familytrack.app
- Beacon interval: approximately every 15 minutes
- Profile display name: "Device Services"
- Classification: dual-use monitoring / stalkerware (web-verified vendor)

## Conclusion
Findings are consistent with installed stalkerware performing location and audio monitoring. On
an unsupervised device, profile payload contents are limited, so some detections are
capability-dependent. Recommend removing the profile and rotating the owner's account passwords.

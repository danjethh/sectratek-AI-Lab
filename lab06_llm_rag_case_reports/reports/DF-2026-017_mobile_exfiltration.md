# Case DF-2026-017: Suspected Customer-Data Exfiltration

*Synthetic teaching report. All names, systems, and indicators are fictional.*

Examiner: Analyst B, SectraTEK Lab
Device: Google Pixel 7 (Android 14)
Acquisition: full file system, Cellebrite UFED 7.64
Incident window (UTC): 2026-02-15 01:00 to 01:15

## Summary
A company-issued Android phone was reviewed after a possible leak of the file
customers_q1.csv before an employee's departure. The artifacts show the file being staged in
Telegram storage, outbound Telegram and Gmail messages, related network activity, and deletion
of the original file from Downloads.

## Key findings
- 01:05:22 - customers_q1.csv created in /Download.
- 01:07:41 - the same file hash copied into Telegram's Documents folder.
- 01:07:58 - outbound Telegram message: "sending that sheet now".
- 01:09:44 - outbound Gmail message: "see attached export".
- 01:12:04 - customers_q1.csv deleted from Downloads.

## Indicators
- SHA-256 of customers_q1.csv: 531ec9ebf8f4492754f16b1437f1824995c8bf4ee2f6be74d4f2f13fdf3f2ab5
- Network endpoints: api.telegram.org, smtp.gmail.com

## Conclusion
The evidence supports staging and attempted external sharing of the file through Telegram and
Gmail. It does not, on its own, confirm that the file was delivered to or received by any
recipient. Recommend correlation with recipient-side or provider records.

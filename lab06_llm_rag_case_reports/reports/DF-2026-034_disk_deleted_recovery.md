# Case DF-2026-034: Disk Image and Deleted-File Recovery

*Synthetic teaching report. All names, systems, and indicators are fictional.*

Examiner: Analyst C, SectraTEK Lab
Device: external USB drive (exFAT), 128 GB
Acquisition: raw dd image, verified by SHA-256

## Summary
An external drive suspected of holding deleted evidence was imaged and carved. Several images
and a spreadsheet were recovered from unallocated space, and signs of anti-forensic wiping were
observed.

## Key findings
- File carving recovered 42 JPEG images and one XLSX from unallocated clusters.
- Filesystem metadata for the originals had been overwritten, but file content survived.
- A wiping utility had been run, zeroing the directory entries but not all data clusters.
- Timestamps on recovered content predated the reported wipe by several days.

## Indicators
- Recovered artifacts: 42 x JPEG, 1 x XLSX (from unallocated space)
- Anti-forensic tool signature: bulk directory-entry zeroing
- Verification: image SHA-256 matched the acquisition log

## Conclusion
The evidence supports an attempt to destroy files by wiping directory entries, which did not
fully remove the underlying data. Carving recovered usable content. The recovered spreadsheet
should be compared by hash against known case files.

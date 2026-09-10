# Occupied support risk audit

> 歷史紀錄，非目前待辦；現況見 [專案狀態](../publication-preparation.md)。

Goal: assess whether low frame support identifies only spurious obstacles, using
the already authorized cached-depth forensic workflow. No inference, filtering,
new thresholds, route changes or held-out performance claims.

Implementation: extend depth_audit with exact supporting-frame-count groups over
ALL learned occupied cells, cross-counting baseline free/occupied/unknown and
full-source oracle free/occupied. Rebuild the existing oracle from the same scene
and verify scene identity, bounds and shape before evaluation. Oracle rasterization
is a discretized reference, not physical ground truth or clinical evidence.

Alternatives: immediately filter single-frame cells would require new development
experiments and could discard real obstacles; inspect only baseline disagreements
would omit correct learned obstacles. Use all occupied cells and exact groups first.

- [x] Add regression cases for real obstacle with one-frame support, spurious cell
  with repeated support, unknown baseline, empty denominator and invalid oracle.
- [x] Implement counts and explicit denominators; preserve exact occupied-union check.
- [x] Extend existing JSON/HTML/Markdown report; record oracle/source hashes.
- [x] Generate with cached observations, inspect browser, run Python/Node tests,
  update verification/source bundle and commit locally.

Acceptance: group totals equal selected occupied count; single-frame oracle
occupied fraction uses all single-frame occupied cells as denominator (null if zero).
This is an exploratory cell-level overlap statistic, never a false-release rate.

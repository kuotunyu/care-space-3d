# Method disagreement diagnostics

> 歷史紀錄，非目前待辦；現況見 [專案狀態](../publication-preparation.md)。

User authorization: continue improving the delivered workbench; routine engineering
choices are delegated. This is a bounded addition to the existing comparison workflow.

Design: use reconstructed grids only. DA3 all/interval compares to RGB-D all/interval
with identical selected-frame IDs; RGB-D sampling compares to RGB-D all and explicitly
declares the different observation budget. No oracle mesh or truth alignment enters
the diagnostic. A baseline disagreement is not a ground-truth error. The existing
planner thresholds and evaluation queries remain frozen.

Alternatives: a second full 3D viewport duplicates rendering and obscures spatial
correspondence; model retraining is premature. Choose one opt-in difference overlay,
endpoint/path explanation and a deterministic report from the same JavaScript logic.

Implementation:
- Extract the existing footprint state lookup to planning.js, with unchanged geometry.
- Add diagnostics.js: validate grids, three-state transition matrix, evidence loss/gain,
  known occupancy conflict, endpoint states and selected-method constraints along a
  baseline known-free path. No free path means no path-local denominator.
- Add analytical regression tests (unknown is not obstacle disagreement, missing data
  rejected, zero denominators, boundary/blocked endpoints, same-frame pairing).
- Integrate an opt-in overlay and compact diagnostic panel. Hide the regular floor
  colors in this mode and provide a dedicated legend; status still uses the selected
  reconstruction. Recompute on case/method/query/radius changes, never reuse stale data.
- Add a Node report command sharing the exact browser computation. Record study SHA256,
  runtime/code fingerprint and explicit denominators; retain negative results.
- Verify existing 15 decisions, altered query, unavailable baseline, and overlay source
  distinction. Run Node/Python checks, review the diff, update source-only Colab bundle.

Stop: ship this diagnostic workflow. No new model, dataset, GPU job, dependencies,
threshold tuning, GitHub operation or public deployment.

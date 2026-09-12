# Single-frame occupancy abstention experiment

> 歷史計畫，非目前待辦；實驗已完成，結果見 [單影格障礙降為未知實驗](abstention.md)，第一版完成狀態見 [專案狀態](publication-preparation.md)。

User-authorized bounded continuation. Hypothesis: treating single-frame occupied
columns as unknown can reduce unsupported blocked decisions at a cost in decision
coverage. It cannot create new observed-free routes: the free set is unchanged.

Fixed rule before this experiment runs: exactly one distinct selected frame with
an occupied endpoint in an XZ column changes occupied to unknown. Two or more stays
occupied. All original free/unknown cells remain unchanged. No configurable sweep.
This is column-level evidence, not same-surface multi-view geometric consistency.

This hypothesis was motivated by already inspected evaluation scenes. Results must
be labeled exploratory reuse, not untouched held-out validation. Do not tune it on
the results. Analytic development tests run before cached evaluation. No new model
inference or GPU work, no source-geometry inputs to the transformation.

Implementation:
- `src/carespace/abstention.py`: predicted camera-Z endpoints, unique frame support,
  exact stored occupied-union check and copied-grid occupied-to-unknown transform.
  Inputs are predicted depth, calibration, known poses and existing reconstructed grid.
- `tests/test_abstention.py`: synthetic wall blocked-to-unknown; free-set invariance,
  invalid/duplicate evidence rejection and false obstacle remaining with two frames.
- `scripts/run_abstention.py`: cached NPZ/metadata validation, method pairing for all
  and interval frames, original/proposed metrics and oracle labels evaluation-only.
  Save independent JSON + HTML/Markdown report, input/source hashes, failures, runtime.
  Keep study.json, baseline fusion and viewer's official method list unchanged.
- Verify tests, exact endpoint unions, coverage/false-release denominators and browser;
  update README/Colab bundle and commit locally.

Acceptance: retained failures count separately, no free-cell changes, no new passable
queries, no GT-derived masks. A blocked-to-unknown change is abstention, not successful
reconstruction. Unknown requires more evidence; do not recommend acquiring user data.

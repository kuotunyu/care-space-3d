# Scientific correctness review — 2026-09-10

> 歷史紀錄，非目前待辦；現況見 [專案狀態](../publication-preparation.md)。

Read-only source review of the first local MVP; only this report was added. Scope: contracts, synthesis, fusion, oracle/planning, learned adapter, study runner, configuration, tests and current study artifact. Viewer excluded. No GPU inference, environment changes, optional models or medical-standard expansion.

Validation: `.venv/Scripts/python.exe -m pytest -q` passed **9 tests in 11.20 s**. The findings below include failure cases not exercised by those tests. Priorities are relative to the stated conservative geometry and reproducible-study contract; they do not imply that every issue occurred in the saved six cases.

## P1 — A single depth sample certifies unobserved voxel volume

`src/carespace/fusion.py`, `reconstruct`, selects the nearest projected pixel for each voxel center and checks only its depth. The distance margin addresses depth uncertainty but does not establish that the voxel's projected extent has valid, consistent observed depth. At silhouettes, invalid-pixel boundaries or undersampled views this expands a single ray into free volume, contrary to the full-volume observed-free claim.

Verified counterexample: a 5×5 depth image with only `depth[2,2]=10`, K with fx=fy=.01 and cx=cy=2, camera `look_at([1,.6,0],[1,.6,2])`, bounds `[0,0,2,3]`, resolution .1 and height 1.2 yields **580 of 600 free columns**. This is an extreme but currently accepted camera calibration, exposing the missing sampling condition. A normal-focal silhouette regression should also be added.

Minimal fix: require valid conservative depth over the projected voxel footprint and retain unknown for invalid/out-of-view coverage; explicitly reject unsupported undersampling. Until implemented, describe this as a voxel-center approximation rather than a swept-volume guarantee. Preserve the counterexample as a test.

## P1 — Invalid height produces free space without observations

`src/carespace/fusion.py`, `volume_centers` and `reconstruct`: heights at or below the first analyzed center produce zero Y cells. `free.reshape(shape).all(axis=2)` is then vacuously true. Verified `reconstruct([], [0,0,1,1], .1, .1, 's')` returns exclusively free cells.

Minimal fix: validate finite positive bounds/resolution and supported height, require at least one analyzed height cell, and cover the complete requested interval above the documented floor tolerance, including a partial top layer. Add zero-observation/invalid-height and overhang tests. The default 1.20 m run is not the reproducer.

## P1 — Failed learned frames can shift observations and metrics

`scripts/run_learning.py:52–61`: results are appended before the formatted MAE log. An all-invalid prediction has MAE `None`; formatting it as `.3f` raises, then the exception branch appends a second zero-depth observation. Subsequent frame positions shift and selected IDs refer to the wrong frames. Other failures compact `timings` and `errors`, but line 71 indexes timings using original frame IDs. Invalid observations can also leave pre-appended metrics behind. `len(errors)==0` is not a reliable reconstruction-failure indicator.

Minimal fix: maintain exactly one record per requested frame ID containing observation, error, validity and timing; validate before storing; format null safely. Index every selection through those records. Record attempted, failed and selected counts explicitly. Add injected failure at a middle frame and all-invalid prediction tests; no real model run is needed for these tests.

## P2 — All/interval depth metrics and resumed runtime are mislabeled

`scripts/run_learning.py:68–77` computes both methods' MAE/AbsRel from all candidate errors and failure fraction from all candidates, although `observation_count` is the selected count. Current saved normal and blocked cases have exactly identical all/interval MAE values (.304559 and .373503 m respectively), reflecting that implementation. `valid_depth_fraction` is calculated but discarded. Frame means also conceal differing valid-pixel denominators. On cache reuse, method `runtime_seconds` sums historical inference durations while execution wall time measures the resumed invocation; no cache-hit distinction explains the difference.

Minimal fix: report selected-frame pixel-weighted errors with valid/reference pixel counts, selected failure fraction and a separately named candidate-wide metric if useful. Keep all requested observations in failure denominators. Separate original inference compute seconds, cache hits/misses and current wall seconds. Add learned clearance error when both reference and reconstructed clearances exist, as promised by the design.

## P2 — Recorded fingerprints are not enforced end-to-end

`scripts/run_learning.py:24–34` loads current config but never verifies its hash against the study; it checks scene ID but not the frame's saved observation SHA. A changed RGB/depth/K/pose under the same scene ID is accepted while old baseline/oracle results remain. Prediction keys contain array bytes but not shape/dtype: verified zero RGB arrays of shapes `(2,6,3)` and `(3,4,3)` produce the same key with equal K. The shape check prevents one wrong-shaped prediction from being used, but instead creates an avoidable cache failure. Renderer/code changes also have no observation-cache revision.

Minimal fix: verify configuration and observation digests before learning, hash shape/dtype with bytes, and include a small renderer/reconstruction revision in manifests. Refuse stale study inputs with a clear regeneration command. Cache metadata should identify original prediction execution separately from the current run. Preserve failure history across retries rather than overwriting it with an empty successful-run list.

## P2 — Accepted intrinsics exceed the implemented camera model

`src/carespace/contracts.py` permits arbitrary finite 3×3 matrices with positive diagonal focal lengths. `synthesis.camera_rays` assumes zero skew and `[0,0,1]` bottom row, while fusion projects with the entire matrix. Accepted skew/projective matrices therefore give inconsistent projection and backprojection.

Minimal fix: reject nonzero skew/off-model bottom rows for this MVP, or use the same full inverse-K convention in both functions. The default synthetic K is supported. Add a rejection test and explicit degenerate `look_at` validation.

## Checks that support the current design

- Reconstruction and learned prediction APIs do not take source meshes; reference depth enters learned scoring only after prediction. Oracle generation is separate. No ground-truth scale fitting was found.
- The adapter's mean processed focal / 300 conversion agrees with pinned upstream `utils/alignment.py:118–133`; resizing uses adjusted intrinsics before converting to metres.
- Occupied evidence wins; unobserved columns normally remain unknown. The planner tests free connectivity first and occupied-only impossibility second, uses four-connected motion, and treats domain boundaries as occupied.
- Classification includes unknown queries in N and reports both false-release denominators with null for zero predicted passes. Current learned results retain the negative normal-case blockage: 0 passable, 2 blocked, 1 unknown over three evaluation queries; zero false releases is not successful passage recovery.
- Camera placement checks reject interior AABB positions, scene geometry edits change the scene ID, and RGB-D coverage selection explicitly discloses access to all candidate frames. No hidden source-geometry coverage selection was found.
- Evaluation is one programmatic furniture family with related variants. The design appropriately disclaims independent-home generalization. Nine tests are a useful start, but do not currently demonstrate overhang handling, failure resumption or the sampling condition above.

No recommendation here requires a broader framework or additional model. Fix frame accounting and contract validation first; rerun scoring from cached predictions, then regenerate geometry results if the free-evidence rule changes. Keep both original and corrected result provenance.

## Scoped re-review after corrections — 2026-09-10

The preceding findings describe the earlier implementation and are retained as review history. Re-read the changed core, runner, regression tests, README and generated results; independently ran the CPU suite: **19 passed in 1.16 s**. No source/environment changes or GPU work were performed during review.

All six original findings are resolved for the documented fixed local MVP:

1. **Ray evidence:** fusion now traces measured pixel-center rays at half-voxel steps, retains untouched voxels as unknown and gives occupied evidence priority. The single-ray counterexample now produces no free columns. `docs/results.md` explicitly limits the claim to discrete voxel evidence, not measurement of every continuous volume point; this is an appropriate bounded resolution rather than a continuous-space safety guarantee.
2. **Height:** unsupported/nonfinite height is rejected, at least one layer is required and partial top layers are included. New tests cover the original vacuous-free case, an overhang and partial top coverage. Upward height rounding is documented.
3. **Failed frames:** there is one observation append per frame, timing/error records are keyed by frame ID, null MAE is logged safely and selected failure denominators retain failed frames. The injected middle failure plus all-invalid prediction test verifies frame alignment and denominators without loading the real model.
4. **Metrics/runtime:** errors are selected by IDs and weighted by valid pixels; valid/reference pixel counts, selected failure fractions and clearance errors are retained. Original inference compute is identified separately from invocation wall time and cache reuse. Current all/interval MAE values differ as expected: normal .298664/.278937 m, moved-furniture .404659/.372623 m. Sparse shares its single frame and therefore appropriately shares MAE.
5. **Invalidation/cache:** configuration and observation digests are checked, array shape/dtype is hashed, renderer/fusion revisions are recorded, previous nonempty failure logs are archived, and model config has a checksum. The regenerated artifact identifies `observed-rays-half-voxel-v2`. Its recorded execution has 44 cache misses, 5 hits, no failures, CPU float32 and null VRAM; this agrees with the generated report. Upstream checkout status was clean during this review.
6. **Camera contract:** unsupported skew/projective intrinsics and degenerate look-at directions are rejected, with regression coverage.

**No unresolved blocker was found for the reported fixed six-case CPU MVP.** The negative learned normal-case blockage remains visible; RGB-D interval now returns unknown for the normal evaluation case, and the report retains that result. Oracle separation, metric scaling and zero-denominator handling remain intact.

Two small follow-ups remain within the prior accounting/provenance scope, neither affecting the saved successful run:

- `cache_misses` increments after `predict` succeeds, so a failed uncached prediction attempt is absent from hit+miss totals. Move that increment before attempting prediction, or rename it to successful uncached predictions. Individual failures are already retained correctly.
- The new dirty-source guard uses `git diff --quiet`, which checks unstaged tracked changes but misses staged changes. Use `git diff --quiet HEAD --` to compare both index and working tree with the pinned commit. The inspected checkout is currently clean; this is a future provenance edge case.

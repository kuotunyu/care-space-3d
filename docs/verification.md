# Local verification — 2026-09-10

- Python: **19 passed**, covering camera-Z/rigid pose, unknown occlusion, body-radius
  boundaries and gaps, revision rejection, no-valid-depth behavior, empty-height
  prevention, single-ray sampling, skew/degenerate camera rejection, canonical scale,
  shape-aware prediction cache, selected pixel-weighted error, injected middle-frame
  failure/all-invalid prediction, overhang height and partial upper voxel layer.
- Node: **5 passed**: unknown start/goal must not enter a free-only path, incomplete
  coordinates cannot become zero, redraws coalesce and settle, and nested/shared GPU
  resources (including instance buffers) are disposed exactly once.
- Independent scientific review: all six original findings resolved; no blockers for
  documented CPU MVP. Subsequent minor notes fixed: failed cache misses count as
  attempts, and staged as well as unstaged upstream code changes are rejected.
- Browser: all **15 evaluation case/method combinations** matched saved Python
  statuses after correcting unknown-start handling. The three cases are normal,
  moved sofa, and insufficient observations.
- Numeric start X=0.05 m changed normal case to blocked; restoring X=1.25 m restored
  passable. Slider keyboard control changed body radius to 0.70 m and replanned.
- Oracle toggle visibly states complete source geometry is only reference, not
  reconstruction. DA3 frame dialog displayed actual RGB and predicted depth PNG
  (224 pixels wide), with no sensor-depth fallback or incorrect missing message.
- Desktop visual capture checked full-height WebGL canvas, point cloud/occupancy/
  narrow/unknown overlays, method table, frame dialog, labels and color distinctions.
- Browser error console was empty during the 15-method sweep.
- Measured on the local in-app browser: JSON **4,317,806 bytes**, **141.2 ms** from
  viewer module start through fetch, parse, initial scene build and render call.
  This is a local single-run, warm-environment measurement, not a cold-load benchmark,
  frame-rate metric or hardware-independent guarantee.
- Current local server binds only `127.0.0.1:8840`; PID recorded in artifacts/server.json.
- Final study: observed-rays-half-voxel-v2; 44 real fresh DA3 predictions + 5 cache
  hits in the recorded final invocation, no failed frames. CPU float32, 2 threads;
  51.43 s wall time. Per-method durations distinguish cached original compute time.
- Colab notebook parsed and bundled with the shared core; **not executed in Colab**.
  GPU inference was not run because RTX4090 was already heavily occupied.

Raw observations, predictions, study history and environment fingerprints remain in
the local ignored artifacts directory. Data/model download manifests and actual
dependency licenses are retained separately. No remote repository, push or deployment.

## Viewer refinement — 2026-09-10

- Rechecked all 15 evaluation case/method statuses; unchanged from saved Python results.
- Keyboard select-all/backspace leaves a coordinate blank, verdict becomes `待輸入`,
  and remains suspended after blur. Method switch retains edited coordinates. Note:
  this browser driver's `fill('')` did not clear the numeric input; actual keyboard
  deletion was used to verify the user interaction.
- Reference/method switching over three cycles returned to 36 geometries and 2 textures.
  These counters exclude instance buffers; a separate Node dispose-event regression
  covers those buffers. An independent reviewer checked the installed Three.js r174
  release path and found the missing `InstancedMesh.dispose()` call, now fixed.
- Idle redraw count stayed at 3 across independent checks. Active interaction schedules
  renders and damping; there is no permanent animation loop. This is behavior validation,
  not an energy or VRAM benchmark.
- Responsive checks: 390 × 844 and 900 × 900, with a nonzero 3D canvas, no page horizontal
  overflow, and readable comparison rows. Default desktop viewport also visually checked.
  Temporary browser viewport overrides were reset after verification.
- DA3 frame dialog loaded the actual 224-pixel predicted depth; missing-state message
  remained hidden, and browser error console was empty during the interaction sweep.
- Impeccable detector ran once. Its two missing-image-source warnings refer to the closed
  frame dialog: images are assigned real artifact paths before `showModal()`, and missing
  predicted depth hides the image. Its dash warning counts `—` missing-value cells, not
  prose punctuation. These are intentional dynamic/measurement states.
- Independent review also identified coordinate formatting after reading as a boundary
  mismatch. Replanning now preserves typed precision rather than rounding the display.
- No dataset, model, dependency version, reconstruction algorithm or recorded experiment
  was changed during this refinement.

## Pairwise diagnostics — 2026-09-10

- Python: 19 tests passed; Node: 11 tests passed. New tests cover both directions of
  known occupancy conflict, unknown evidence transitions, no free-path denominator,
  alternate routes despite a restricted baseline path, absent states, incompatible
  grid extents, and strict DA3 frame-ID pairing (including different frame order).
- Read-only review checked 329,868 valid-evidence classifier lookups against the prior
  browser implementation. Missing-state fallback, frame-identity validation and bounds
  compatibility issues identified in review are corrected and regression-covered.
- Browser: all 15 evaluation case/method statuses unchanged; RGB-D subsampling explicitly
  labels changed frame subsets, DA3 all/interval pairs with corresponding RGB-D inputs.
- Edited normal start X from 1.25 to 3.25 m: baseline path denominator changed 56→36,
  selected-method constrained-center count 43→23, first restricted center updated.
  Keyboard-cleared coordinate hid the difference overlay and suspended diagnosis.
- The diagnostic action uses top view and hides point-cloud clutter. Switching back to
  RGB-D all disables self-comparison; unknown agreements are explicitly not labeled free.
- Desktop and 390×844 viewport inspected; nonzero canvas, no horizontal page overflow,
  difference legend/source visible, no browser errors. Viewport override reset.
- Node report produced 18 development/evaluation comparisons, 0 failed diagnoses, using
  the same browser module. Report includes study/module/builder hashes and node version;
  unavailable pairings or invalid evidence are retained as diagnostic failures.
- Original study remains byte-identical: SHA256
  `e368c46e4eda63f21eb17214b95a3f6b66ace2117b91a723b6b63d8b2895a4c2`.
  No model inference, threshold tuning, new dependencies or GPU work in this addition.

## Cached depth source audit — 2026-09-10

- Python: 24 tests passed; Node: 11 tests passed with `node --test tests/browser-*.test.mjs`.
  `npm test` is not configured; the direct Node runner is the verified command.
  JavaScript syntax and `git diff --check` passed.
- All 49 cached frames across three evaluation cases were traced without new model
  inference. Each case's occupied endpoint union exactly matched its saved DA3 grid;
  no audit failures. Study SHA256 remained unchanged from the value above.
- Pinned upstream CPU utility checks: focal/300 maximum difference 0 m; camera-Z
  unprojection maximum world-coordinate difference 1.7763568394002505e-15 m.
  No model weights were loaded for these checks.
- Normal-case baseline-free to DA3-occupied conflicts: 1,872 cells. Only 89 had
  exclusively true-floor support; 1,783 had non-floor support. Floor lift alone is
  insufficient to explain the discrepancy. 1,081 conflict cells had occupied endpoint
  support in only one frame; this is descriptive evidence, not a validated removal rule.
- Five audit regressions cover floor/non-floor/no-reference attribution, invalid depth,
  shared-cell contributors, per-frame voting and rejection of incompatible saved masks.
- Review identified an image provenance gap; report pictures now come directly from
  audited arrays, with filenames bound to observation, prediction and source hashes.
  Reference-assisted masks are used only for post-inference reporting.
- Browser report: study fingerprint accepted, all 30 images loaded at native width 224,
  no page horizontal overflow, no browser errors; default viewport visually inspected.
  Report URL was opened directly. Automated navigation via the viewer anchor was not
  confirmed, so this check does not claim click-through navigation coverage.
- Colab launcher includes the same audit builder. The notebook has not been run in Colab.

## Supporting-frame risk extension — 2026-09-10

- Python: 26 passed; Node: 11 passed. New tests first failed on the absent implementation,
  then passed for single-frame true occupancy, repeated spurious occupancy, unknown
  baseline cells, no occupied cells (null fraction), invalid oracle and unchanged inputs.
- Cached audit regenerated across 49 frames, zero failures. All 18 exact support-count
  groups partition their case's learned occupied grid; each group's oracle binary counts
  and baseline ternary counts separately sum to its explicit denominator.
- Oracle rebuilt using existing rasterization, with scene identity/bounds verified and
  shape validated. Oracle int8 grid hashes and scene implementation hash are recorded.
  Duplicate selected frame IDs are rejected to avoid double-counting support.
- Single-frame oracle occupied overlap: normal 199/1308 (15.2%), blocked 137/1299
  (10.5%), sparse 35/222 (15.8%). These exploratory cell overlaps are not route failure
  rates, and the oracle is a discretized reference. No filtering intervention was run.
- Browser: all three grouping tables present, normal denominator/overlap text checked,
  table visually inspected, 30 images loaded, no horizontal page overflow or console errors.
- Original study SHA256 unchanged. No inference, GPU work, threshold selection, new
  dependency or passage-state change. Source bundle regenerated; Colab remains unexecuted.

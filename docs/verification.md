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

## Single-frame occupied-to-unknown experiment — 2026-09-10

- Fixed exactly-one-frame rule documented before executing cached evaluation. Analytic
  tests ran first: blocked wall becomes unknown, original free set unchanged, repeated
  support retained, unknown preserved, stale/mismatched support rejected. Predicted
  endpoint helper has no reference-depth/geometry argument. New tests failed on missing
  implementation, then passed. Full Python 29 passed; Node 11 passed.
- Six evaluation case/method combinations completed, no failures. Distinct selected
  frame IDs checked, source observations and prediction revisions validated; all six
  predicted endpoint unions reproduced their stored DA3 occupied masks exactly.
- All-observation statuses remained blocked/blocked/unknown. Interval normal changed
  blocked to unknown; interval blocked/sparse stayed blocked/unknown. Interval decision
  coverage fell from 2/3 to 1/3. No new passable query; zero predicted-pass denominator
  remains null/not applicable, not a claimed 0% false-release rate among released routes.
- Each output grid and supporting-frame count saved separately with SHA256. Runtime
  separates transform/planning from whole launcher. This was cached CPU work, no new
  inference. Original study remains byte-identical to the SHA256 recorded above.
- Rule was motivated by prior inspection of these scenes: explicitly exploratory
  reuse, not held-out validation. Column support is not same-surface correspondence.
  Negative result retained; default reconstruction/planner/viewer study not replaced.
- Read-only reviewer found no material correctness, information-boundary or accounting
  issues. Browser verified six result rows and four metric rows, matched study fingerprint,
  zero-denominator label, no horizontal overflow or console errors; desktop inspected.
- README and shared Colab launcher updated; notebook/source bundle regenerated locally.
  Colab itself was not executed.

## Report access and source handoff — 2026-09-10

- Added a separate saved-report section in the workbench. It distinguishes stored
  experiment queries from current interactive endpoints and links both forensic and
  abstention reports when their files are available.
- Browser found the center of a wrapped inline report link fell into non-clickable
  line spacing. Links now occupy full rows with padding. Updated stylesheet URL avoids
  reusing the observed stale browser CSS cache. Actual viewer-to-abstention and
  viewer-to-depth-audit navigation both verified, with matching study fingerprint;
  return links also verified. No change to passage methods or recorded results.
- Source ZIP previously omitted tests; it now includes Python and Node tests. Colab
  launcher runs CPU tests after installation and Node tests after npm installation.
- Extracted source to project-local artifacts/handoff-smoke. Confirmed Python module
  imports resolved inside the extracted src directory using PYTHONPATH; all 29 tests
  passed there. Used existing project Python runtime/dependencies, not a fresh venv.
- Installed the locked Three.js dependency in the extracted directory using
  `npm ci --offline --ignore-scripts`; all 11 Node tests and viewer syntax check passed.
  All notebook code cells compiled. No model inference/download or Colab execution.
- ZIP inspection confirmed tests present and data, models, artifacts, third_party,
  .venv, node_modules and .git excluded. Final bundle entries checked against current
  source bytes after documentation/style updates. No publication or remote operation.

## Final local handoff refresh — 2026-09-10

- Refreshed the first-visit viewer changes, 16 px minimum typography, explicit
  endpoint navigation and compact layer explanations. Detailed browser evidence
  and untested cases are in docs/ux/viewer-improvement-acceptance.md.
- Fresh workspace regression: Python 29 passed; Node 14 passed; viewer app syntax
  checked. No model inference, dependency upgrade or research result regeneration.
- Source handoff validation is recorded separately in artifacts/handoff-final/validation.json
  so the ZIP can match final source documentation without embedding its own hash.
- Colab/GPU execution, real touch, 200% zoom and full screen-reader coverage remain
  unverified. This delivery is the local CPU MVP; no publication or remote action.

## Colab CPU execution — user-supplied evidence

User supplied first-cell output: managed Python 3.11.15, pinned CPU dependencies,
29 tests passed in 6.51 s and INSTALL_CHECK_OK. The second-cell report shows
learning_execution wall_seconds=217.514126895, cache_hits=5, cache_misses=44,
failures=[], CPU float32 / 2 threads and null peak VRAM. The evaluation RGB-D all
cases reproduce passable/blocked/unknown; DA3 reproduces blocked/blocked/unknown.
Reported MAE rounds to .299/.279 m normal, .405/.373 m moved, .460 m sparse.
These are pasted execution results, not independent inspection of cloud files.
The 217.51 s value is learning launcher wall time, not whole notebook duration.
At this log-only checkpoint, Colab viewer/browser was still unverified; subsequent
user screenshots confirm loading and three baseline case displays (see below).

The report generator incorrectly embedded historical local GPU occupancy, a claim
that Colab was not executed, and browser verification. Removed those fixed claims;
report now defers to saved execution metadata and separate platform/UI evidence.
This correction changes report text only, not experiment data or inference.

## Colab viewer acceptance and first-version closeout

User screenshots show CareSpace3D_CPU_Reproduction_v1_1.ipynb with the embedded
viewer loaded. Three RGB-D all / reconstruction / radius 0.30 m cases match:

| Case | Displayed status | Observed fraction |
|---|---|---|
| ReplicaCAD furniture, open passage | Passable | 93.3% (earlier screenshot) |
| Sofa moved into passage | Blocked; experiment default | 88.9% |
| Insufficient observations | Unknown; experiment default | 40.2% |

Point cloud, floor states, endpoints, path, frame previews and comparison table are
visible across the screenshots. This verifies displayed states after user-operated
case switching, not every interaction or browser/device combination. Cloud Node
console output was not supplied separately; do not report independently observed
cloud Node test counts. The prior local 14-test result remains local evidence.

Selected screenshots are preserved locally in artifacts/colab-evidence/ with SHA256
manifest.json; originals were supplied in this conversation. They are excluded from
the source ZIP and Git. Cloud artifacts have not been downloaded or substituted for
the local study. The user's cloud report retains old host prose until regenerated
with the corrected generator; numerical results are not changed by that correction.

Current completion: local CPU MVP and user-verified Colab CPU reproduction/display.
Remaining unverified: GPU, real touch, screen reader, 200% zoom and exhaustive cloud
UI/error recovery. Unknown poses and richer body models are future scope. No GitHub
creation, push or public deployment. Earlier unverified notes above describe their
historical checkpoints, superseded only within the evidence scope recorded here.

## Private GitHub handoff — 2026-09-11

User authorized the proposed private repository creation and push. Verified active
GitHub account kuotunyu; the repository lookup returned 404 before creation.
All historical Git object paths were checked for data/models/artifacts/third_party,
environments, images, archives and model arrays; no matching paths were found.
156 historical blobs were scanned for common credential patterns with no hits;
this is a bounded pattern check, not proof of absence of every possible secret.
Created kuotunyu/care-space-3d as private and pushed local work/local-mvp to main.
No dataset, weights, research artifacts or user screenshots were uploaded.
No public deployment or visibility change was performed. Earlier no-remote notes
record the state before this explicitly authorized handoff.

## Public repository publication — 2026-09-11

After the user agreed to the explicit private-to-public proposal, verified local
HEAD and origin/main matched at 51e2385, the worktree was clean, and tracked paths
excluded datasets, models, artifacts and environments. Changed repository visibility
to public. GitHub API confirmed private=false, visibility=public and MIT license.
No Pages/site deployment or dataset/weight upload was performed. Earlier private
status entries are historical, not the current repository visibility.


## Mermaid 技術圖解 — 2026-09-11

README 架構、design.md 三態流程、viewer-contract.md 互動時序各一張，
以各 Markdown 的 Mermaid 區塊為唯一公開圖源。對照 Python pipeline／fusion／planning、
run_learning 及 Viewer app／planning；沒有改動研究或瀏覽器程式。

本機使用 @mermaid-js/mermaid-cli 11.12.0、Mermaid 11.17.2、Puppeteer 23.11.1，
獨立安裝於忽略的 artifacts/mermaid-tooling，使用既有 Chrome 並停用 GPU。
三張皆成功渲染 PNG，檢查文字、分支、箭頭與版面；渲染的 .mmd 與公開 Markdown 區塊逐字一致。
研究環境、Node 執行時相依及 Manim 環境沒有變更。

維護時直接修改 Markdown 裡的圖，不需維護第二份公開圖片或安裝 Viewer 相依。
可使用 Mermaid CLI 的 Markdown 輸入功能做本機預覽，例如：

```powershell
# 已有相同 CLI 環境與 Chrome 設定時，輸出僅作本機預覽。
artifacts/mermaid-tooling/node_modules/.bin/mmdc.cmd -i README.md -o artifacts/diagrams/readme-preview.md -p artifacts/diagrams/puppeteer.json
```

GitHub 原生渲染的版本由平台控制；本機成功不等於所有 GitHub 版本都相容。
使用基本 flowchart／sequenceDiagram，並另行檢查實際 repository 顯示。

# Depth-to-occupancy forensic audit

Continue the user-authorized investigation of the retained DA3 false-blocking case.
Use cached predictions only; no GPU, new checkpoint, retraining, GT scale fit or
evaluation-threshold changes. First verify pinned upstream focal/300 and camera-Z
unprojection, then trace occupied endpoints back to observed pixels and frames.

The audit is explicitly reference-assisted evaluation. Synthetic reference depth and
known camera pose identify true floor hits (world |Y| <= 1e-4 m, numerical tolerance).
Predicted endpoints use exactly the existing fusion rule: depth in (0,20), XZ domain,
height cells beginning at Y=0.10 m with the same outward-rounded upper extent.
Separate support from true-floor pixels, valid non-floor reference pixels, and pixels
without a reference return. Union of all predicted endpoint support must reproduce
the stored learned occupied mask. Reject stale observations or inconsistent masks.

Report signed pixel-depth error, floor depth ratio, observed floor pixels projected
into obstacle height, and unique conflict cells supported by floor/non-floor pixels.
Floor-supported cells can have multiple contributors; report floor-only support
separately. Counts are descriptive attribution, not an intervention or independent
household sample. No error-derived masks enter reconstruction or planning.

Build a compact HTML report with real RGB/reference/predicted depth, signed error and
floor-support masks. Show fixed frame 0, the largest floor-conflict contributor,
and the largest overall conflict contributor
(selection explicitly diagnostic); retain every frame's scores and input hashes in
JSON. Validate report snapshot against study SHA256 before displaying it. Share the
same core with the Colab launcher, update reproducible commands and run tests/review.

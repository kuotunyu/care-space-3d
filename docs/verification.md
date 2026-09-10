# Local verification — 2026-09-10

- Python: **19 passed**, covering camera-Z/rigid pose, unknown occlusion, body-radius
  boundaries and gaps, revision rejection, no-valid-depth behavior, empty-height
  prevention, single-ray sampling, skew/degenerate camera rejection, canonical scale,
  shape-aware prediction cache, selected pixel-weighted error, injected middle-frame
  failure/all-invalid prediction, overhang height and partial upper voxel layer.
- Node: **2 passed**, specifically unknown start/goal must not enter a free-only path.
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

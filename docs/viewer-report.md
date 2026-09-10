# Viewer implementation report

Run `npm ci` once, then `./scripts/serve.ps1` from the project root. Open
`http://127.0.0.1:8840/viewer/`. The static viewer reads `/artifacts/study.json`
and local Three.js 0.174.0; it uses no CDN or external services.

## Interaction and evidence

The center contains the 3D evidence and full-width saved-method comparison. The left
panel selects cases/methods, cylinder radius, endpoints and frame previews; the right
panel explains the current query and observed coverage. Detailed metrics and provenance
are expandable. At small widths the scene and comparison come first.

- Blue-gray points retain the measured/predicted 3D coordinates; neutral color improves
  contrast on the pale canvas. RGB colors remain available in actual frame previews.
- Colored floor cells encode free, occupied and unknown. Obstacle columns are a 0.12 m
  projection, not a recovered obstacle height. Purple narrow bands use fixed radius
  clearance [0.30, 0.60) m to known occupied cells or the padded domain boundary.
- Start/goal letters and circles show endpoint location and the selected body radius.
  The conservative grid margin is additional to the displayed radius.
- Solid paths are known-free routes. Dashed paths are candidates crossing unknown
  evidence, with status and length labeled accordingly. Oracle geometry is opt-in,
  visibly labeled, and has no effect on the planner's selected reconstruction grid.
- Method selection preserves the current endpoint/radius query. The reset button
  restores the stored experiment query. Blank inputs suspend the verdict and clear
  the old path; numeric typing retains its precision across blur/replanning.
- Frame count changes previews/camera markers only. Selected frames have green borders.
  DA3 previews never substitute sensor depth for a missing model prediction.

## Rendering lifecycle

An on-demand scheduler coalesces changes and follows OrbitControls damping to rest.
Visibility changes and resizing request redraws. Switching geometry disposes nested
geometries, materials, textures and per-instance buffers; content revisions reject
and dispose stale asynchronous reference loads. Reference-loading errors retain the
active reconstruction with an explicit source message. No-method cases clear previous
path, markers, metrics and comparison, and disable query controls.

## Validation and scope

See `docs/verification.md` for the actual browser interactions and test results.
The local viewer retains all 15 original evaluation case/method decisions and the
DA3 false-blocking normal-room example. Python geometry/inference and study artifacts
were not changed by the viewer refinement. Rendering remains an evidence inspection
tool, not a recovered watertight mesh or a collision-measurement authority.

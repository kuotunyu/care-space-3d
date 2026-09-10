# CareSpace 3D — first executable study

User-approved direction: controlled synthetic home geometry, finite observations,
three-state passage analysis, one learned depth comparison, local interactive 3D.
Implementation details below are routine choices within that authorization.

## Preflight (2026-09-10)

- Workspace: `D:\AI-Portfolio\CC_github部隊\care-space-3d` (existing empty Codex project).
  Requested `D:\AI-Portfolio\CC\_github部隊\care-space-3d` does not exist. No duplicate created.
- No AGENTS.md found in workspace/ancestor directories. No enclosing Git repository.
- `gh repo view kuotunyu/care-space-3d` cannot resolve repository. No remote creation/push/deploy.
- Other active task: 建立可恢復預約 Agent in its own project. No files touched there.
- RTX 4090: 22135/24564 MiB, 99% busy. CPU only until a new occupancy check permits GPU.
- Ubuntu-bench is running. Do not enter or modify it. Use private Windows Python 3.11 venv.

## Approach and alternatives

Choose a CPU ray renderer, conservative voxel observation fusion, disk configuration-space
planning, and a Three.js viewer. This gives observable geometry and direct failure tests.
Habitat-sim would preserve official simulation semantics but adds a Linux environment;
Splatfacto/gsplat adds appearance reconstruction and CUDA build dependencies without
strengthening collision evidence. Neither is necessary for the first end-to-end result.

Download a small individually addressable ReplicaCAD subset with immutable revision,
actual file hashes/sizes and retained attribution. Inspect assets before choosing scene
placements. Use deterministic analytic room fixtures for exact expected-case tests and
ReplicaCAD furniture in an explicitly programmatic scene for realistic geometry. Never
represent a partial or modified scene as an unchanged official apartment configuration.

## Data and information boundaries

World: metres, right handed, Y up; ground plane XZ. Camera: OpenCV x right, y down,
z forward; K in pixel units; T_world_camera is 4x4 rigid transform. Depth is camera
Z in metres, invalid pixels are zero. RGB, K, poses and revision live in observations.
Full source mesh belongs only to synthesis, oracle evaluation and labeled reference view.
Reconstruction functions accept observation bundles, never source meshes. Learned depth
accepts RGB and calibrated intrinsics only; known synthetic poses are used for fusion.
No ground-truth depth fitting or Umeyama scale fitting in the main learned method.
DA3METRIC-LARGE canonical depth must use the focal conversion verified in upstream code.
Unknown-pose reconstruction is reported unsupported for this monocular metric model,
separately from the known-pose experiment; do not imply measured localization accuracy.

Each scene/observation/result carries a content fingerprint. Furniture edits regenerate
reference geometry and observations; mismatches invalidate results instead of displaying
stale reconstruction. Saved manifests and per-frame predictions support resumption.

## Geometry contract

Straight upright circular cylinder, radius 0.30 m, height 1.20 m; flat known support
plane, no stairs/slopes, no dynamics, no heading-dependent rotation. This is NOT a
complete wheelchair envelope. All results conditional on this model and discretization.
Volume is discretized at 0.10 m initially, with explicit floor tolerance. A column is
free only when all analyzed height cells have observed free evidence. Any observed
obstacle makes it occupied; otherwise unknown. Occupied evidence wins conflicts.
Free evidence is sampled on actual measured rays every 0.05 m, using every second
valid ray; no nearest-pixel voxel-cone filling. A ray-touched cell is discrete evidence,
not a guarantee that every continuous point in that voxel has been directly measured.
The upper height interval rounds outward to the next voxel; below 0.10 m is ignored.
Conservative disk inflation includes voxel half diagonal and path sampling margin.
4-connected planning avoids diagonal corner cutting. Outside domain is impassable.

Known-free connectivity -> passable. No connectivity even allowing unknown -> blocked.
Otherwise -> unknown. Endpoints and swept volume obey the same inflation rules.
Reference oracle is separately built from full geometry under identical body assumptions.
Sub-voxel features and transparent/reflective materials are outside first renderer scope.

## Experiments and acceptance

First show normal, barrier and insufficient-observation fixtures. Then compare baseline
and one actually executed DA3METRIC-LARGE inference, retaining negative results.
Complete observation means all frames in the declared trajectory, NOT omniscience.
Compare all frames, fixed-interval frames and greedy observed coverage selection using
only candidate sensor observations. Record selection scan cost and candidate access.
Development and evaluation fixture families are separately seeded and fixed before
evaluation. ReplicaCAD variants share the same apartment family; no independent-home
generalization claim. Pretraining overlap unknown.

For N requested queries (including unknown): report pass/blocked/unknown proportions,
decision coverage=(pass+blocked)/N, false release count / oracle-blocked count AND
false release count / predicted-pass count; zero denominators -> null. Report oracle
pass/blocked counts, confusion matrix, depth errors, observed free/occupied/unknown
coverage, clearance error where both exist, failed observations/reconstructions,
wall-clock, CPU/GPU mode, peak VRAM (null on CPU) and viewer payload/load timing.
Do not hide failures or tune thresholds on evaluation outcomes.

Tests: metric projection/backprojection, invalid poses/depth, occlusion unknown,
height overhangs, narrow corridor/footprint/boundaries, disconnected blockers, stale
scene rejection, no source-geometry argument in inference, metric-scale conversion,
zero metric denominators. Visually inspect RGB/depth/point-cloud and viewer controls.

## Viewer

Single local workbench: prominent 3D model with reconstruction/unknown/path overlays,
case and method selection, body radius control, start/end selection, camera frames,
furniture before/after selection (regenerated artifacts), and side-by-side numeric
comparison. Muted blue-gray canvas, teal free, coral obstacles, ochre unknown; compact
Chinese copy, clear mode/source labels, keyboard accessible controls. Raw oracle
reference geometry is opt-in and visibly labeled. No medical claims or authentication.

## Completion and limits

Deliver reproducible commands, lockfiles, local viewer, real learned predictions,
tests, failures and attribution. No SAM/VGGT expansion, platform, paid APIs or hosting.
If a specific component is blocked, retain evidence and explicit incomplete status.

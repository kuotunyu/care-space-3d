# CareSpace 3D implementation plan

Goal: execute a small, honest reconstruction and passage study with a local 3D viewer.
Architecture: immutable scene -> observed RGB-D -> voxel states -> 2D swept-cylinder
planner. Full geometry evaluation is a separate branch. Learned depth replaces only
observed depth, preserving identical downstream methods and declared camera inputs.
Stack: Python 3.11, NumPy/SciPy/trimesh CPU; PyTorch CPU DA3; Three.js static viewer.

Global constraints: docs/design.md is authoritative; local only; no GPU while busy;
no modification of Ubuntu-bench; no oracle in inference; unknown must be retained.

- [x] Task 1: bootstrap private environment, immutable source manifest and download.
  Files: pyproject.toml, requirements*.txt, scripts/fetch_assets.py, docs/sources.md.
  Verify actual bytes/hashes/license and load meshes; save visual inspection.
- [x] Task 2: geometry contract, sensor synthesis, fusion, planner and meaningful tests.
  Files: src/carespace/{contracts,scenes,synthesis,fusion,planning}.py; tests/.
  Interfaces: Observation(rgb, depth, K, T_world_camera, scene_id); Grid(states,
  origin, resolution, scene_id); analyze(grid,start,goal,radius)->JSON result.
  First run failing tests for finite cameras, camera-Z projection, unknown occlusion,
  closed barrier, narrow gap, conservative body size and stale revision rejection.
  Then implement and run `.venv/Scripts/python -m pytest -q`.
- [x] Task 3: experiment runner, reference evaluation and static export.
  Files: src/carespace/{evaluation,pipeline}.py, scripts/run_study.py, configs/study.json.
  `python scripts/run_study.py` produces artifacts/study.json and per-case arrays.
  Validate three expected fixtures, all/interval/coverage selection and denominator
  behavior, immutable development/evaluation split and result cache identity.
- [x] Task 4: local viewer (bounded delegated task while core is implemented).
  Files: viewer/index.html, viewer/app.js, viewer/style.css, package*.json.
  Contract: docs/viewer-contract.md; test click/keyboard cases, selectors and overlays.
  Viewer is served only on 127.0.0.1, with locally installed Three.js.
- [x] Task 5: one actual learned method, CPU smoke study and resumable Colab launcher.
  Files: src/carespace/learned.py, scripts/run_learning.py, notebooks/colab.ipynb.
  Pin upstream code/model revision, verify canonical focal scaling against upstream,
  predict RGB-only per frame, record device/timing/errors and preserve failed frames.
  Compare known-pose learned fusion and baseline. Unknown-pose status unsupported.
- [x] Task 6: independent review, targeted fixes, visual verification, README/report.
  Verify fresh test output, served JSON/assets, complete interactive UI, dependency
  licenses, report denominators and failure evidence. Capture browser views and save provenance.
  Deliver local path and commands; no remote actions.

Completed local CPU MVP. Unknown-pose reconstruction and Colab execution were not
performed and are explicitly marked unsupported/unverified; the launcher shares the
same verified CPU core. Independent review and browser parity fixes are documented.

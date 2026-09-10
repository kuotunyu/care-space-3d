# Viewer implementation report

## Run

From the repository root:

```powershell
npm install
npm run serve
```

Open `http://localhost:8000/viewer/`. The viewer fetches `/artifacts/study.json` and imports Three.js 0.174.0 from the local `node_modules` directory. It uses no CDN, framework, backend, or deployment service.

## Implemented checks

- Schema version, missing artifact, empty cases, empty methods, optional frames, optional metrics, and absent reference meshes have explicit states.
- Case and method changes rebuild the visualization without changing saved geometry.
- Grid indexing follows flattened x-major `ix * nz + iz` states.
- Browser replanning uses the specified `radius + sqrt(2) * resolution` disk threshold, blocks out-of-domain footprints, propagates unknown cells, runs free-only then free-plus-unknown four-neighbor BFS, and estimates path clearance against known obstacles and boundaries with a half-cell diagonal deduction.
- Endpoints support numeric input, ground clicks, and keyboard arrows after focusing the 3D viewport.
- Oracle GLB display is opt-in, wireframed, and labeled as full source geometry rather than reconstruction.

## Validation

Run `npm install` to verify the lockfile and exact Three.js version. Serve the complete repository over HTTP; opening the HTML directly cannot resolve the absolute artifact and module paths. Browser interaction should be checked against a real generated `artifacts/study.json`, including RGB paths, point colors, reference mesh orientation, endpoint classification, and responsive layouts.

## Concerns

- Real `artifacts/study.json` was structurally checked: six cases, three methods per case, and every first-method state array matched `shape[0] * shape[1]`. The subagent browser surface could not open localhost, so final visual capture remains to be performed from the parent task or a normal local browser.
- WebGL line width is commonly fixed at one pixel. The path remains differentiated by color and endpoint markers.
- Observation count changes the visible RGB/depth preview pairs and camera-position markers. It does not recompute persisted method states; generating a different reconstruction remains an artifact-generation task.

## Browser review fixes

- The viewport now fills the complete center stage instead of inheriting the canvas default height of 150 px.
- Clearance treats unknown and occupied cells as evidence limits and measures boundaries against Python's padded grid centers before subtracting the half-cell diagonal.
- DA3 methods use `learned_depth_preview` and label it as predicted depth; RGB-D methods label `depth_preview` as sensor depth.
- A compact per-case comparison exposes status, selected-frame count, observed coverage, runtime, and depth MAE. ReplicaCAD normal is the initial case.

## Final product pass

- A purple `0.30–0.60 m` narrow-band overlay uses fixed center-to-known-obstacle or padded-boundary clearance after the cell half-diagonal deduction. Its labels state that it is a radius-clearance visualization rather than a clinical threshold.
- Frame thumbnails open an accessible native dialog with large RGB and method-specific depth images. DA3 missing predictions display an unavailable state and never substitute sensor depth.
- Endpoint fields have complete accessible names and recover safely from non-finite input. The saved-method comparison is labeled as using original endpoints and the default radius.
- Initial fetch, JSON parse, scene construction, and explicit first render duration is recorded in `document.body.dataset.viewerReadyMs`; payload size is recorded in `document.body.dataset.studyBytes` using `Content-Length` or UTF-8 text length.

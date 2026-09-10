# Viewer artifact contract v1

Fetch `/artifacts/study.json`. Top level: {schema_version:1, body:{radius:0.3,
height:1.2, assumption:string}, cases:[Case], learning_status:string}.
Case: {id, title, description, split, family, scene_id, bounds:[xmin,zmin,xmax,zmax],
resolution:0.1, shape:[nx,nz], reference_mesh:string|null, methods:[Method], frames:[Frame]}.
Method: {id, label, states:number[] (flattened x-major nx*nz, -1 unknown/0 free/1 occupied),
points: {positions:number[] (xyz), colors:number[] (rgb 0..1)}, selected_frames:number[],
result: {status:'passable'|'blocked'|'unknown', path:[[x,z],...], start:[x,z],goal:[x,z],
clearance_m:number|null, reason:string}, metrics:object}.
Frame: {rgb:string,depth_preview:string,position:[x,y,z],id:number}.
Reference mesh is GLB opt-in, full source geometry, NEVER labeled reconstruction.
Grid lies at y=0.02, Y up. Draw unknown visibly. Method points represent observed surfaces.

Implement browser replan from states for endpoints/radius: any occupied footprint cell
blocks, any unknown footprint cell makes center unknown; pad outside as blocked; disk
threshold radius+sqrt(2)*resolution (same conservative margin as Python). Four-neighbor
BFS path in free, then optimistic free+unknown. Path clearance is nearest non-free cell
(unknown or occupied) or padded boundary distance minus half-cell diagonal.
Start/end click controls plus numeric fields/keyboard. Before/after is case selection,
never move geometry without regenerating artifacts. Static persisted cases are sufficient.
All files local; dependency three==0.174.0 npm; no CDN, servers, frameworks or deployment.
Palette: #eaf0f4 canvas, #152f43 ink, #117d83 free, #d66750 obstacle, #c19b43 unknown,
#ffffff panels. Type: system UI/Microsoft JhengHei and monospace measurements.
Chinese UI, compact professional spatial research tool, centerpiece 3D, no marketing hero.
Show radius/height assumptions and known-pose mode, reconstructed vs oracle clearly.
Show all metrics available, optional frames, mode and observation count controls.
Loading/error/empty states, labels, focus styles, responsive; capture UI after real data.

Final UI: obstacle grid is shown as 0.12 m projection columns, not reconstructed
height. Points preserve observed surface coordinates; purple narrow bands mean fixed
radius clearance [0.30,0.60) m to known obstacles/boundary, unrelated to clinical rules.
Frame dialog uses learned_depth_preview only for DA3, and declares missing outputs.
Browser BFS checks start/goal admissibility before exploring; unknown candidate paths
are colored unknown and never described as a passable path. Saved comparison rows
retain original experiment endpoints/radius; interactive replan is separately labeled.

Refinement: neutral blue-gray point display improves contrast without changing point
coordinates; sensor RGB remains in frame previews and artifact colors. Unknown candidate
paths are dashed and their lengths explicitly labeled candidate lengths. Endpoint circles
show the chosen radius (the extra planner discretization margin is not drawn). Typed
coordinates retain their precision; blank/non-finite coordinates suspend the verdict.
Method switches retain the current query; case changes reset endpoints, and the explicit
reset action restores endpoints plus study radius. Reference mode overlays geometry but
the active method's reconstruction grid remains the only browser-planning input.
Three.js redraws on changes/resizes and while OrbitControls damping settles, then stops.
Stale GLTF callbacks are invalidated by content revision and dispose their whole hierarchy.

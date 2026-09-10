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
BFS path in free, then optimistic free+unknown. Path clearance is nearest known obstacle
or boundary distance minus half-cell diagonal, limited to observed evidence.
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

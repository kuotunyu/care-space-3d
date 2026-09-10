# Retained development failures

- Bootstrap: editable install attempted before `src/` existed; fixed by creating the
  declared package. No global environment changes.
- First sensor visual inspection: camera 0 at (1,0.65,1) lay inside the sofa in the
  programmatic ReplicaCAD furniture room. RGB showed an interior triangle close-up.
  This acquisition was invalid; changed camera placement to a clear aisle, added an
  AABB camera placement guard, and regenerated affected observations and results.
  This is a data-generation correction, not threshold fitting to evaluation labels.
- Projection warning: behind-camera voxel projections overflowed Windows integer
  conversion. Only positive camera-Z points are eligible for evidence; use a harmless
  denominator for ineligible points before integer projection. Geometry tests pass.
- DA3 first launch: transitive InputProcessor import requires `imageio` through
  `parallel_utils`. Retained initialization failure and added pinned dependency.

Experimental negative results and classification counts are in `artifacts/study.json`
and the generated report. Runtime frame failures are recorded by run_learning.py.

- Independent review: nearest-pixel projective carving allowed a single valid ray to
  declare a whole pixel cone free. Preserved failing regression, replaced it with
  actual observed-ray sampling at half-voxel steps, regenerated all results. This
  remains discrete occupancy evidence, not a proof for every continuous volume point.
- Height validation: an empty height axis could make `all()` vacuously true. Reject
  unsupported heights and include a partial top layer; zero-observation test retained.
- Learned accounting: selected subsets previously shared all-frame MAE. Now use
  selected-frame pixel-weighted errors, count invalid/failed frames explicitly, and
  preserve a single observation slot when inference fails. Injected failure test
  checks middle-frame failure plus all-invalid frame without invoking a real model.
- Browser parity validation: the first JavaScript BFS could start in an unknown
  cell and enter neighboring free cells, disagreeing with Python. Extracted the
  connectivity primitive and added two endpoint-evidence regression tests. All 15
  evaluation case/method combinations now match the Python persisted status.
- Frame dialog: a CSS display rule overrode the native `hidden` attribute and showed
  an unavailable message alongside valid DA3 preview. The hidden rule is now explicit.

# Source and license record

## ReplicaCAD subset

- [Official dataset page](https://aihabitat.org/datasets/replica_cad/).
- [Pinned files](https://huggingface.co/datasets/ai-habitat/ReplicaCAD_dataset/tree/3e8c7fe5759f64bfcbc3882f9cdf6de97f82a06d).
- Revision `3e8c7fe5759f64bfcbc3882f9cdf6de97f82a06d`.
- Whole interactive repository file listing: **157,450,746 bytes**, not downloaded.
- Actual selected 14 files: **8,667,421 bytes**; every URL/size/SHA256 is in
  `docs/asset-manifest.json`. Includes empty stage (inspected, not used in the main
  controlled room), sofa/chair/table and their collision assets/configurations.
- The official webpage and HF card say **CC BY 4.0**, but the downloaded
  [LICENSE.txt](https://huggingface.co/datasets/ai-habitat/ReplicaCAD_dataset/blob/3e8c7fe5759f64bfcbc3882f9cdf6de97f82a06d/LICENSE.txt)
  says **CC BY-NC 4.0**. This conflict remains unresolved. This local work observes
  the stricter noncommercial condition and does not distribute the dataset.
- Attribution: Copyright Facebook, Inc. and its affiliates; ReplicaCAD from AI Habitat.
  Modifications: original-scale furniture translated/rotated in a programmatic room,
  recolored for the CPU renderer; RGB-D and voxel results are derived outputs.
  Not an unchanged official apartment layout and not a real long-term-care facility.
- No original Habitat navmeshes are used as passage truth. Collision assets were
  inspected/downloaded; reference evaluation uses the same full render triangles as
  sensor synthesis, rasterized independently under our declared cylinder model.

## Learned model

- [Official DA3 code](https://github.com/ByteDance-Seed/Depth-Anything-3/tree/3d835ec1a5802d64a8b8b15f817a1ab54809bfe4), revision `3d835ec1a5802d64a8b8b15f817a1ab54809bfe4`, Apache-2.0.
- [DA3METRIC-LARGE checkpoint](https://huggingface.co/depth-anything/DA3METRIC-LARGE/tree/4010e39f3634a45bc60553321fb49fb760bd594e), revision `4010e39f3634a45bc60553321fb49fb760bd594e`, Apache-2.0.
- Actual weight **1,336,734,448 bytes**, SHA256 `bbea5b0b3ee389849cffa7ddae89de064a90abd2b055fc5aa99aac68db324776`.
- Only this checkpoint downloaded. BASE is relative-depth/pose-capable Apache-2.0;
  selected Metric-Large is monocular metric, no pose estimation. Giant/Large/Nested
  `-1.1` models have different capabilities and CC BY-NC terms. The refreshed weights
  replace their corresponding deprecated large models; that does not make BASE or
  Metric-Large equivalent to them. See the official model table, not name inference.
- See `docs/da3-audit.md` for the checked focal/300 conversion and source code.
  No GT depth alignment. Known simulated intrinsics and poses are an experimental
  input assumption; unknown-pose reconstruction is explicitly unsupported here.
- Pretraining overlap with related synthetic data is unknown. No unseen-home claim.

## Runtime and viewer

Direct dependencies are pinned in `pyproject.toml`, the complete actually installed
CPU environment in `requirements-cpu.lock`, with metadata, license-file texts and
hashes in `docs/dependency-provenance.json`. Missing metadata is left missing, not
converted into a guessed license. Upstream license files remain in installed wheels.

- NumPy 1.26.4 / SciPy 1.15.2: BSD; trimesh 4.6.8 / rtree 1.4.0: MIT.
- embreex 2.17.7.post6: bundled license recorded; CPU Embree intersection.
- Pillow 11.1.0: MIT-CMU. PyTorch 2.6.0+cpu / torchvision 0.21.0+cpu: BSD.
- OpenCV Python 4.11.0.86: Apache-2.0; all wheel third-party notices retained.
- [Three.js 0.174.0](https://github.com/mrdoob/three.js/tree/r174): MIT, npm exact lock.

Splatfacto/gsplat was evaluated as an alternative appearance pipeline, not installed.
The [official Splatfacto documentation](https://docs.nerf.studio/nerfology/methods/splat.html)
does not turn appearance Gaussians into collision evidence; the small Three.js viewer
meets this version's display need without an additional CUDA training environment.

The root MIT license applies to original project work, not third-party data/weights.
See ../THIRD_PARTY_NOTICES.md. The private GitHub repository was created and pushed
with user authorization on 2026-09-11. No public deployment or paid inference service
was used.

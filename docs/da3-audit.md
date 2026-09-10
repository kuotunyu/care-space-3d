# DA3Metric-Large pinned integration audit

Audited sources:

- Official code: ByteDance-Seed/Depth-Anything-3 at `3d835ec1a5802d64a8b8b15f817a1ab54809bfe4` ([tree](https://github.com/ByteDance-Seed/Depth-Anything-3/tree/3d835ec1a5802d64a8b8b15f817a1ab54809bfe4)).
- Official checkpoint: `depth-anything/DA3METRIC-LARGE` at `4010e39f3634a45bc60553321fb49fb760bd594e` ([files](https://huggingface.co/depth-anything/DA3METRIC-LARGE/tree/4010e39f3634a45bc60553321fb49fb760bd594e)).

## Canonical depth to metres

The exact conversion is:

```python
focal_px = (K_processed[0, 0] + K_processed[1, 1]) / 2.0
depth_m = output.depth * (focal_px / 300.0)
```

This is the implementation of [`apply_metric_scaling`](https://github.com/ByteDance-Seed/Depth-Anything-3/blob/3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src/depth_anything_3/utils/alignment.py), whose default `scale_factor` is the canonical focal length `300.0`. The pinned repository README FAQ states the same formula explicitly: `metric_depth = focal * net_output / 300.` The HF card's phrase “multiplying by focal length” is incomplete if read literally; the `/ 300` is required. Use the focal length in **pixels at the processed image resolution**, averaged from processed `fx` and `fy`. Do not fit a scale to scene or dataset ground truth.

`DA3METRIC-LARGE` is the standalone metric branch. Its config has no camera encoder/decoder, so passing `K` to the network does not condition its prediction. `K` is used after forward only for the canonical conversion above.

## Preprocessing at `process_res=224`

Use the pinned official [`InputProcessor`](https://github.com/ByteDance-Seed/Depth-Anything-3/blob/3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src/depth_anything_3/utils/io/input_processor.py) with `process_res_method="upper_bound_resize"` and pass the original `K` into it. It performs, in order:

1. RGB conversion.
2. Aspect-preserving resize so the longest side is 224.
3. A small second resize that rounds each dimension to the nearest multiple of patch size 14 (224 itself is already divisible by 14).
4. Matching row-wise updates to `K`: scale row 0 by `new_width / old_width`, row 1 by `new_height / old_height`, at both resize stages.
5. `ToTensor()` to `[0,1]`, then ImageNet normalization with mean `(0.485, 0.456, 0.406)` and std `(0.229, 0.224, 0.225)`.

This path introduces no crop, so there is no principal-point crop-offset mismatch. Do not resize the image independently and then reuse the original `K`, and do not pre-scale `K` before passing it to `InputProcessor`. For a batch with different resulting shapes the processor later center-crops all items to the minimum height/width and adjusts `cx,cy`; prefer single-image calls (the metric model is monocular) to avoid that batch-unification crop entirely.

The processor returns image data as `(N,3,H,W)` despite an inaccurate docstring claiming `(1,N,3,H,W)`; add exactly one leading batch dimension before direct model forward.

## Minimal CPU direct-forward path

Avoid `depth_anything_3.api`: it imports output/export machinery and thereby pulls unrelated geometry/export dependencies. Instantiate the core network from the checkpoint's embedded config and load the core state after removing the API wrapper's `model.` prefix.

Required packages for this path are `torch`, `torchvision`, `numpy<2`, `opencv-python`, `Pillow`, `omegaconf`, `addict`, `einops`, `safetensors`, and `huggingface_hub`. `xformers` is optional: the pinned DINO code catches its absence and uses its local PyTorch `SwiGLUFFN`. `gsplat`, `open3d`, `trimesh`, Gradio/app packages, FastAPI, COLMAP, and the repository's broad full dependency set are not needed for this metric-only direct forward.

```python
import json

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from omegaconf import OmegaConf
from safetensors.torch import load_file

from depth_anything_3.cfg import create_object
from depth_anything_3.utils.io.input_processor import InputProcessor

REPO = "depth-anything/DA3METRIC-LARGE"
REV = "4010e39f3634a45bc60553321fb49fb760bd594e"

config_path = hf_hub_download(REPO, "config.json", revision=REV)
weights_path = hf_hub_download(REPO, "model.safetensors", revision=REV)
with open(config_path, encoding="utf-8") as f:
    hub_config = json.load(f)

net = create_object(OmegaConf.create(hub_config["config"]))
wrapped_state = load_file(weights_path, device="cpu")
core_state = {
    key.removeprefix("model."): value
    for key, value in wrapped_state.items()
}
net.load_state_dict(core_state, strict=True)
net.eval().to("cpu")

# rgb may be a PIL image, an RGB uint8 HxWx3 ndarray, or a path.
# K_original is float32 3x3 in pixels at the original image size.
processor = InputProcessor()
images_nchw, _, K_processed = processor(
    image=[rgb],
    intrinsics=np.asarray([K_original], dtype=np.float32),
    process_res=224,
    process_res_method="upper_bound_resize",
    num_workers=1,
    sequential=True,
)

x = images_nchw.unsqueeze(0).to("cpu")  # (B=1,N=1,3,H,W)
with torch.inference_mode():
    output = net(x)                       # no K/E: metric net has no camera encoder

raw_depth = output.depth[0, 0].float()   # processed HxW
Kp = K_processed[0].float()
focal_px = (Kp[0, 0] + Kp[1, 1]) * 0.5
depth_m = raw_depth * (focal_px / 300.0)
```

Do not wrap CPU forward in the API's CUDA-oriented autocast selection. Plain float32 is the least surprising CPU path. The core forward also applies the metric model's sky postprocessing: pixels classified as sky are replaced with the non-sky 99th-percentile depth before the focal conversion.

## Checkpoint identity and bytes

At the pinned HF revision the canonical filenames are exactly `config.json` and `model.safetensors`; the repository contains only those plus `README.md` and `.gitattributes`. `config.json` names `da3metric-large` and embeds a `DepthAnything3Net` with ViT-L backbone (`vitl`, layers 4/11/17/23) and a one-channel DPT depth head with sky head defaults.

The weight response was checked as real safetensors bytes, not a Git-LFS/Xet pointer:

- HTTP range response: `206`, `Content-Range: bytes 0-262143/1336734448`.
- Exact linked size: **1,336,734,448 bytes**.
- Linked SHA-256/ETag: `bbea5b0b3ee389849cffa7ddae89de064a90abd2b055fc5aa99aac68db324776`.
- First eight bytes decode to safetensors header length `48,864`; the following bytes begin valid JSON, and the header contains 406 tensor entries.
- HF metadata reports 334,171,394 float32 parameters.

Both the code files and model card declare **Apache-2.0** for this metric checkpoint/model. The general DA3 repository table assigns other licenses to some larger models, but `DA3METRIC-LARGE` is specifically Apache-2.0.

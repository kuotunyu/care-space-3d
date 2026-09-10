"""Pinned DA3 metric-only CPU adapter. API has no ground-truth depth or mesh argument."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
CODE_REV="3d835ec1a5802d64a8b8b15f817a1ab54809bfe4"
MODEL_REV="4010e39f3634a45bc60553321fb49fb760bd594e"
WEIGHT_SHA="bbea5b0b3ee389849cffa7ddae89de064a90abd2b055fc5aa99aac68db324776"
CONFIG_SHA="a336f3e76fe375aaae17a9aed9130c9f2aa061535d317ec57dcb2f1f02e1dd53"
ADAPTER_REV="metric-focal300-fp32-r224-v1"

def metric_scale(raw_depth,K):
    return raw_depth*((float(K[0,0])+float(K[1,1]))/2/300.)

def prediction_key(rgb,K):
    h=hashlib.sha256((CODE_REV+MODEL_REV+ADAPTER_REV).encode())
    for a in (rgb,K):
        a=np.asarray(a)
        h.update(str((a.shape,a.dtype.str)).encode());h.update(a.tobytes())
    return h.hexdigest()

class MetricDepth:
    def __init__(self,device="cpu",threads=2):
        import subprocess
        import torch
        from omegaconf import OmegaConf
        from safetensors.torch import load_file
        if device!="cpu":
            raise ValueError("This verified local launcher is CPU-only; use an isolated validated GPU environment for GPU experiments")
        self.device=device
        source=ROOT/"third_party/Depth-Anything-3"
        actual=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
        if actual!=CODE_REV:raise ValueError("DA3 source revision mismatch")
        if subprocess.run(["git","-C",str(source),"diff","--quiet","HEAD","--"]).returncode:
            raise ValueError("DA3 source contains unrecorded modifications")
        weights=ROOT/"models/DA3METRIC-LARGE/model.safetensors"
        with weights.open("rb") as stream:
            if hashlib.file_digest(stream,"sha256").hexdigest()!=WEIGHT_SHA:raise ValueError("Checkpoint checksum mismatch")
        if hashlib.sha256((weights.parent/"config.json").read_bytes()).hexdigest()!=CONFIG_SHA:
            raise ValueError("Checkpoint configuration checksum mismatch")
        sys.path.insert(0,str(source/"src"))
        from depth_anything_3.cfg import create_object
        from depth_anything_3.utils.io.input_processor import InputProcessor
        torch.set_num_threads(threads)
        config=json.loads((weights.parent/"config.json").read_text())
        self.model=create_object(OmegaConf.create(config["config"]))
        state=load_file(weights,device="cpu")
        self.model.load_state_dict({k.removeprefix("model."):v for k,v in state.items()},strict=True)
        self.model.eval().to(device)
        self.processor=InputProcessor()

    def predict(self,rgb,K):
        import torch
        from PIL import Image
        start=time.perf_counter()
        images,_,intrinsics=self.processor(image=[rgb],intrinsics=np.asarray([K],np.float32),
            process_res=224,process_res_method="upper_bound_resize",num_workers=1,sequential=True)
        with torch.inference_mode():out=self.model(images.unsqueeze(0).to(self.device))
        raw=out.depth[0,0].float().cpu().numpy()
        Kp=intrinsics[0].numpy()
        depth=metric_scale(raw,Kp)
        # Resize back after metric conversion; original RGB and K remain aligned.
        if depth.shape!=rgb.shape[:2]:
            depth=np.asarray(Image.fromarray(depth).resize((rgb.shape[1],rgb.shape[0]),Image.Resampling.BILINEAR))
        depth=np.where(np.isfinite(depth)&(depth>0)&(depth<=20),depth,0).astype(np.float32)
        return depth,{"runtime_seconds":time.perf_counter()-start,"device":self.device,
            "peak_vram_mb":None,"model_revision":MODEL_REV,"code_revision":CODE_REV,
            "adapter_revision":ADAPTER_REV,"calibration":"known K; focal / 300; no GT fitting",
            "input_information":["RGB","calibrated intrinsics"],"processed_shape":list(raw.shape)}

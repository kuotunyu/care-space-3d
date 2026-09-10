"""Fetch precisely one official checkpoint and its pinned source revision."""
import hashlib
import subprocess
import urllib.request
from pathlib import Path
from carespace.learned import ROOT,CODE_REV,MODEL_REV,WEIGHT_SHA

def main():
    source=ROOT/"third_party/Depth-Anything-3"
    if not source.exists():
        source.parent.mkdir(exist_ok=True)
        subprocess.run(["git","clone","--no-checkout","--filter=blob:none","https://github.com/ByteDance-Seed/Depth-Anything-3.git",str(source)],check=True)
        subprocess.run(["git","-C",str(source),"checkout",CODE_REV],check=True)
    actual=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
    if actual!=CODE_REV:raise RuntimeError("Existing source revision differs; refusing to overwrite it")
    dest=ROOT/"models/DA3METRIC-LARGE";dest.mkdir(parents=True,exist_ok=True)
    base=f"https://huggingface.co/depth-anything/DA3METRIC-LARGE/resolve/{MODEL_REV}/"
    for filename in ["config.json","README.md","model.safetensors"]:
        path=dest/filename
        if not path.exists():
            print(f"Downloading {filename}; checkpoint is 1,336,734,448 bytes",flush=True)
            partial=path.with_suffix(path.suffix+".part")
            subprocess.run(["curl","-L","--fail","--retry","3","-C","-","-o",str(partial),base+filename],check=True)
            partial.replace(path)
    with (dest/"model.safetensors").open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=WEIGHT_SHA:raise RuntimeError("Checkpoint checksum mismatch")
    print("Pinned DA3 source and checkpoint verified")

if __name__=="__main__":main()

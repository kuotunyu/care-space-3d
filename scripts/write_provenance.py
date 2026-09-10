"""Capture actual environment and third-party license metadata, without guessing."""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
records=[]
for dist in sorted(metadata.distributions(),key=lambda d:d.metadata["Name"].lower()):
    name=dist.metadata["Name"]
    if name=="care-space-3d":continue
    license_files=[]
    for f in dist.files or []:
        if ("license" in str(f).lower() or "copying" in str(f).lower()) and ("dist-info" in str(f) or "egg-info" in str(f)):
            p=dist.locate_file(f)
            if p.is_file():license_files.append({"path":str(f),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"text":p.read_text(encoding="utf8",errors="replace")})
    records.append({"name":name,"version":dist.version,"license":dist.metadata.get("License-Expression") or dist.metadata.get("License"),
        "classifiers":[c for c in dist.metadata.get_all("Classifier",[]) if c.startswith("License")],
        "sources":dist.metadata.get_all("Project-URL",[])+([dist.metadata["Home-page"]] if dist.metadata.get("Home-page") else []),
        "license_files":license_files})
(ROOT/"docs/dependency-provenance.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf8")
lock=["--extra-index-url https://download.pytorch.org/whl/cpu"]+[f"{r['name']}=={r['version']}" for r in records]
(ROOT/"requirements-cpu.lock").write_text("\n".join(lock)+"\n",encoding="utf8")
run={"python":sys.version,"platform":platform.platform(),"processor":platform.processor(),"device":"cpu",
     "project_source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ["src","scripts","viewer","configs"] for p in (ROOT/base).rglob("*") if p.is_file() and "__pycache__" not in str(p)}}
(ROOT/"artifacts/environment.json").write_text(json.dumps(run,indent=2),encoding="utf8")
print(f"Recorded {len(records)} installed dependency versions and available license files")

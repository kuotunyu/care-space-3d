"""Fetch an immutable small subset, preserving actual license and file hashes."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REV = "3e8c7fe5759f64bfcbc3882f9cdf6de97f82a06d"
BASE = f"https://huggingface.co/datasets/ai-habitat/ReplicaCAD_dataset/resolve/{REV}/"
NAMES = ["frl_apartment_sofa", "frl_apartment_chair_01", "frl_apartment_table_01"]
FILES = ["LICENSE.txt", "README.md", "configs/scenes/empty_stage.scene_instance.json",
         "configs/stages/frl_apartment_stage.stage_config.json", "stages/frl_apartment_stage.glb"]
for name in NAMES:
    FILES += [f"configs/objects/{name}.object_config.json", f"objects/{name}.glb",
              f"objects/convex/{name}_cv_decomp.glb"]

def main():
    dest = ROOT / "data/replicacad"
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"repo": "ai-habitat/ReplicaCAD_dataset", "revision": REV,
                "license_actual": "CC BY-NC 4.0", "license_card": "CC BY 4.0",
                "license_conflict": True, "use": "local noncommercial research", "files": []}
    for name in FILES:
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_suffix(target.suffix + ".part")
            urllib.request.urlretrieve(BASE + name, temporary)
            temporary.replace(target)
        content = target.read_bytes()
        manifest["files"].append({"path": name, "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(), "url": BASE + name})
    manifest["total_bytes"] = sum(x["bytes"] for x in manifest["files"])
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ROOT / "docs/asset-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(FILES), "bytes": manifest["total_bytes"], "revision": REV}))

if __name__ == "__main__":
    main()

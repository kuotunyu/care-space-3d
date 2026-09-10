"""Run real learned depth, resume frame predictions, retain failures, update study."""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS","2")
os.environ.setdefault("OMP_NUM_THREADS","2")
import json
import hashlib
from pathlib import Path
import time
from datetime import datetime,timezone
import numpy as np
from PIL import Image
from carespace.learned import MetricDepth,prediction_key,MODEL_REV,CODE_REV
from carespace.pipeline import ROOT,ART,load_observation,compact_points,observation_digest
from carespace.contracts import Observation
from carespace.fusion import reconstruct,FUSION_REV
from carespace.planning import analyze
from carespace.evaluation import classification_metrics,depth_metrics

def atomic_json(path,value):
    tmp=path.with_suffix(".json.part")
    tmp.write_text(json.dumps(value,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    tmp.replace(path)

def main():
    study_path=ART/"study.json"
    study=json.loads(study_path.read_text(encoding="utf-8"))
    config=json.loads((ROOT/"configs/study.json").read_text())
    if hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()!=study["config_sha256"] or study.get("reconstruction_revision")!=FUSION_REV:
        raise ValueError("Stale study configuration or reconstruction; run scripts/run_study.py first")
    cache=ART/"predictions";cache.mkdir(exist_ok=True)
    failure_path=ART/"learning-failures.json"
    if failure_path.exists():
        previous=json.loads(failure_path.read_text(encoding="utf8"))
        if previous:
            history=ART/"history";history.mkdir(exist_ok=True)
            stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            (history/(stamp+"-learning-failures.json")).write_bytes(failure_path.read_bytes())
    model=None;failures=[];summaries={};t=time.perf_counter();cache_hits=0;cache_misses=0
    for case in study["cases"]:
        if case["split"]!="evaluation":continue
        observations=[];timings={};errors={}
        for frame in case["frames"]:
            obs=load_observation(ART/"observations"/case["id"]/f"{frame['id']:03d}.npz")
            if obs.scene_id!=case["scene_id"]:raise ValueError("Stale scene revision")
            if observation_digest(obs)!=frame["observation_sha256"]:
                raise ValueError("Observation content changed; regenerate the baseline study before learning")
            key=prediction_key(obs.rgb,obs.K);path=cache/(key+".npz");meta_path=cache/(key+".json")
            try:
                if path.exists() and meta_path.exists():
                    with np.load(path,allow_pickle=False) as a:depth=a["depth"]
                    metadata=json.loads(meta_path.read_text())
                    cache_hits+=1
                else:
                    if model is None:
                        print("Loading pinned DA3METRIC-LARGE on CPU (2 threads)",flush=True)
                        model=MetricDepth()
                    cache_misses+=1
                    depth,metadata=model.predict(obs.rgb,obs.K)
                    np.savez_compressed(path,depth=depth)
                    atomic_json(meta_path,metadata)
                if depth.shape!=obs.depth.shape:raise ValueError("Depth shape mismatch")
                d=np.clip(depth/10,0,1)
                preview=np.stack([255*(1-d),220*np.sqrt(d),255*d],axis=-1).astype(np.uint8)
                preview[depth==0]=[30,40,50]
                p=cache/(key+".png");Image.fromarray(preview).save(p)
                frame["learned_depth_preview"]="/"+p.relative_to(ROOT).as_posix()
                result_obs=Observation(obs.rgb,depth,obs.K,obs.T_world_camera,obs.scene_id)
                errors[frame["id"]]=depth_metrics(depth,obs.depth) # evaluation branch only, AFTER prediction
                timings[frame["id"]]=metadata["runtime_seconds"]
                mae=errors[frame["id"]]["depth_mae_m"]
                mae_text=f"{mae:.3f}m" if mae is not None else "no valid depths"
                print(f"{case['id']} frame {frame['id']}: {metadata['runtime_seconds']:.2f}s, depth MAE={mae_text}",flush=True)
                if mae is None:failures.append({"case":case["id"],"frame":frame["id"],"error":"no valid predicted depth"})
            except Exception as exc:
                failures.append({"case":case["id"],"frame":frame["id"],"error":repr(exc)})
                atomic_json(ART/"learning-failures.json",failures)
                result_obs=Observation(obs.rgb,np.zeros_like(obs.depth),obs.K,obs.T_world_camera,obs.scene_id)
                errors.pop(frame["id"],None);timings.pop(frame["id"],None)
                print(f"FAILED {case['id']} frame {frame['id']}: {exc}",flush=True)
                if model is None: raise
            observations.append(result_obs)
        for selection in ["all","interval"]:
            ids=next(m["selected_frames"] for m in case["methods"] if m["id"]==selection)
            before=time.perf_counter()
            grid,points=reconstruct([observations[i] for i in ids],case["bounds"],case["resolution"],study["body"]["height"],case["scene_id"])
            passage=analyze(grid,case["methods"][0]["result"]["start"],case["methods"][0]["result"]["goal"],study["body"]["radius"])
            ident="da3-"+selection
            clearance=passage["clearance_m"];ref_clearance=case["oracle_result"]["clearance_m"]
            metrics={"observation_count":len(ids),"candidate_count":len(observations),
                "observed_fraction":float(np.mean(grid.states!=-1)),"unknown_fraction":float(np.mean(grid.states==-1)),
                "free_fraction":float(np.mean(grid.states==0)),"occupied_fraction":float(np.mean(grid.states==1)),
                "runtime_seconds":sum(timings.get(i,0.) for i in ids)+time.perf_counter()-before,
                "inference_compute_seconds":sum(timings.get(i,0.) for i in ids),
                "runtime_note":"original per-frame inference compute plus current fusion; cached reuse is separate",
                "device":"cpu","peak_vram_mb":None,"model_revision":MODEL_REV,"code_revision":CODE_REV,
                "oracle_status":case["oracle_result"]["status"],"pose_source":"known synthetic camera pose",
                "depth_mae_m":mean_metric(errors,ids,"depth_mae_m"),
                "depth_abs_rel":mean_metric(errors,ids,"depth_abs_rel"),
                "valid_depth_pixels":sum(errors[i]["valid_depth_pixels"] for i in ids if i in errors),
                "reference_depth_pixels":int(sum(np.count_nonzero(load_observation(ART/"observations"/case["id"]/f"{i:03d}.npz").depth>0) for i in ids)),
                "clearance_error_m":abs(clearance-ref_clearance) if clearance is not None and ref_clearance is not None else None,
                "observation_failure_fraction":sum(f["case"]==case["id"] and f["frame"] in ids for f in failures)/len(ids),
                "reconstruction_failed":not any(errors.get(i,{}).get("valid_depth_pixels",0)>0 for i in ids),"pose_failure_rate":None,
                "scale_alignment":"known focal / 300; no ground truth scale fitting"}
            case["methods"]=[m for m in case["methods"] if m["id"]!=ident]
            case["methods"].append({"id":ident,"label":"DA3 Metric · "+("全部觀測" if selection=="all" else "固定間隔"),
                "states":grid.states.ravel().tolist(),"points":compact_points(points),"selected_frames":ids,"result":passage,"metrics":metrics})
            np.savez_compressed(ART/f"{case['id']}-{ident}-grid.npz",states=grid.states,scene_id=case["scene_id"])
            summaries.setdefault(ident,([],[]));summaries[ident][0].append(passage["status"]);summaries[ident][1].append(case["oracle_result"]["status"])
            print(f"{case['id']}/{ident}: {passage['status']}",flush=True)
        study["learning_status"]="DA3METRIC-LARGE 已執行；CPU、已知相機姿態、無真值尺度校正"
        atomic_json(study_path,study)
    for name,value in summaries.items():study["classification_metrics"]["evaluation/"+name]=classification_metrics(*value)
    study["learning_execution"]={"wall_seconds":time.perf_counter()-t,"cache_hits":cache_hits,"cache_misses":cache_misses,"failures":failures,"peak_vram_mb":None,"device":"cpu","precision":"float32","threads":2}
    atomic_json(study_path,study)
    atomic_json(ART/"learning-failures.json",failures)

def mean_metric(errors,ids,name):
    chosen=[errors[i] for i in ids if i in errors and errors[i][name] is not None]
    count=sum(e["valid_depth_pixels"] for e in chosen)
    return float(sum(e[name]*e["valid_depth_pixels"] for e in chosen)/count) if count else None

if __name__=="__main__":main()

"""Small resumable study; source geometry is confined to synthesis and oracle calls."""
import hashlib
import json
from pathlib import Path
import time
from datetime import datetime,timezone
import numpy as np
from PIL import Image
from carespace.contracts import Observation
from carespace.scenes import build_scene,oracle_grid
from carespace.synthesis import Renderer,look_at,RENDERER_REV
from carespace.fusion import reconstruct,FUSION_REV
from carespace.planning import analyze
from carespace.evaluation import classification_metrics

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/"artifacts"

def poses(scene):
    _,_,w,d=scene.bounds
    points=[[1,.65,2],[w/2-.8,.65,1],[w/2+.8,.65,1],[w-1,.65,2],
            [1,.65,d-2],[w/2-.8,.65,d-1],[w/2+.8,.65,d-1],[w-1,.65,d-2]]
    out=[]
    # Camera placements are controlled synthesis inputs, not a robot navigation claim.
    for p in points:
        if any(np.all(np.array(p)>part.bounds[0]) and np.all(np.array(p)<part.bounds[1]) for part in scene.parts):
            raise ValueError("Synthetic camera lies inside a geometry AABB; revise acquisition layout")
        for target in [[w/2,.65,d/2],[w/2,.4,d-.2],[w/2,.9,.2]]:
            out.append(look_at(p,target))
    return out[:1] if scene.sparse else out

def observation_digest(observation):
    h=hashlib.sha256(observation.scene_id.encode())
    for a in (observation.rgb,observation.depth,observation.K,observation.T_world_camera):
        h.update(str((a.shape,a.dtype.str)).encode());h.update(a.tobytes())
    return h.hexdigest()

def save_observation(obs,path):
    np.savez_compressed(path,rgb=obs.rgb,depth=obs.depth,K=obs.K,T=obs.T_world_camera,scene_id=obs.scene_id,renderer_revision=RENDERER_REV)

def load_observation(path):
    with np.load(path,allow_pickle=False) as a:
        return Observation(a["rgb"],a["depth"],a["K"],a["T"],str(a["scene_id"]))

def synthesize(scene,config):
    folder=ART/"observations"/scene.id;folder.mkdir(parents=True,exist_ok=True)
    frames=[];observations=[];renderer=None
    start=time.perf_counter()
    for i,T in enumerate(poses(scene)):
        path=folder/f"{i:03d}.npz"
        obs=None
        if path.exists():
            with np.load(path,allow_pickle=False) as saved:
                if str(saved.get("renderer_revision",""))==RENDERER_REV:obs=load_observation(path)
        if obs is None or obs.scene_id!=scene.scene_id or obs.depth.shape!=(config["frame_height"],config["frame_width"]) or not np.allclose(obs.T_world_camera,T):
            if renderer is None:renderer=Renderer(scene.mesh)
            obs=renderer.render(T,scene.scene_id,config["frame_width"],config["frame_height"])
            save_observation(obs,path)
        rgb_path=folder/f"{i:03d}.png";depth_path=folder/f"{i:03d}-depth.png"
        Image.fromarray(obs.rgb).save(rgb_path)
        d=np.clip(obs.depth/10,0,1)
        color=np.stack([255*(1-d),220*np.sqrt(d),255*d],axis=-1).astype(np.uint8)
        color[obs.depth==0]=[30,40,50]
        Image.fromarray(color).save(depth_path)
        frames.append({"id":i,"rgb":"/"+rgb_path.relative_to(ROOT).as_posix(),
            "depth_preview":"/"+depth_path.relative_to(ROOT).as_posix(),"position":T[:3,3].tolist(),
            "observation_sha256":observation_digest(obs)})
        observations.append(obs)
    return observations,frames,time.perf_counter()-start

def select_frames(observations,scene,resolution,height,budget):
    n=len(observations);budget=min(budget,n)
    interval=np.linspace(0,n-1,budget,dtype=int).tolist()
    t=time.perf_counter();known=[]
    for obs in observations:
        grid,_=reconstruct([obs],scene.bounds,resolution,height,scene.scene_id)
        known.append(grid.states!=-1)
    covered=np.zeros_like(known[0]);selected=[]
    for _ in range(budget):
        score=[np.count_nonzero(k&~covered) if i not in selected else -1 for i,k in enumerate(known)]
        chosen=int(np.argmax(score));selected.append(chosen);covered |= known[chosen]
    return {"all":list(range(n)),"interval":interval,"coverage":selected},time.perf_counter()-t

def compact_points(points,max_points=7000):
    p=np.array(points["positions"]).reshape(-1,3);c=np.array(points["colors"]).reshape(-1,3)
    step=max(1,int(np.ceil(len(p)/max_points)))
    return {"positions":p[::step].ravel().tolist(),"colors":c[::step].ravel().tolist()}

def run_study():
    ART.mkdir(exist_ok=True)
    existing=ART/"study.json"
    if existing.exists():
        history=ART/"history";history.mkdir(exist_ok=True)
        name=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")+"-study.json"
        (history/name).write_bytes(existing.read_bytes())
    config=json.loads((ROOT/"configs/study.json").read_text())
    r=config["resolution"];height=config["body"]["height"];radius=config["body"]["radius"]
    config_hash=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    result={"schema_version":1,"body":{**config["body"],"assumption":"直立圓柱；平坦已知地面；圓形截面無方向性；忽略 y<0.10 m 接觸層。非完整輪椅模型。"},
            "config_sha256":config_hash,"renderer_revision":RENDERER_REV,"reconstruction_revision":FUSION_REV,
            "learning_status":"尚未執行學習式深度","cases":[],
            "unknown_pose_status":"未支援：DA3METRIC-LARGE 不估計姿態；本實驗融合使用已知合成姿態。"}
    summaries={}
    for replica in [False,True]:
        for kind in ["normal","blocked","sparse"]:
            scene=build_scene(kind,replica)
            print(f"Generating {scene.id}",flush=True)
            observations,frames,render_seconds=synthesize(scene,config)
            selections,selection_seconds=select_frames(observations,scene,r,height,config["subset_budget"])
            oracle=oracle_grid(scene,r,height)
            oracle_result=analyze(oracle,scene.start,scene.goal,radius)
            glb=ART/f"{scene.id}-reference.glb"
            scene.mesh.export(glb)
            case={"id":scene.id,"title":scene.title,"description":scene.description,"split":scene.split,
                "family":scene.family,"scene_id":scene.scene_id,"bounds":scene.bounds,"resolution":r,
                "shape":list(oracle.states.shape),"reference_mesh":"/"+glb.relative_to(ROOT).as_posix(),
                "frames":frames,"methods":[],"oracle_result":oracle_result,"scene_source":"programmatic room; original-scale ReplicaCAD furniture recolored" if replica else "analytic geometry",
                "render_seconds":render_seconds,"coverage_selection_seconds":selection_seconds,
                "selection_cost_note":"Coverage selection inspects ALL candidate RGB-D frames; reduction is in fusion budget, not sensor acquisition."}
            labels={"all":"RGB-D · 全部觀測","interval":"RGB-D · 固定間隔","coverage":"RGB-D · 覆蓋選樣"}
            for name,ids in selections.items():
                before=time.perf_counter()
                grid,points=reconstruct([observations[i] for i in ids],scene.bounds,r,height,scene.scene_id)
                passage=analyze(grid,scene.start,scene.goal,radius)
                elapsed=time.perf_counter()-before
                np.savez_compressed(ART/f"{scene.id}-{name}-grid.npz",states=grid.states,scene_id=scene.scene_id)
                clearance=passage["clearance_m"];ref_clearance=oracle_result["clearance_m"]
                metrics={"observation_count":len(ids),"candidate_count":len(observations),
                    "observed_fraction":float(np.mean(grid.states!=-1)),"unknown_fraction":float(np.mean(grid.states==-1)),
                    "free_fraction":float(np.mean(grid.states==0)),"occupied_fraction":float(np.mean(grid.states==1)),
                    "geometry_occupied_iou":float(np.sum((grid.states==1)&(oracle.states==1))/max(1,np.sum((grid.states==1)|(oracle.states==1)))),
                    "clearance_error_m":abs(clearance-ref_clearance) if clearance is not None and ref_clearance is not None else None,
                    "runtime_seconds":elapsed,"peak_vram_mb":None,"device":"cpu","reconstruction_failed":False,
                    "observation_failure_fraction":float(np.mean([not np.any(o.depth>0) for o in observations])),
                    "pose_source":"known synthetic camera pose","pose_failure_rate":None,
                    "oracle_status":oracle_result["status"]}
                case["methods"].append({"id":name,"label":labels[name],"states":grid.states.ravel().tolist(),
                    "points":compact_points(points),"selected_frames":ids,"result":passage,"metrics":metrics})
                key=scene.split+"/"+name
                summaries.setdefault(key,([],[]));summaries[key][0].append(passage["status"]);summaries[key][1].append(oracle_result["status"])
                print(f"  {name}: {passage['status']}, observed={metrics['observed_fraction']:.1%}",flush=True)
            result["cases"].append(case)
    result["classification_metrics"]={k:classification_metrics(*v) for k,v in summaries.items()}
    target=ART/"study.json";target.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"Saved {target} ({target.stat().st_size/1e6:.2f} MB)",flush=True)
    return result

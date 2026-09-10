import importlib.util
from pathlib import Path
import numpy as np
import json
import hashlib
from carespace.evaluation import depth_metrics
from carespace.contracts import Observation
from carespace.pipeline import save_observation,observation_digest
from carespace.fusion import FUSION_REV

spec=importlib.util.spec_from_file_location("run_learning",Path(__file__).parents[1]/"scripts/run_learning.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_selected_error_is_pixel_weighted_and_skips_missing_frame_id():
    records={0:{"depth_mae_m":1.,"valid_depth_pixels":10},2:{"depth_mae_m":3.,"valid_depth_pixels":30}}
    assert module.mean_metric(records,[0,1,2],"depth_mae_m")==2.5
    assert module.mean_metric(records,[0],"depth_mae_m")==1.
    assert module.mean_metric(records,[1],"depth_mae_m") is None

def test_all_invalid_prediction_preserves_zero_valid_count():
    m=depth_metrics(np.zeros((3,3)),np.ones((3,3)))
    assert m["depth_mae_m"] is None
    assert m["valid_depth_pixels"]==0
    assert m["reference_depth_pixels"]==9

def test_middle_failure_and_invalid_frame_keep_one_slot_each(tmp_path,monkeypatch):
    art=tmp_path/"artifacts";folder=art/"observations"/"case";folder.mkdir(parents=True)
    (tmp_path/"configs").mkdir()
    config={"resolution":.1}
    (tmp_path/"configs/study.json").write_text(json.dumps(config))
    frames=[]
    for i in range(3):
        obs=Observation(np.full((3,3,3),i,np.uint8),np.ones((3,3),np.float32),np.eye(3),np.eye(4),"s")
        save_observation(obs,folder/f"{i:03d}.npz")
        frames.append({"id":i,"observation_sha256":observation_digest(obs)})
    case={"id":"case","scene_id":"s","split":"evaluation","frames":frames,"bounds":[0,0,2,2],"resolution":.1,
        "oracle_result":{"status":"passable","clearance_m":None},"methods":[
            {"id":"all","selected_frames":[0,1,2],"result":{"start":[.55,.55],"goal":[1.45,1.45]}},
            {"id":"interval","selected_frames":[0,2]}]}
    study={"config_sha256":hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
        "reconstruction_revision":FUSION_REV,"body":{"height":1.2,"radius":.1},"cases":[case],"classification_metrics":{}}
    (art/"study.json").write_text(json.dumps(study))
    class FakeMetric:
        def predict(self,rgb,K):
            i=int(rgb[0,0,0])
            if i==1:raise RuntimeError("injected frame failure")
            return np.full((3,3),1. if i==0 else 0.,np.float32),{"runtime_seconds":float(i+1)}
    monkeypatch.setattr(module,"ROOT",tmp_path);monkeypatch.setattr(module,"ART",art)
    monkeypatch.setattr(module,"MetricDepth",FakeMetric)
    calls=[];real_reconstruct=module.reconstruct
    def capture(observations,*args):
        calls.append([float(o.depth.mean()) for o in observations])
        return real_reconstruct(observations,*args)
    monkeypatch.setattr(module,"reconstruct",capture)
    module.main()
    assert calls==[[1.,0.,0.],[1.,0.]]
    saved=json.loads((art/"study.json").read_text(encoding="utf8"))
    methods={m["id"]:m for m in saved["cases"][0]["methods"]}
    assert methods["da3-all"]["metrics"]["observation_failure_fraction"]==2/3
    assert methods["da3-interval"]["metrics"]["observation_failure_fraction"]==.5
    assert methods["da3-all"]["metrics"]["reference_depth_pixels"]==27
    assert methods["da3-all"]["metrics"]["inference_compute_seconds"]==4
    assert saved["learning_execution"]["cache_misses"]==3

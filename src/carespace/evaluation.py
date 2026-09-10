"""Explicit denominators; abstaining is counted rather than rewarded as correctness."""
import numpy as np

def classification_metrics(predictions,references):
    if len(predictions)!=len(references): raise ValueError("Query count mismatch")
    n=len(predictions)
    if any(x not in {"passable","blocked","unknown"} for x in predictions+references):
        raise ValueError("Invalid passage label")
    count={s:predictions.count(s) for s in ("passable","blocked","unknown")}
    false_release=sum(p=="passable" and r=="blocked" for p,r in zip(predictions,references))
    negatives=references.count("blocked")
    ratio=lambda a,b: a/b if b else None
    confusion={r:{p:sum(a==p and b==r for a,b in zip(predictions,references))
        for p in count} for r in count}
    return {"n_queries":n,"counts":count,"decision_coverage":ratio(n-count["unknown"],n),
        "status_coverage":{k:ratio(v,n) for k,v in count.items()},
        "false_release_count":false_release,"oracle_blocked_count":negatives,
        "predicted_pass_count":count["passable"],
        "false_release_per_oracle_blocked":ratio(false_release,negatives),
        "false_release_per_predicted_pass":ratio(false_release,count["passable"]),
        "confusion":confusion}

def depth_metrics(predicted,reference):
    valid=(reference>0)&np.isfinite(predicted)&(predicted>0)
    counts={"valid_depth_pixels":int(valid.sum()),"reference_depth_pixels":int((reference>0).sum())}
    if not valid.any(): return {"depth_mae_m":None,"depth_abs_rel":None,"valid_depth_fraction":0.,**counts}
    error=np.abs(predicted[valid]-reference[valid])
    return {"depth_mae_m":float(error.mean()),"depth_abs_rel":float((error/reference[valid]).mean()),
            "valid_depth_fraction":float(valid.mean()),**counts}

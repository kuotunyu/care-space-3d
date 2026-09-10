"""Reference-assisted evaluation only. Never imported by reconstruction/inference."""
import numpy as np
from carespace.fusion import volume_centers
from carespace.synthesis import camera_rays

FLOOR_TOLERANCE_M=1e-4  # Numerical equality with the controlled support plane Y=0.
AUDIT_REV="pixel-endpoint-floor-support-v1"

def trace_frame(reference,predicted,bounds,resolution,height):
    predicted=np.asarray(predicted)
    if predicted.shape!=reference.depth.shape:raise ValueError("Prediction/reference shape mismatch")
    _,shape=volume_centers(bounds,resolution,height)
    h,w=predicted.shape
    origins,rays=camera_rays(reference.K,reference.T_world_camera,w,h)
    pred=predicted.ravel();truth=reference.depth.ravel()
    valid_pred=np.isfinite(pred)&(pred>0)&(pred<20)
    valid_truth=truth>0;valid=valid_pred&valid_truth
    truth_points=origins+rays*truth[:,None]
    floor=valid_truth&(np.abs(truth_points[:,1])<=FLOOR_TOLERANCE_M)
    points=origins+rays*np.where(valid_pred,pred,0)[:,None]
    cells=np.floor((points-[bounds[0],.1,bounds[1]])/resolution).astype(int)
    x,y,z=cells.T
    inside=valid_pred&(x>=0)&(x<shape[0])&(z>=0)&(z<shape[1])&(y>=0)&(y<shape[2])
    floor_lift=inside&floor
    support={}
    for name,mask in [('occupied',inside),('floor',floor_lift),
                     ('nonfloor',inside&valid_truth&~floor),('unlabeled',inside&~valid_truth)]:
        grid=np.zeros(shape[:2],bool);grid[x[mask],z[mask]]=True;support[name+'_support']=grid
    error=pred[valid]-truth[valid]
    floor_valid=floor&valid_pred
    metrics={"valid_pair_pixels":int(valid.sum()),"reference_pixels":int(valid_truth.sum()),
        "invalid_prediction_pixels":int((~valid_pred).sum()),"floor_pixels":int(floor.sum()),
        "floor_valid_prediction_pixels":int(floor_valid.sum()),"floor_lift_pixels":int(floor_lift.sum()),
        "signed_depth_mean_m":float(error.mean()) if len(error) else None,
        "depth_mae_m":float(np.abs(error).mean()) if len(error) else None,
        "depth_absolute_p95_m":float(np.quantile(np.abs(error),.95)) if len(error) else None,
        "floor_depth_ratio_median":float(np.median(pred[floor_valid]/truth[floor_valid])) if floor_valid.any() else None,
        "floor_predicted_y_median_m":float(np.median(points[floor_valid,1])) if floor_valid.any() else None}
    signed=np.full(pred.shape,np.nan);signed[valid]=pred[valid]-truth[valid]
    return {**support,"metrics":metrics,"signed_error":signed.reshape(h,w),
            "floor_lift_mask":floor_lift.reshape(h,w)}

def summarize_support(traces,baseline_states,selected_states):
    """Attribution requires exact agreement with the saved occupied-wins endpoint union."""
    if not traces:raise ValueError("No frame evidence")
    baseline_states=np.asarray(baseline_states);selected_states=np.asarray(selected_states)
    if baseline_states.shape!=selected_states.shape or any(not np.isin(a,[-1,0,1]).all() for a in [baseline_states,selected_states]):
        raise ValueError("Invalid comparison grids")
    names=['occupied','floor','nonfloor','unlabeled']
    if any(t[name+'_support'].shape!=selected_states.shape for t in traces for name in names):
        raise ValueError("Support grid shape mismatch")
    union={name:np.logical_or.reduce([t[name+'_support'] for t in traces]) for name in names}
    if not np.array_equal(union['occupied'],selected_states==1):
        raise ValueError("Predicted endpoint union does not reproduce saved occupied states")
    conflict=(baseline_states==0)&(selected_states==1)
    floor_only=union['floor']&~union['nonfloor']&~union['unlabeled']
    votes=np.sum([t['occupied_support'] for t in traces],axis=0)
    support_count,cell_count=np.unique(votes[conflict],return_counts=True)
    return {"conflict_cells":int(conflict.sum()),
        "floor_supported_conflict_cells":int((conflict&union['floor']).sum()),
        "floor_only_conflict_cells":int((conflict&floor_only).sum()),
        "nonfloor_supported_conflict_cells":int((conflict&union['nonfloor']).sum()),
        "unlabeled_supported_conflict_cells":int((conflict&union['unlabeled']).sum()),
        "single_frame_supported_conflict_cells":int((conflict&(votes==1)).sum()),
        "supporting_frame_histogram":{str(int(k)):int(v) for k,v in zip(support_count,cell_count)},
        "occupied_union_matches":True}

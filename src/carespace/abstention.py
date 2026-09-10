"""Exploratory predicted-endpoint abstention; no reference geometry/depth inputs."""
import numpy as np
from carespace.fusion import volume_centers
from carespace.synthesis import camera_rays

ABSTENTION_REV='single-frame-column-to-unknown-v1'


def endpoint_support(depth,K,T_world_camera,bounds,resolution,height):
    depth=np.asarray(depth)
    if depth.ndim!=2:raise ValueError('Depth must be a camera-Z image')
    _,shape=volume_centers(bounds,resolution,height)
    origins,rays=camera_rays(K,T_world_camera,depth.shape[1],depth.shape[0])
    ds=depth.ravel();valid=np.isfinite(ds)&(ds>0)&(ds<20)
    points=origins[valid]+rays[valid]*ds[valid,None]
    x,y,z=np.floor((points-[bounds[0],.1,bounds[1]])/resolution).astype(int).T
    inside=(x>=0)&(x<shape[0])&(z>=0)&(z<shape[1])&(y>=0)&(y<shape[2])
    mask=np.zeros(shape[:2],bool);mask[x[inside],z[inside]]=True
    return mask


def abstain_single_frame(states,frame_support):
    states=np.asarray(states)
    if states.ndim!=2 or not np.isin(states,[-1,0,1]).all() or not frame_support:
        raise ValueError('Valid ternary grid and distinct-frame evidence required')
    masks=list(frame_support.values())
    if any(m.shape!=states.shape or m.dtype!=bool for m in masks):
        raise ValueError('Support must be boolean and match the grid')
    votes=np.sum(masks,axis=0)
    if not np.array_equal(votes>0,states==1):
        raise ValueError('Endpoint union differs from saved occupied grid')
    changed=states.astype(np.int8,copy=True)
    changed[(states==1)&(votes==1)]=-1
    return changed,votes

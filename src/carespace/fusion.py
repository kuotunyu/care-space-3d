"""Observed ray samples only; occupied-wins conflicts and unknown volume."""
import numpy as np
from carespace.contracts import Grid
from carespace.synthesis import camera_rays

FUSION_REV="observed-rays-half-voxel-v2"

def volume_centers(bounds,resolution,height):
    if len(bounds)!=4 or not np.isfinite(bounds).all() or bounds[2]<=bounds[0] or bounds[3]<=bounds[1]:
        raise ValueError("Finite increasing XZ bounds required")
    if not np.isfinite(resolution) or resolution<=0 or not np.isfinite(height) or height<.1+resolution:
        raise ValueError("Height must contain at least one analyzed voxel above the floor tolerance")
    xmin,zmin,xmax,zmax=bounds
    xs=np.arange(xmin+resolution/2,xmax,resolution)
    zs=np.arange(zmin+resolution/2,zmax,resolution)
    # Known flat support at y=0; ignore the floor contact layer below 0.10 m.
    ny=int(np.ceil((height-.1)/resolution-1e-9))
    ys=.1+(np.arange(ny)+.5)*resolution
    X,Z,Y=np.meshgrid(xs,zs,ys,indexing="ij")
    return np.column_stack([X.ravel(),Y.ravel(),Z.ravel()]),(len(xs),len(zs),len(ys))

def reconstruct(observations,bounds,resolution,height,scene_id):
    _,shape=volume_centers(bounds,resolution,height)
    free=np.zeros(shape,bool); occupied=np.zeros(shape,bool)
    point_arrays=[];color_arrays=[]
    margin=np.sqrt(3)*resolution/2
    for obs in observations:
        if obs.scene_id!=scene_id:
            raise ValueError("Observation scene revision is stale")
        T=obs.T_world_camera
        h,w=obs.depth.shape
        origins,rays=camera_rays(obs.K,T,w,h)
        ds=obs.depth.ravel();good=(ds>0)&(ds<20)
        points=origins[good]+rays[good]*ds[good,None]
        # Trace actual measured rays. Nearest-pixel projective carving would falsely
        # certify a whole pixel cone when only its centre ray was observed.
        selected_rays=rays[good][::2]
        lengths=np.linalg.norm(selected_rays,axis=1)
        ends=ds[good][::2]*lengths-margin
        directions=selected_rays/np.maximum(lengths[:,None],1e-12)
        step=resolution/2
        maximum=min(float(ends.max(initial=0)),float(np.linalg.norm(np.array(bounds[2:])-bounds[:2])+height*4))
        for offset in range(0,max(0,int(np.ceil(maximum/step))),16):
            distances=(offset+np.arange(16))*step
            valid=distances[None,:]<ends[:,None]
            samples=(T[:3,3]+directions[:,None,:]*distances[None,:,None])[valid]
            cells=np.floor((samples-[bounds[0],.1,bounds[1]])/resolution).astype(int)
            x,y,zz=cells.T
            inside=(x>=0)&(x<shape[0])&(zz>=0)&(zz<shape[1])&(y>=0)&(y<shape[2])
            free[x[inside],zz[inside],y[inside]]=True
        xyz=np.floor((points-[bounds[0],.1,bounds[1]])/resolution).astype(int)
        x,y,zz=xyz.T
        inside=(x>=0)&(x<shape[0])&(zz>=0)&(zz<shape[1])&(y>=0)&(y<shape[2])
        occupied[x[inside],zz[inside],y[inside]]=True
        point_arrays.append(points[::12]);color_arrays.append(obs.rgb.reshape(-1,3)[good][::12]/255.)
    state=np.full(shape[:2],-1,np.int8)
    state[free.all(axis=2)]=0
    state[occupied.any(axis=2)]=1
    points=np.concatenate(point_arrays) if point_arrays else np.empty((0,3))
    colors=np.concatenate(color_arrays) if color_arrays else np.empty((0,3))
    if len(points)>24000:
        step=int(np.ceil(len(points)/24000));points=points[::step];colors=colors[::step]
    return Grid(state,list(bounds[:2]),resolution,scene_id),{"positions":points.round(3).ravel().tolist(),"colors":colors.round(3).ravel().tolist()}

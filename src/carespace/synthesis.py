"""CPU pinhole RGB-D synthesis from source triangles; source never enters fusion."""
import numpy as np
from trimesh.ray.ray_pyembree import RayMeshIntersector
from carespace.contracts import Observation

RENDERER_REV="cpu-embree-camera-z-recolor-v2"

def look_at(position,target):
    p=np.asarray(position,dtype=float)
    forward=np.asarray(target,dtype=float)-p
    if not np.isfinite([*p,*forward]).all() or np.linalg.norm(forward)<1e-9:
        raise ValueError("Finite distinct camera position and target required")
    forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,1,0])
    if np.linalg.norm(right)<1e-9:raise ValueError("Camera direction cannot be parallel to world up")
    right/=np.linalg.norm(right)
    down=np.cross(forward,right)
    T=np.eye(4); T[:3,:3]=np.column_stack([right,down,forward]); T[:3,3]=p
    return T

def camera_rays(K,T,width,height):
    u,v=np.meshgrid(np.arange(width),np.arange(height))
    camera=np.column_stack([(u.ravel()-K[0,2])/K[0,0],(v.ravel()-K[1,2])/K[1,1],np.ones(width*height)])
    rays=camera@T[:3,:3].T
    return np.broadcast_to(T[:3,3],rays.shape).copy(),rays

class Renderer:
    def __init__(self,mesh):
        self.mesh=mesh
        self.intersector=RayMeshIntersector(mesh)

    def render(self,T,scene_id,width=224,height=168):
        K=np.array([[width/2,0,(width-1)/2],[0,width/2,(height-1)/2],[0,0,1.]])
        origins,rays=camera_rays(K,T,width,height)
        triangles,ray_ids,hits=self.intersector.intersects_id(origins,rays,multiple_hits=False,return_locations=True)
        depth=np.zeros(width*height,np.float32)
        depth[ray_ids]=((hits-origins[ray_ids])@T[:3,:3])[:,2]
        rgb=np.full((width*height,3),[213,225,234],dtype=np.uint8)
        colors=self.mesh.visual.face_colors[triangles,:3].astype(float)
        normal=self.mesh.face_normals[triangles]
        light=np.array([.3,.85,.4]); light/=np.linalg.norm(light)
        shading=.65+.35*np.abs(normal@light)
        # Small fixed spatial pattern supplies texture while preserving exact geometry.
        check=(np.floor(hits[:,0]*5)+np.floor(hits[:,2]*5)).astype(int)%2
        rgb[ray_ids]=np.clip(colors*shading[:,None]*(.95+.05*check[:,None]),0,255)
        return Observation(rgb.reshape(height,width,3),depth.reshape(height,width),K,T,scene_id)

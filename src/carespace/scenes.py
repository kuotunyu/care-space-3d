"""Declared programmatic room layouts. ReplicaCAD objects retain original metre scale."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np
import trimesh
from scipy.ndimage import binary_fill_holes
from carespace.contracts import Grid

ROOT=Path(__file__).resolve().parents[2]

@dataclass
class Scene:
    id: str
    title: str
    description: str
    family: str
    split: str
    parts: list
    bounds: list
    start: list
    goal: list
    sparse: bool=False

    @property
    def mesh(self):
        return trimesh.util.concatenate(self.parts)

    @property
    def scene_id(self):
        h=hashlib.sha256(self.id.encode())
        for p in self.parts:
            h.update(p.vertices.tobytes());h.update(p.faces.tobytes());h.update(p.visual.face_colors.tobytes())
        return h.hexdigest()[:20]

def box(extents,center,color):
    mesh=trimesh.creation.box(extents)
    mesh.apply_translation(center)
    mesh.visual.face_colors=np.array([*color,255],np.uint8)
    return mesh

def build_scene(kind="normal",replica=True):
    width=8 if replica else 7
    depth=6 if replica else 5
    cx=width/2;cz=depth/2
    parts=[box([width,.1,depth],[cx,-.05,cz],[191,183,162]),
           box([width,2.6,.12],[cx,1.3,0],[203,214,219]),
           box([width,2.6,.12],[cx,1.3,depth],[203,214,219]),
           box([.12,2.6,depth],[0,1.3,cz],[203,214,219]),
           box([.12,2.6,depth],[width,1.3,cz],[203,214,219])]
    gap=2 if replica else 1.6
    seg=(depth-gap)/2
    parts += [box([.18,1.8,seg],[cx,.9,seg/2],[139,167,176]),
              box([.18,1.8,seg],[cx,.9,depth-seg/2],[139,167,176])]
    if replica:
        for name,x,z,angle,color in [
            ("frl_apartment_sofa",1.65,1.05,0,[102,139,149]),
            ("frl_apartment_table_01",6.2,1.1,0,[158,119,76]),
            ("frl_apartment_chair_01",6.5,4.8,25,[181,145,110])]:
            if kind=="blocked" and name=="frl_apartment_sofa":
                x,z,angle=cx,cz,90
            mesh=trimesh.load(ROOT/f"data/replicacad/objects/{name}.glb",force="mesh")
            mesh.apply_translation([0,-mesh.bounds[0,1],0])
            mesh.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),[0,1,0]))
            mesh.apply_translation([x,0,z])
            # Explicit recoloring avoids relying on unsupported compressed PBR textures.
            mesh.visual=trimesh.visual.ColorVisuals(mesh,face_colors=np.tile([*color,255],(len(mesh.faces),1)))
            parts.append(mesh)
    else:
        parts += [box([1.5,.8,.8],[1.5,.4,.8],[110,150,160])]
    if kind=="blocked" and not replica:
        parts.append(box([.55,1.4,gap+.15],[cx,.7,cz],[206,112,87]))
    label={"normal":"通道開放","blocked":"沙發移至通道" if replica else "新增隔擋後","sparse":"觀測不足"}[kind]
    prefix="ReplicaCAD 家具" if replica else "解析幾何"
    return Scene(("replica" if replica else "fixture")+"-"+kind,prefix+" · "+label,
        "程式化房間與家具配置；原始幾何僅供生成與參考評估。" if replica else "獨立開發用幾何測試房間。",
        "programmatic-replica-furniture" if replica else "analytic-development",
        "evaluation" if replica else "development",parts,[0,0,width,depth],
        [1.25,cz+.05],[width-1.25,cz+.05],kind=="sparse")

def oracle_grid(scene,resolution=.1,height=1.2):
    """Full triangle reference, rasterized separately; no supplied Habitat navmesh."""
    shape=tuple(np.ceil((np.array(scene.bounds[2:])-scene.bounds[:2])/resolution).astype(int))
    occupied=np.zeros(shape,bool)
    for part in scene.parts:
        # Exclude ground and surfaces entirely outside the cylinder height interval.
        tris=part.triangles
        chosen=(tris[:,:,1].max(axis=1)>.1)&(tris[:,:,1].min(axis=1)<height)
        if not chosen.any():continue
        sub=trimesh.Trimesh(vertices=tris[chosen].reshape(-1,3),faces=np.arange(chosen.sum()*3).reshape(-1,3),process=False)
        verts,_=trimesh.remesh.subdivide_to_size(sub.vertices,sub.faces,max_edge=resolution*.45,max_iter=10)
        verts=verts[(verts[:,1]>.1)&(verts[:,1]<height)]
        cells=np.floor((verts[:,[0,2]]-scene.bounds[:2])/resolution).astype(int)
        valid=(cells>=0).all(axis=1)&(cells<shape).all(axis=1)
        mask=np.zeros(shape,bool);mask[tuple(cells[valid].T)]=True
        occupied |= binary_fill_holes(mask)
    return Grid(occupied.astype(np.int8),scene.bounds[:2],resolution,scene.scene_id)

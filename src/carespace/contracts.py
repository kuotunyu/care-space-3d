"""Metric observation types. No reference geometry is part of reconstruction input."""
from dataclasses import dataclass
import numpy as np

@dataclass
class Observation:
    rgb: np.ndarray
    depth: np.ndarray
    K: np.ndarray
    T_world_camera: np.ndarray
    scene_id: str

    def __post_init__(self):
        if self.depth.ndim != 2 or self.rgb.shape != (*self.depth.shape,3):
            raise ValueError("RGB/depth shape mismatch")
        if not np.isfinite(self.depth).all() or np.any(self.depth < 0):
            raise ValueError("Depth must be finite nonnegative camera-Z metres; zero is invalid")
        T=np.asarray(self.T_world_camera)
        if T.shape != (4,4) or not np.isfinite(T).all() or not np.allclose(T[3],[0,0,0,1]):
            raise ValueError("Invalid rigid camera pose")
        if not np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-5) or not np.isclose(np.linalg.det(T[:3,:3]),1):
            raise ValueError("Camera rotation must be right-handed orthonormal")
        if self.K.shape != (3,3) or not np.isfinite(self.K).all() or min(self.K[0,0],self.K[1,1])<=0:
            raise ValueError("Invalid calibrated intrinsics")
        if not np.allclose(self.K[2],[0,0,1]) or not np.isclose(self.K[0,1],0) or not np.isclose(self.K[1,0],0):
            raise ValueError("Only zero-skew pinhole intrinsics are supported")

@dataclass
class Grid:
    states: np.ndarray
    origin: list
    resolution: float
    scene_id: str

    def __post_init__(self):
        self.states=np.asarray(self.states,dtype=np.int8)
        if self.states.ndim!=2 or not np.isin(self.states,[-1,0,1]).all():
            raise ValueError("Grid states must be unknown=-1/free=0/occupied=1")
        if not np.isfinite(self.resolution) or self.resolution<=0:
            raise ValueError("Resolution must be positive")

    def cell(self,point):
        return tuple(np.floor((np.asarray(point)-self.origin)/self.resolution).astype(int))

    def position(self,cell):
        return (np.asarray(self.origin)+(np.asarray(cell)+.5)*self.resolution).tolist()

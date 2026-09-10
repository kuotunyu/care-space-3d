import numpy as np
import pytest
from carespace.contracts import Observation, Grid
from carespace.synthesis import look_at, camera_rays
from carespace.fusion import reconstruct
from carespace.planning import analyze

def test_camera_z_and_rigid_pose():
    T = look_at([0, 1, 0], [0, 1, 2])
    K = np.array([[2, 0, 1], [0, 2, 1], [0, 0, 1.]])
    origins, rays = camera_rays(K, T, 3, 3)
    np.testing.assert_allclose(rays[4], [0, 0, 1])
    np.testing.assert_allclose((rays[0] * 2) @ T[:3, :3], [-1, -1, 2])
    with pytest.raises(ValueError):
        Observation(np.zeros((3,3,3),np.uint8), np.ones((3,3)), K, np.zeros((4,4)), "s")

def test_unknown_and_barrier_are_distinct():
    grid = Grid(np.zeros((30,30),np.int8), [0,0], .1, "s")
    assert analyze(grid,[.65,1.55],[2.35,1.55],.2)["status"] == "passable"
    grid.states[14:16,:] = -1
    assert analyze(grid,[.65,1.55],[2.35,1.55],.2)["status"] == "unknown"
    grid.states[14:16,:] = 1
    assert analyze(grid,[.65,1.55],[2.35,1.55],.2)["status"] == "blocked"

def test_radius_boundary_and_narrow_gap():
    states = np.zeros((40,40),np.int8)
    states[19:21,:] = 1
    states[19:21,16:24] = 0
    grid = Grid(states,[0,0],.1,"s")
    assert analyze(grid,[.85,2.05],[3.05,2.05],.15)["status"] == "passable"
    assert analyze(grid,[.85,2.05],[3.05,2.05],.45)["status"] == "blocked"
    assert analyze(grid,[.05,2.05],[3.05,2.05],.15)["status"] == "blocked"

def test_occluded_volume_stays_unknown_and_stale_rejected():
    K=np.array([[4,0,2],[0,4,2],[0,0,1.]])
    obs=Observation(np.zeros((5,5,3),np.uint8),np.ones((5,5)),K,
                    look_at([1,.6,0],[1,.6,2]),"s")
    g, points = reconstruct([obs], [0,0,2,3], .1, 1.2, "s")
    assert np.all(g.states[:,20:] == -1)
    with pytest.raises(ValueError,match="revision"):
        reconstruct([obs],[0,0,2,3],.1,1.2,"changed")

def test_invalid_depth_does_not_carve_free():
    K=np.eye(3)
    obs=Observation(np.zeros((2,2,3),np.uint8),np.zeros((2,2)),K,np.eye(4),"s")
    g,_=reconstruct([obs],[0,0,2,2],.1,1.2,"s")
    assert np.all(g.states == -1)

def test_height_cannot_create_vacuously_free_volume():
    with pytest.raises(ValueError,match="Height"):
        reconstruct([],[0,0,2,2],.1,.1,"s")

def test_one_valid_ray_does_not_fill_its_entire_pixel_cone():
    depth=np.zeros((5,5),np.float32);depth[2,2]=10
    K=np.array([[.01,0,2],[0,.01,2],[0,0,1.]])
    obs=Observation(np.zeros((5,5,3),np.uint8),depth,K,look_at([1,.6,0],[1,.6,2]),"s")
    g,_=reconstruct([obs],[0,0,2,3],.1,1.2,"s")
    assert not np.any(g.states==0)

def test_unsupported_camera_intrinsics_and_look_at_are_rejected():
    K=np.eye(3);K[0,1]=.2
    with pytest.raises(ValueError,match="zero-skew"):
        Observation(np.zeros((2,2,3),np.uint8),np.ones((2,2)),K,np.eye(4),"s")
    with pytest.raises(ValueError):look_at([0,0,0],[0,0,0])
    with pytest.raises(ValueError):look_at([0,0,0],[0,1,0])

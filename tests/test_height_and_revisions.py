import numpy as np
import pytest
from carespace.contracts import Observation
from carespace.fusion import reconstruct,volume_centers
from carespace.synthesis import look_at
from carespace.pipeline import observation_digest

def test_overhang_below_body_top_is_occupied_not_ground_only_free():
    K=np.array([[100,0,1],[0,100,1],[0,0,1.]])
    obs=Observation(np.zeros((3,3,3),np.uint8),np.ones((3,3)),K,look_at([.55,1.1,.05],[.55,1.1,2]),"s")
    low,_=reconstruct([obs],[0,0,2,2],.1,.8,"s")
    high,_=reconstruct([obs],[0,0,2,2],.1,1.2,"s")
    assert np.count_nonzero(low.states==1)==0
    assert np.count_nonzero(high.states==1)>0

def test_partial_top_layer_is_included():
    _,shape=volume_centers([0,0,1,1],.1,.22)
    assert shape[2]==2

def test_pose_edit_changes_observation_digest():
    obs=Observation(np.zeros((3,3,3),np.uint8),np.ones((3,3)),np.eye(3),np.eye(4),"s")
    old=observation_digest(obs)
    obs.T_world_camera[0,3]=.5
    assert observation_digest(obs)!=old

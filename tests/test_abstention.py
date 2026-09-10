import numpy as np
import pytest
from carespace.contracts import Grid
from carespace.planning import analyze
from carespace.abstention import abstain_single_frame, endpoint_support


def test_single_frame_wall_becomes_unknown_without_new_free_space():
    states=np.zeros((20,20),np.int8);states[10,:]=1
    evidence={0:states==1}
    changed,votes=abstain_single_frame(states,evidence)
    assert np.array_equal(changed==0,states==0)
    assert (changed[10,:]==-1).all() and (states[10,:]==1).all()
    before=analyze(Grid(states,[0,0],.1,'test'),[.55,1.05],[1.55,1.05],0)
    after=analyze(Grid(changed,[0,0],.1,'test'),[.55,1.05],[1.55,1.05],0)
    assert before['status']=='blocked' and after['status']=='unknown'
    assert votes[10,10]==1


def test_repeated_support_retains_obstacles_and_unknown_is_preserved():
    states=np.array([[1,-1,0],[0,1,0]],np.int8)
    a=states==1;b=np.zeros_like(a);b[0,0]=True
    result,_=abstain_single_frame(states,{0:a,1:b})
    assert np.array_equal(result,[[1,-1,0],[0,-1,0]])
    for evidence in [{},{0:np.zeros_like(a)},{0:np.ones((1,1),bool)},
                     {0:a.astype(float)}]:
        with pytest.raises(ValueError):abstain_single_frame(states,evidence)


def test_predicted_endpoints_need_no_reference_depth_and_count_column_once():
    T=np.eye(4);T[:3,3]=[1.,.5,1.]
    mask=endpoint_support(np.array([[.5,.5]]),np.diag([100.,100.,1.]),T,[0,0,3,3],.1,1.2)
    assert mask.dtype==bool and mask.sum()==1 and mask[10,15]
    for value in [0.,20.,np.nan]:
        assert not endpoint_support(np.array([[value]]),np.eye(3),T,[0,0,3,3],.1,1.2).any()

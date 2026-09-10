import numpy as np
from carespace.contracts import Observation
from carespace.depth_audit import trace_frame,summarize_support

def observation(depth=1.):
    # Central camera ray travels downward toward a known flat floor at Y=0.
    T=np.eye(4);T[:3,:3]=[[1,0,0],[0,0,-1],[0,1,0]];T[:3,3]=[1.5,1.,1.5]
    return Observation(np.zeros((1,1,3),np.uint8),np.array([[depth]],np.float32),np.eye(3),T,'fixture')

def test_underestimated_floor_depth_enters_height_band():
    r=trace_frame(observation(),np.array([[.8]],np.float32),[0,0,3,3],.1,1.2)
    assert r['metrics']['floor_pixels']==1
    assert r['metrics']['floor_lift_pixels']==1
    assert r['floor_support'][15,15]
    assert r['metrics']['signed_depth_mean_m']<0

def test_correct_floor_and_invalid_depth_do_not_create_occupied_support():
    for depth in [1.,0.,20.]:
        r=trace_frame(observation(),np.array([[depth]],np.float32),[0,0,3,3],.1,1.2)
        assert not r['occupied_support'].any()
        assert not r['floor_support'].any()

def test_invalid_reference_is_not_mislabeled_nonfloor():
    r=trace_frame(observation(0.),np.array([[.8]],np.float32),[0,0,3,3],.1,1.2)
    assert r['unlabeled_support'].any()
    assert not r['nonfloor_support'].any()
    assert r['metrics']['depth_mae_m'] is None

def test_nonfloor_hits_remain_separate_and_bad_prediction_shape_is_rejected():
    import pytest
    r=trace_frame(observation(.8),np.array([[.8]],np.float32),[0,0,3,3],.1,1.2)
    assert r['nonfloor_support'].any()
    assert not r['floor_support'].any()
    with pytest.raises(ValueError):trace_frame(observation(),np.zeros((2,2)),[0,0,3,3],.1,1.2)

def test_shared_cell_support_is_a_union_not_an_additive_attribution():
    import pytest
    floor=trace_frame(observation(),np.array([[.8]],np.float32),[0,0,3,3],.1,1.2)
    other=trace_frame(observation(.8),np.array([[.8]],np.float32),[0,0,3,3],.1,1.2)
    base=np.zeros((30,30),np.int8);selected=base.copy();selected[15,15]=1
    s=summarize_support([floor,other],base,selected)
    assert s['conflict_cells']==1 and s['floor_supported_conflict_cells']==1
    assert s['floor_only_conflict_cells']==0
    assert s['supporting_frame_histogram']=={'2':1}
    with pytest.raises(ValueError):summarize_support([floor],base,base)
    with pytest.raises(ValueError):summarize_support([floor],base[0],selected)

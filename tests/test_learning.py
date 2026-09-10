import numpy as np
from carespace.learned import metric_scale, prediction_key

def test_canonical_focal_scaling_is_not_gt_alignment():
    K=np.diag([150.,150.,1.])
    np.testing.assert_allclose(metric_scale(np.ones((2,2))*6,K),3)
    K[0,0]=300;K[1,1]=300
    np.testing.assert_allclose(metric_scale(np.ones((2,2))*6,K),6)

def test_prediction_cache_changes_with_image_and_intrinsics():
    rgb=np.zeros((2,2,3),np.uint8);K=np.eye(3)
    a=prediction_key(rgb,K)
    rgb[0,0]=255
    assert prediction_key(rgb,K)!=a
    rgb[:]=0;K[0,0]=2
    assert prediction_key(rgb,K)!=a

def test_cache_includes_shape_even_when_bytes_are_identical():
    assert prediction_key(np.zeros((2,6,3),np.uint8),np.eye(3)) != prediction_key(np.zeros((3,4,3),np.uint8),np.eye(3))

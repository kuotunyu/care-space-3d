from carespace.evaluation import classification_metrics
from carespace.scenes import build_scene,oracle_grid
from carespace.planning import analyze

def test_unknown_does_not_improve_decision_coverage():
    m=classification_metrics(["unknown","unknown"],["blocked","passable"])
    assert m["decision_coverage"]==0
    assert m["false_release_per_predicted_pass"] is None
    m=classification_metrics(["passable","blocked"],["blocked","passable"])
    assert m["false_release_per_oracle_blocked"]==1

def test_analytic_reference_and_scene_edit():
    normal=build_scene("normal",False);blocked=build_scene("blocked",False)
    assert normal.scene_id!=blocked.scene_id
    assert analyze(oracle_grid(normal),normal.start,normal.goal)["status"]=="passable"
    assert analyze(oracle_grid(blocked),blocked.start,blocked.goal)["status"]=="blocked"

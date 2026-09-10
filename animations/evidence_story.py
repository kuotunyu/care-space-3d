"""Original 2D observation illustration, independent of ReplicaCAD/study artifacts."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from carespace.contracts import Grid
from carespace.planning import analyze, bfs, inflated_states

RESOLUTION = .2
RADIUS = .12
CAMERAS = [(5, 10), (26, 10)]
START, GOAL = (6, 10), (25, 10)

def observe(geometry, camera, previous):
    evidence = previous.copy()
    traces = []
    for angle in np.linspace(0, 2*np.pi, 720, endpoint=False):
        direction = np.array([np.cos(angle), np.sin(angle)])
        origin = np.array(camera) + .5
        last = None
        for distance in np.arange(0, 45, .15):
            point = origin + direction * distance
            cell = tuple(np.floor(point).astype(int))
            if not (0 <= cell[0] < 32 and 0 <= cell[1] < 20): break
            if geometry[cell]:
                evidence[cell] = 1
                last = point
                break
            if evidence[cell] != 1: evidence[cell] = 0
            last = point
        traces.append((origin, last))
    return evidence, traces

def build_story():
    geometry = np.zeros((32, 20), dtype=bool)
    geometry[[0, -1], :] = True
    geometry[:, [0, -1]] = True
    geometry[15:17, 6:14] = True
    initial = np.full(geometry.shape, -1, dtype=np.int8)
    first, rays1 = observe(geometry, CAMERAS[0], initial)
    second, rays2 = observe(geometry, CAMERAS[1], first)
    grids = [Grid(s, [0, 0], RESOLUTION, 'original-explainer-v1') for s in [initial, first, second]]
    start, goal = grids[0].position(START), grids[0].position(GOAL)
    results = [analyze(g, start, goal, RADIUS) for g in grids]
    optimistic = bfs(inflated_states(grids[1], RADIUS) != 1, START, GOAL)
    assert [r['status'] for r in results] == ['unknown', 'unknown', 'passable']
    assert first[GOAL] == -1 and not np.any((first == 0) & geometry)
    assert not np.any((second == 0) & geometry)
    assert np.all(second[first == 1] == 1)
    assert optimistic and results[2]['path']
    return grids, results, optimistic, [rays1, rays2]

if __name__ == '__main__':
    grids, results, _, _ = build_story()
    print([(r['status'], int((g.states == -1).sum())) for g, r in zip(grids, results)])

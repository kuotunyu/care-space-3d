"""Fixed evidence and endpoints; vary only the planner's circular footprint."""
import numpy as np
from evidence_story import build_story, START, GOAL
from carespace.planning import analyze, inflated_states

RADII = (.12, .25, .35)

def build_footprint_story():
    grid = build_story()[0][-1]
    original = grid.states.copy()
    start, goal = grid.position(START), grid.position(GOAL)
    states = [inflated_states(grid, radius) for radius in RADII]
    results = [analyze(grid, start, goal, radius) for radius in RADII]
    assert [r['status'] for r in results] == ['passable', 'passable', 'blocked']
    assert np.array_equal(original, grid.states), 'Radius queries must not alter evidence.'
    for previous, current in zip(states, states[1:]):
        assert np.all(current[previous == 1] == 1), 'Blocked space must grow monotonically.'
    for state, result in zip(states, results):
        # Endpoints remain free: the final failure is a disconnected passage.
        assert state[START] == state[GOAL] == 0
        cells = [grid.cell(p) for p in result['path']]
        if cells:
            assert cells[0] == START and cells[-1] == GOAL
            assert all(state[c] == 0 for c in cells)
            assert all(sum(abs(a-b) for a,b in zip(c,d)) == 1
                       for c,d in zip(cells, cells[1:]))
    return grid, states, results

if __name__ == '__main__':
    grid, states, results = build_footprint_story()
    print([{'radius_m': radius, 'status': result['status'],
            'blocked_center_cells': int((state == 1).sum())}
           for radius, state, result in zip(RADII, states, results)])

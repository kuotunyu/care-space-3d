"""Conservative circular-footprint connectivity, never silently treating unknown as free."""
from collections import deque
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

def inflated_states(grid,radius):
    if not np.isfinite(radius) or radius<0 or radius>3:
        raise ValueError("Radius must be finite and in [0,3] metres")
    r=grid.resolution
    limit=radius+np.sqrt(2)*r
    n=int(np.ceil(limit/r))
    x,z=np.mgrid[-n:n+1,-n:n+1]
    disk=(x*r)**2+(z*r)**2<=limit**2+1e-12
    blocked=binary_dilation(grid.states==1,structure=disk,border_value=1)
    unknown=binary_dilation(grid.states==-1,structure=disk,border_value=0)
    out=np.zeros(grid.states.shape,np.int8);out[unknown]=-1;out[blocked]=1
    return out

def bfs(allowed,start,goal):
    nx,nz=allowed.shape
    if not (0<=start[0]<nx and 0<=start[1]<nz and 0<=goal[0]<nx and 0<=goal[1]<nz):
        return None
    if not allowed[start] or not allowed[goal]: return None
    queue=deque([start]);parent={start:None}
    while queue:
        here=queue.popleft()
        if here==goal:
            path=[]
            while here is not None: path.append(here);here=parent[here]
            return path[::-1]
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
            nxt=(here[0]+dx,here[1]+dz)
            if 0<=nxt[0]<nx and 0<=nxt[1]<nz and allowed[nxt] and nxt not in parent:
                parent[nxt]=here;queue.append(nxt)
    return None

def analyze(grid,start,goal,radius=.3):
    if len(start)!=2 or len(goal)!=2 or not np.isfinite([*start,*goal]).all():
        raise ValueError("Finite XZ endpoints required")
    states=inflated_states(grid,radius)
    a,b=grid.cell(start),grid.cell(goal)
    path=bfs(states==0,a,b)
    if path is not None:
        status="passable";reason="A complete observed-free swept-cylinder path exists."
    elif bfs(states!=1,a,b) is None:
        status="blocked";reason="Occupied geometry or domain boundary disconnects the endpoints even allowing unknown."
    else:
        status="unknown";reason="Potential connection crosses unobserved space; more observations required."
    clearance=None
    if path:
        # Unknown also limits the certifiable clearance; outside domain is occupied.
        distance=distance_transform_edt(np.pad(grid.states==0,1,constant_values=False))[1:-1,1:-1]*grid.resolution
        clearance=max(0.,float(min(distance[c] for c in path)-grid.resolution/np.sqrt(2)))
    return {"status":status,"path":[grid.position(c) for c in (path or [])],
            "start":list(start),"goal":list(goal),"clearance_m":clearance,"reason":reason}

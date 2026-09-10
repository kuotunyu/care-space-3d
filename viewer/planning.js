// Shared browser connectivity primitive. Endpoints obey the same evidence rule as edges.
export function parseEndpoint(x, z) {
  if ([x, z].some(value => String(value).trim() === '')) return null;
  const point = [Number(x), Number(z)];
  return point.every(Number.isFinite) ? point : null;
}

// Same circular footprint and outside-domain policy as the original browser planner.
export function stateLookup(grid, states, radius) {
  states=states??[]; // An unavailable reconstruction supplies no free evidence.
  const [nx,nz]=grid.shape,res=grid.resolution,threshold=radius+Math.SQRT2*res;
  const reach=Math.ceil(threshold/res),cache=new Int8Array(nx*nz).fill(2);
  return (ix,iz)=>{
    if(ix<0||iz<0||ix>=nx||iz>=nz)return 1;
    const key=ix*nz+iz;if(cache[key]!==2)return cache[key];
    let unknown=false;
    for(let dx=-reach;dx<=reach;dx++)for(let dz=-reach;dz<=reach;dz++){
      if(Math.hypot(dx*res,dz*res)>threshold)continue;
      const x=ix+dx,z=iz+dz;
      if(x<0||z<0||x>=nx||z>=nz)return cache[key]=1;
      const value=states[x*nz+z]??-1;
      if(value===1)return cache[key]=1;
      if(value===-1)unknown=true;
    }
    return cache[key]=unknown?-1:0;
  };
}

export function bfs(start,goal,allowed,stateAt){
  if(!allowed(stateAt(...start))||!allowed(stateAt(...goal)))return [];
  const key=([x,z])=>`${x},${z}`,q=[start],parent=new Map([[key(start),null]]);
  for(let n=0;n<q.length;n++){
    const p=q[n];
    if(p[0]===goal[0]&&p[1]===goal[1]){
      const path=[];let cur=p;
      while(cur){path.push(cur);cur=parent.get(key(cur))}
      return path.reverse();
    }
    for(const d of [[1,0],[-1,0],[0,1],[0,-1]]){
      const v=[p[0]+d[0],p[1]+d[1]],k=key(v);
      if(!parent.has(k)&&allowed(stateAt(...v))){parent.set(k,p);q.push(v)}
    }
  }
  return [];
}

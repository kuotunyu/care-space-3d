// Shared browser connectivity primitive. Endpoints obey the same evidence rule as edges.
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

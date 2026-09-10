import {bfs,stateLookup} from './planning.js';

function sameFrames(a,b){
  return [a,b].every(m=>Array.isArray(m.selected_frames)&&m.selected_frames.length>0)&&
    JSON.stringify([...a.selected_frames].sort((x,y)=>x-y))===JSON.stringify([...b.selected_frames].sort((x,y)=>x-y));
}

export function chooseBaseline(methods, selected) {
  const id=selected.id.startsWith('da3-')?selected.id.slice(4):'all';
  const baseline=methods.find(m=>m.id===id&&m!==selected);
  if(selected.id.startsWith('da3-')&&(!baseline||!sameFrames(baseline,selected)))return null;
  return baseline||null;
}

function validate(grid, method) {
  const [nx,nz]=grid.shape||[];
  if(!Number.isInteger(nx)||!Number.isInteger(nz)||nx<=0||nz<=0||
     !Number.isFinite(grid.resolution)||grid.resolution<=0||
     !Array.isArray(grid.bounds)||grid.bounds.length!==4||!grid.bounds.every(Number.isFinite))throw new Error('Invalid grid geometry');
  if(Math.abs(grid.bounds[2]-grid.bounds[0]-nx*grid.resolution)>1e-8||
     Math.abs(grid.bounds[3]-grid.bounds[1]-nz*grid.resolution)>1e-8)throw new Error('Grid extent mismatch');
  if(!Array.isArray(method.states)||method.states.length!==nx*nz||method.states.some(v=>![-1,0,1].includes(v)))throw new Error('Incomplete or invalid evidence grid');
}

export function diagnose(grid, baseline, selected, radius, start, goal) {
  validate(grid,baseline);validate(grid,selected);
  if(selected.id.startsWith('da3-')&&!sameFrames(baseline,selected))throw new Error('DA3 comparison requires identical observed frame IDs');
  if(!Number.isFinite(radius)||radius<0||radius>3||![start,goal].every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)))throw new Error('Invalid query');
  const matrix=Array.from({length:3},()=>[0,0,0]); // rows baseline, columns selected; -1,0,1.
  const groups={conflict:[],lost:[],gained:[]};
  baseline.states.forEach((a,i)=>{
    const b=selected.states[i];matrix[a+1][b+1]++;
    if(a===b)return;
    if(a===-1)groups.gained.push(i);
    else if(b===-1)groups.lost.push(i);
    else groups.conflict.push(i);
  });
  const knownBoth=matrix[1][1]+matrix[1][2]+matrix[2][1]+matrix[2][2];
  const cell=p=>[Math.floor((p[0]-grid.bounds[0])/grid.resolution),Math.floor((p[1]-grid.bounds[1])/grid.resolution)];
  const point=([x,z])=>[grid.bounds[0]+(x+.5)*grid.resolution,grid.bounds[1]+(z+.5)*grid.resolution];
  const a=cell(start),b=cell(goal),baseAt=stateLookup(grid,baseline.states,radius),selectedAt=stateLookup(grid,selected.states,radius);
  function route(at){
    const free=bfs(a,b,v=>v===0,at);
    return {status:free.length?'passable':bfs(a,b,v=>v!==1,at).length?'unknown':'blocked',free};
  }
  const baseRoute=route(baseAt),selectedRoute=route(selectedAt);
  let path=null;
  if(baseRoute.free.length){
    const restricted=baseRoute.free.filter(p=>selectedAt(...p)!==0);
    path={total:baseRoute.free.length,blocked:baseRoute.free.filter(p=>selectedAt(...p)===1).length,
      unknown:baseRoute.free.filter(p=>selectedAt(...p)===-1).length,
      first_restricted_center:restricted.length?point(restricted[0]):null};
  }
  return {baseline_id:baseline.id,selected_id:selected.id,
    same_frames:sameFrames(baseline,selected),
    total:baseline.states.length,matrix,state_order:[-1,0,1],groups,
    counts:Object.fromEntries(Object.entries(groups).map(([key,indices])=>[key,indices.length])),
    known_both:knownBoth,known_conflict_fraction:knownBoth?groups.conflict.length/knownBoth:null,
    baseline_status:baseRoute.status,selected_status:selectedRoute.status,
    endpoints:{baseline:[baseAt(...a),baseAt(...b)],selected:[selectedAt(...a),selectedAt(...b)]},path};
}

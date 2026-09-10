import {test} from 'node:test';
import assert from 'node:assert/strict';
import {diagnose, chooseBaseline} from '../viewer/diagnostics.js';
import {stateLookup} from '../viewer/planning.js';
const fixture=()=>({shape:[12,12],bounds:[0,0,12,12],resolution:1});
const method=(id,states)=>({id,label:id,states,selected_frames:[0],result:{start:[3.5,6.5],goal:[8.5,6.5]}});

test('unknown transitions are coverage differences, never known occupancy conflicts',()=>{
  const c=fixture(),a=Array(144).fill(0),b=[...a];
  b[0]=1;b[1]=-1;a[2]=-1;a[3]=1;
  const d=diagnose(c,method('all',a),method('da3-all',b),.3,[3.5,6.5],[8.5,6.5]);
  assert.equal(d.counts.conflict,2);assert.equal(d.counts.lost,1);assert.equal(d.counts.gained,1);
  assert.equal(d.known_both,142);assert.equal(d.matrix.flat().reduce((a,b)=>a+b),144);
});
test('absent reconstruction cells stay unknown and the padded boundary stays blocked',()=>{
  const at=stateLookup(fixture(),undefined,.3);
  assert.equal(at(6,6),-1);assert.equal(at(0,0),1);
});
test('a blocked baseline path is not evidence that every alternate path is blocked',()=>{
  const c=fixture(),a=Array(144).fill(0),b=[...a];b[6*12+6]=1;
  const d=diagnose(c,method('all',a),method('da3-all',b),.1,[3.5,6.5],[8.5,6.5]);
  assert.ok(d.path.blocked>0);assert.equal(d.selected_status,'passable');
});
test('all-unknown grids have no known comparison or baseline free-path denominator',()=>{
  const c=fixture(),a=method('all',Array(144).fill(-1));
  const d=diagnose(c,a,{...a,id:'da3-all'},.3,[3.5,6.5],[8.5,6.5]);
  assert.equal(d.known_conflict_fraction,null);assert.equal(d.path,null);
  assert.equal(d.selected_status,'unknown');
});
test('missing cells and invalid states are rejected rather than becoming free',()=>{
  const c=fixture(),a=method('all',Array(144).fill(0));
  assert.throws(()=>diagnose(c,a,{...a,states:[]},.3,[3,6],[8,6]));
  assert.throws(()=>diagnose(c,a,{...a,states:Array(144).fill(2)},.3,[3,6],[8,6]));
  assert.throws(()=>diagnose({...c,bounds:[0,0,4,4]},a,a,.3,[6.5,6.5],[8.5,6.5]));
});
test('DA3 interval uses the matching RGB-D interval, not the full observation baseline',()=>{
  const all={id:'all',selected_frames:[0,1,2]},interval={id:'interval',selected_frames:[0,2]},da3={id:'da3-interval',selected_frames:[2,0]};
  assert.equal(chooseBaseline([all,interval,da3],da3),interval);
  assert.equal(chooseBaseline([all,da3],da3),null);
  assert.equal(chooseBaseline([all,interval],interval),all);
  assert.equal(chooseBaseline([interval],{...da3,selected_frames:[1,2]}),null);
  assert.equal(chooseBaseline([interval],{...da3,selected_frames:undefined}),null);
  const c=fixture(),a=method('all',Array(144).fill(0));
  assert.throws(()=>diagnose(c,a,{...a,id:'da3-all',selected_frames:[1]},.3,[3,6],[8,6]));
});

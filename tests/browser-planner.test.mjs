import {test} from 'node:test';
import assert from 'node:assert/strict';
import {bfs} from '../viewer/planning.js';

test('unknown start cannot escape into a known-free path',()=>{
  const at=(x,z)=> x<0||z<0||x>=3||z>=3?1:(x===0&&z===1?-1:0);
  assert.deepEqual(bfs([0,1],[2,1],v=>v===0,at),[]);
  assert.ok(bfs([0,1],[2,1],v=>v!==1,at).length>0);
});
test('same unknown start and goal is not an observed-free route',()=>{
  const at=()=>-1;
  assert.deepEqual(bfs([0,0],[0,0],v=>v===0,at),[]);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { canPlaceEndpoint, isBaselineQuery } from '../viewer/interaction.js';

test('瀏覽與相機操作不能改端點', () => {
  assert.equal(canPlaceEndpoint('browse'), false);
  assert.equal(canPlaceEndpoint('camera'), false);
});
test('只有明確設定端點模式可以改端點', () => {
  assert.equal(canPlaceEndpoint('start'), true);
  assert.equal(canPlaceEndpoint('goal'), true);
  assert.equal(canPlaceEndpoint('invalid'), false);
});

test('自訂半徑或端點不能冒充保存條件', () => {
  const baseline = {radius:.3,start:[1.25,3.05],goal:[6.75,3.05]};
  assert.equal(isBaselineQuery(baseline,baseline), true);
  assert.equal(isBaselineQuery({...baseline,radius:.4},baseline), false);
  assert.equal(isBaselineQuery({...baseline,start:[1.35,3.05]},baseline), false);
  assert.equal(isBaselineQuery({...baseline,goal:[6.75,3.15]},baseline), false);
  assert.equal(isBaselineQuery({...baseline,radius:NaN},baseline), false);
  assert.equal(isBaselineQuery({...baseline,start:null},baseline), false);
  assert.equal(isBaselineQuery(baseline,{...baseline,radius:Infinity}), false);
});

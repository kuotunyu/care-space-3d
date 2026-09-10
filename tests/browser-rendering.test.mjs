import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { createRenderScheduler, disposeObject } from '../viewer/rendering.js';

test('redraw requests coalesce and settle when interaction stops', () => {
  const callbacks = [];
  let draws = 0;
  const requestRender = createRenderScheduler(() => { draws++; }, cb => callbacks.push(cb));
  requestRender(); requestRender(); requestRender();
  assert.equal(callbacks.length, 1);
  callbacks.shift()();
  assert.equal(draws, 1);
  assert.equal(callbacks.length, 0);
  requestRender();
  callbacks.shift()();
  assert.equal(draws, 2);
});

test('nested assets, shared textures and instance buffers are disposed exactly once', () => {
  const scene = new THREE.Scene(), root = new THREE.Group(), nested = new THREE.Group();
  const geometry = new THREE.BoxGeometry(), texture = new THREE.Texture();
  const material = new THREE.MeshBasicMaterial({ map: texture });
  scene.add(root); root.add(nested);
  nested.add(new THREE.Mesh(geometry, material), new THREE.Mesh(geometry, material));
  const instances = new THREE.InstancedMesh(geometry, material, 2);
  nested.add(instances);
  const counts = [0, 0, 0, 0];
  [geometry, texture, material, instances].forEach((resource, i) => resource.addEventListener('dispose', () => counts[i]++));
  disposeObject(root);
  assert.deepEqual(counts, [1, 1, 1, 1]);
  assert.equal(scene.children.length, 0);
});

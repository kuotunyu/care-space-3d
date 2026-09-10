// Shared assets in a GLTF hierarchy must be released exactly once, including textures.
export function disposeObject(root) {
  const resources = new Set();
  root.traverse(object => {
    // Three releases per-instance GPU buffers on the mesh's own dispose event.
    if (object.isInstancedMesh) resources.add(object);
    if (object.geometry) resources.add(object.geometry);
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials.filter(Boolean)) {
      resources.add(material);
      for (const value of Object.values(material)) {
        if (value?.isTexture) resources.add(value);
      }
    }
  });
  for (const resource of resources) resource.dispose();
  root.removeFromParent();
}

// OrbitControls' change events keep damping alive; an idle view schedules no frames.
export function createRenderScheduler(draw, requestFrame = requestAnimationFrame) {
  let pending = false;
  return function requestRender() {
    if (pending) return;
    pending = true;
    requestFrame(() => {
      pending = false;
      draw();
    });
  };
}

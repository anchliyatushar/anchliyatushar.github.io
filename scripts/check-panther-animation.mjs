/** Check the real timeline and the exported model's screen framing. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import sharp from 'sharp';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import {
  ASSEMBLY_DEPTHS, CAMERA_FOV, DURATION, STATIC_TIME, getPantherFrame,
} from '../src/scripts/panther-timeline.ts';

function near(actual, expected, tolerance, message) {
  assert.ok(Math.abs(actual - expected) <= tolerance, `${message}: ${actual} vs ${expected}`);
}

function continuousValues(frame) {
  return [...frame.rotation, ...frame.camera, ...frame.target, frame.exploded, frame.technical, frame.sweep];
}

// Each cut point, including the wrap, must preserve both position and velocity.
const epsilon = .001;
for (const time of [0, .4, 1, 2.2, 3.1, 3.35, 4.5, 6, DURATION]) {
  const before = continuousValues(getPantherFrame(time - epsilon));
  const at = continuousValues(getPantherFrame(time));
  const after = continuousValues(getPantherFrame(time + epsilon));
  at.forEach((value, index) => {
    near(before[index], value, .00001, `Position before ${time}s, channel ${index}`);
    near(after[index], value, .00001, `Position after ${time}s, channel ${index}`);
    const leftVelocity = (value - before[index]) / epsilon;
    const rightVelocity = (after[index] - value) / epsilon;
    near(leftVelocity, rightVelocity, .0001, `Velocity at ${time}s, channel ${index}`);
  });
}
assert.deepEqual(getPantherFrame(0), getPantherFrame(DURATION));
assert.equal(DURATION, 6.875, 'Only the faster final Form & finish should shorten the loop to 6.875 seconds');

// Only the final Form & finish return is faster again. Keep every earlier
// phase through six seconds pinned to the already-approved pacing.
near(getPantherFrame(.4).pullback, 0, 0, 'Opening hold ends after .4 seconds');
near(getPantherFrame(.7).pullback, .5, .00001, 'Camera is halfway through the .6-second pullback');
near(getPantherFrame(1).pullback, 1, 0, 'Full view reached within one second');
near(getPantherFrame(1.6).technical, .5, .00001, 'Technical reveal keeps its 1.2-second duration');
near(getPantherFrame(5.25).technical, .5, .00001, 'Finish restoration keeps its 1.5-second duration');
near(getPantherFrame(6).pullback, 1, 0, 'Final return still begins at six seconds');
near(getPantherFrame(6.4375).pullback, .5, .00001, 'Final camera return takes .875 seconds');

// The shortened assembly chapter lasts 2.3 seconds, with only a quarter-second
// fully separated hold before the parts begin returning to the final piece.
assert.equal(getPantherFrame(2.2).chapter, '03|The assembly');
assert.equal(getPantherFrame(4.5).chapter, '02|Beneath the surface');
near(getPantherFrame(2.65).exploded, .5, .00001, 'Separation retains its .9-second duration');
near(getPantherFrame(3.1).exploded, 1, 0, 'Start of separated hold');
near(getPantherFrame(3.35).exploded, 1, 0, 'End of separated hold');
near(getPantherFrame(3.925).exploded, .5, .00001, 'Reassembly retains its 1.15-second duration');
near(getPantherFrame(4.5).exploded, 0, 0, 'Assembly complete within 2.3 seconds');
near(getPantherFrame(6).technical, 0, 0, 'Polished finish restored before camera return');
assert.equal(getPantherFrame(6).chapter, '01|Form & finish');

// Geometry can separate only after the technical view has fully appeared;
// the polished finish can return only when every assembly is back in place.
for (let time = 0; time < DURATION; time += .05) {
  const frame = getPantherFrame(time);
  for (const value of [frame.pullback, frame.technical, frame.exploded]) {
    assert.ok(value >= 0 && value <= 1, `Phase overshoot at ${time}s`);
  }
  if (frame.exploded > .00001) near(frame.technical, 1, .00001, `Separation before CAD at ${time}s`);
  if (frame.technical < .99999) near(frame.exploded, 0, .00001, `Finish before reassembly at ${time}s`);
}
const staticFrame = getPantherFrame(STATIC_TIME);
near(staticFrame.exploded, 0, 0, 'Reduced-motion assembly');
near(staticFrame.technical, 0, 0, 'Reduced-motion finish');
near(staticFrame.pullback, 1, 0, 'Reduced-motion full view');

// Test actual mesh vertices, including the true depth separation, rather than
// approximate bounding rectangles that can miss clipping during rotation.
const buffer = await readFile(new URL('../public/models/panther-bloom.glb', import.meta.url));
const model = (await new GLTFLoader().parseAsync(
  buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength), '',
)).scene;
const rig = new THREE.Group();
rig.add(model);
const meshes = [];
const assemblies = [];
model.traverse((node) => {
  if (node.isMesh) meshes.push(node);
  if (Object.hasOwn(ASSEMBLY_DEPTHS, node.name)) {
    assemblies.push({ node, origin: node.position.clone(), depth: ASSEMBLY_DEPTHS[node.name] });
  }
});
assert.equal(assemblies.length, 4, 'All four construction groups must animate');
assert.ok(meshes.length > 0, 'The model must contain renderable geometry');

// Loading and no-WebGL states must show the same object, never the old shirt
// photograph. A blank/opaque export would also make the handoff visibly flash.
const component = await readFile(new URL('../src/components/PantherBloomTransformation.astro', import.meta.url), 'utf8');
assert.match(component, /assets\/generated\/panther-bloom-opening-gold\.png/, 'Use the refreshed gold opening-frame poster');
assert.doesNotMatch(component, /final-panther-bloom-male-detail/, 'The shirt photograph must not be the loading poster');
const poster = sharp(await readFile(new URL('../src/assets/generated/panther-bloom-opening-gold.png', import.meta.url)));
const posterMetadata = await poster.metadata();
assert.equal(posterMetadata.width, posterMetadata.height, 'Poster must preserve the square camera frame');
assert.ok(posterMetadata.width >= 800, 'Poster must retain crisp desktop detail');
assert.ok(posterMetadata.hasAlpha, 'Poster background must match the live transparent canvas');
const alpha = (await poster.stats()).channels[3];
assert.equal(alpha.min, 0);
assert.equal(alpha.max, 255);
assert.ok(alpha.mean > 5 && alpha.mean < 240, 'Poster must contain a visible brooch on transparency');

const camera = new THREE.PerspectiveCamera(CAMERA_FOV, 1, .1, 70);
const vertex = new THREE.Vector3();
let largestExtent = 0;
for (const aspect of [.75, 1, 1.5]) {
  camera.aspect = aspect;
  camera.updateProjectionMatrix();
  for (const time of [0, .4, .7, 1, 1.6, 2.2, 2.65, 3.1, 3.35, 3.925, 4.5, 5.25, 6, 6.4375]) {
    const frame = getPantherFrame(time, aspect);
    rig.rotation.set(...frame.rotation);
    camera.position.set(...frame.camera);
    camera.lookAt(...frame.target);
    for (const assembly of assemblies) {
      assembly.node.position.copy(assembly.origin);
      assembly.node.position.z += assembly.depth * frame.exploded;
    }
    rig.updateMatrixWorld(true);
    camera.updateMatrixWorld(true);
    for (const mesh of meshes) {
      const positions = mesh.geometry.attributes.position;
      for (let index = 0; index < positions.count; index++) {
        vertex.fromBufferAttribute(positions, index).applyMatrix4(mesh.matrixWorld).project(camera);
        const extent = Math.max(Math.abs(vertex.x), Math.abs(vertex.y));
        largestExtent = Math.max(largestExtent, extent);
        assert.ok(extent <= .91, `Brooch crosses safe frame at ${time}s / aspect ${aspect}: ${extent}`);
        assert.ok(vertex.z > -1 && vertex.z < 1, `Brooch crosses camera clip plane at ${time}s`);
      }
    }
  }
}
console.log(`Panther checks passed: seamless timing, sequence order, matching transparent loading poster, and 42 actual-mesh views (${(largestExtent * 100).toFixed(1)}% maximum half-frame extent).`);

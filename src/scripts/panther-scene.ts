import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { ASSEMBLY_DEPTHS, CAMERA_FOV, DURATION, STATIC_TIME, getPantherFrame } from './panther-timeline';

type Assembly = { node: THREE.Object3D; origin: THREE.Vector3; offset: THREE.Vector3 };

// One spatial sweep changes the actual surface, not a stack of unrelated images.
function studySurface(source: THREE.MeshStandardMaterial, sweep: { value: number }) {
  const gem = /gem|sapphire|stone|diamond|blue/i.test(source.name);
  const eye = source.name === 'black-onyx-eyes';
  const finishes: Record<string, string> = {
    'polished-gold': '#d5a445',
    'pale-gold-settings': '#c3a35f',
    'sapphire-centre': '#091d4b',
    'blue-pave-stones': '#183567',
    'ice-blue-stones': '#82abba',
    'black-onyx-eyes': '#070809',
  };
  const material = new THREE.MeshPhysicalMaterial({
    name: source.name,
    color: finishes[source.name] ?? source.color,
    metalness: gem || eye ? 0 : 1,
    roughness: eye ? .18 : gem ? .075 : .28,
    transmission: gem ? .4 : 0,
    thickness: gem ? .16 : 0,
    attenuationColor: finishes[source.name] ?? source.color,
    attenuationDistance: .5,
    clearcoat: eye ? .65 : gem ? 1 : .04,
    clearcoatRoughness: .12,
    ior: eye ? 1.54 : gem ? 1.77 : 1.5,
    envMapIntensity: eye ? .65 : gem ? .9 : 1,
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1,
  });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uStudySweep = sweep;
    shader.vertexShader = 'varying vec3 vStudyPosition;\n' + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvStudyPosition = position;');
    shader.fragmentShader = 'uniform float uStudySweep;\nvarying vec3 vStudyPosition;\n' + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>', `
      float studyMix = smoothstep(uStudySweep - .16, uStudySweep + .16, vStudyPosition.y);
      float studyLight = .30 + .70 * max(0., dot(normal, normalize(vec3(-.5, .8, 1.))));
      vec3 studyInk = vec3(.030, .075, .090) * studyLight;
      outgoingLight = mix(outgoingLight, studyInk + outgoingLight * .085, studyMix);
      #include <opaque_fragment>
    `);
  };
  material.customProgramCacheKey = () => 'panther-surface-study-v1';
  return material;
}

function studyEdges(sweep: { value: number }) {
  const material = new THREE.LineBasicMaterial({ color: 0xa9d3d9, transparent: true, opacity: .4, depthWrite: false });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uStudySweep = sweep;
    shader.vertexShader = 'varying vec3 vStudyPosition;\n' + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvStudyPosition = position;');
    shader.fragmentShader = 'uniform float uStudySweep;\nvarying vec3 vStudyPosition;\n' + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace('#include <color_fragment>', `
      #include <color_fragment>
      diffuseColor.a *= smoothstep(uStudySweep - .16, uStudySweep + .16, vStudyPosition.y);
    `);
  };
  material.customProgramCacheKey = () => 'panther-edges-study-v1';
  return material;
}

export function mountPantherStudy(container: HTMLElement) {
  if (container.dataset.mounted) return;
  container.dataset.mounted = 'true';
  const host = container.querySelector<HTMLElement>('[data-panther-canvas]')!;
  const button = container.querySelector<HTMLButtonElement>('[data-panther-pause]')!;
  const caption = container.querySelector<HTMLElement>('[data-panther-caption]')!;
  const number = container.querySelector<HTMLElement>('[data-panther-number]')!;
  const progress = container.querySelector<HTMLElement>('[data-panther-progress]')!;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const qaParams = import.meta.env.DEV ? new URLSearchParams(location.search) : null;
  // Local QA can inspect the server-rendered fallback without waiting for WebGL.
  if (qaParams?.has('panther-still')) return;
  let renderer: THREE.WebGLRenderer;
  try {
    renderer = new THREE.WebGLRenderer({
      alpha: true, antialias: true, powerPreference: 'high-performance',
      // A local authoring view captures the exact opening frame as the poster.
      preserveDrawingBuffer: qaParams?.has('panther-poster') ?? false,
    });
  } catch {
    return; // The matching brooch still remains usable without WebGL.
  }
  renderer.setPixelRatio(Math.min(devicePixelRatio, matchMedia('(max-width: 600px)').matches ? 1.5 : 2));
  renderer.setClearColor(0x070908, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .92;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  host.append(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(CAMERA_FOV, 1, .1, 70);
  const rig = new THREE.Group();
  scene.add(rig);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const studio = new RoomEnvironment();
  // Bright studio bounce keeps broad polished leaves yellow-gold instead of
  // reflecting the dark room as brown. Preserve the same gold finish on every part.
  studio.add(new THREE.AmbientLight(0xfff4de, .8));
  const environment = pmrem.fromScene(studio, .08);
  scene.environment = environment.texture;
  scene.environmentRotation.set(.1, .45, -.12);
  studio.dispose();
  pmrem.dispose();
  const key = new THREE.DirectionalLight(0xfff1d5, 1.1);
  key.position.set(-4, 5, 8);
  key.castShadow = true;
  const shadowSize = matchMedia('(max-width: 600px)').matches ? 1024 : 2048;
  key.shadow.mapSize.set(shadowSize, shadowSize);
  Object.assign(key.shadow.camera, { left: -3.5, right: 3.5, top: 3.5, bottom: -3.5, near: .1, far: 20 });
  key.shadow.normalBias = .008;
  key.shadow.bias = -.00005;
  const fill = new THREE.DirectionalLight(0xc2d9ed, .45);
  fill.position.set(5, 1, 4);
  const rim = new THREE.DirectionalLight(0xffe5b0, 1);
  rim.position.set(-1, -2, -4);
  scene.add(key, fill, rim);

  const sweep = { value: 3.5 };
  const assemblies: Assembly[] = [];
  const materials = new Map<THREE.Material, THREE.MeshPhysicalMaterial>();
  const edgeMaterial = studyEdges(sweep);
  const edgeGeometries: THREE.EdgesGeometry[] = [];
  const edgeObjects: THREE.LineSegments[] = [];
  let model: THREE.Group | undefined;
  let disposed = false;
  let ready = false;
  let playing = !reduced.matches;
  let visible = true;
  let seconds = reduced.matches ? STATIC_TIME : 0;
  let previous = 0;
  let currentChapter = '';
  // Local-only, deterministic frames for visual QA. Not exposed on the deployed site.
  const qaValue = qaParams?.get('panther-time') ?? null;
  const qaTime = qaValue !== null && Number.isFinite(Number(qaValue)) ? Number(qaValue) % DURATION : null;

  function paint(t: number, render = true) {
    const state = getPantherFrame(t, camera.aspect);
    rig.rotation.set(...state.rotation);
    for (const assembly of assemblies) assembly.node.position.copy(assembly.origin).addScaledVector(assembly.offset, state.exploded);
    for (const edge of edgeObjects) edge.visible = state.technical > .001;
    sweep.value = state.sweep;
    camera.position.set(...state.camera);
    camera.lookAt(...state.target);
    const chapter = state.chapter;
    if (chapter !== currentChapter) {
      [number.textContent, caption.textContent] = chapter.split('|');
      currentChapter = chapter;
    }
    progress.style.transform = `scaleX(${state.progress})`;
    if (render) renderer.render(scene, camera);
    if (import.meta.env.DEV) container.dataset.phase = t.toFixed(2);
  }

  function frame(now: number) {
    if (disposed) return;
    if (!playing || !visible || document.hidden || qaTime !== null) {
      renderer.setAnimationLoop(null);
      previous = 0;
      return;
    }
    if (previous) seconds += Math.min((now - previous) / 1000, .05);
    previous = now;
    paint(qaTime ?? seconds % DURATION);
  }

  function resumeIfVisible() {
    renderer.setAnimationLoop(null);
    previous = 0;
    if (!ready || disposed) return;
    paint(qaTime ?? seconds % DURATION);
    if (playing && visible && !document.hidden && qaTime === null) renderer.setAnimationLoop(frame);
  }
  function updateButton() {
    button.dataset.paused = String(!playing);
    button.setAttribute('aria-label', playing ? 'Pause brooch animation' : 'Play brooch animation');
  }
  function toggle() { playing = !playing; updateButton(); resumeIfVisible(); }
  function motionChanged() { playing = !reduced.matches; seconds = reduced.matches ? STATIC_TIME : 0; updateButton(); resumeIfVisible(); }
  button.addEventListener('click', toggle);
  reduced.addEventListener('change', motionChanged);
  document.addEventListener('visibilitychange', resumeIfVisible);
  window.addEventListener('pageshow', resumeIfVisible);
  window.addEventListener('focus', resumeIfVisible);
  const contextLost = (event: Event) => { event.preventDefault(); renderer.setAnimationLoop(null); };
  const contextRestored = () => resumeIfVisible();
  renderer.domElement.addEventListener('webglcontextlost', contextLost);
  renderer.domElement.addEventListener('webglcontextrestored', contextRestored);
  const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; resumeIfVisible(); }, { threshold: .05 });
  observer.observe(container);
  const resize = new ResizeObserver(() => {
    const { width, height } = host.getBoundingClientRect();
    if (!width || !height) return;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (ready) paint(qaTime ?? seconds % DURATION);
  });
  resize.observe(host);

  function dispose() {
    if (disposed) return;
    disposed = true;
    renderer.setAnimationLoop(null);
    observer.disconnect();
    resize.disconnect();
    button.removeEventListener('click', toggle);
    reduced.removeEventListener('change', motionChanged);
    document.removeEventListener('visibilitychange', resumeIfVisible);
    window.removeEventListener('pageshow', resumeIfVisible);
    window.removeEventListener('focus', resumeIfVisible);
    renderer.domElement.removeEventListener('webglcontextlost', contextLost);
    renderer.domElement.removeEventListener('webglcontextrestored', contextRestored);
    document.removeEventListener('astro:before-swap', dispose);
    edgeGeometries.forEach((geometry) => geometry.dispose());
    model?.traverse((node) => { if (node instanceof THREE.Mesh) node.geometry.dispose(); });
    materials.forEach((material, original) => { material.dispose(); original.dispose(); });
    edgeMaterial.dispose();
    environment.dispose();
    key.shadow.dispose();
    renderer.dispose();
  }
  document.addEventListener('astro:before-swap', dispose, { once: true });

  new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}models/panther-bloom.glb`).then(async (gltf) => {
    if (disposed) {
      gltf.scene.traverse((node) => {
        if (node instanceof THREE.Mesh) {
          node.geometry.dispose();
          (Array.isArray(node.material) ? node.material : [node.material]).forEach((material) => material.dispose());
        }
      });
      return;
    }
    model = gltf.scene;
    rig.add(model);
    model.traverse((node) => {
      if (!/^(face|feather|botanical|gems)$/.test(node.name)) return;
      const depth = ASSEMBLY_DEPTHS[node.name as keyof typeof ASSEMBLY_DEPTHS];
      assemblies.push({ node, origin: node.position.clone(), offset: new THREE.Vector3(0, 0, depth) });
    });
    const meshes: THREE.Mesh[] = [];
    model.traverse((node) => { if (node instanceof THREE.Mesh) meshes.push(node); });
    const replace = (source: THREE.Material) => {
      if (!materials.has(source)) materials.set(source, studySurface(source as THREE.MeshStandardMaterial, sweep));
      return materials.get(source)!;
    };
    for (const mesh of meshes) {
      if (disposed) return;
      mesh.material = Array.isArray(mesh.material) ? mesh.material.map(replace) : replace(mesh.material);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      const geometry = new THREE.EdgesGeometry(mesh.geometry, 32);
      edgeGeometries.push(geometry);
      const edges = new THREE.LineSegments(geometry, edgeMaterial);
      edges.renderOrder = 1;
      edgeObjects.push(edges);
      mesh.add(edges);
      // Let the page remain responsive while feature edges are prepared.
      await new Promise<void>((resolve) => setTimeout(resolve, 0));
    }
    const { width, height } = host.getBoundingClientRect();
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    paint(qaTime ?? seconds, false);
    // iOS WebKit can delay or decline KHR_parallel_shader_compile. Never make
    // autoplay depend on that optional warm-up step.
    ready = true;
    host.removeAttribute('aria-hidden');
    container.dataset.ready = 'true';
    button.disabled = false;
    updateButton();
    resumeIfVisible();
    void renderer.compileAsync(scene, camera).catch(() => undefined);
    if (import.meta.env.DEV && qaParams?.has('panther-poster')) {
      // Keep the loading image in sync with geometry, lighting and framing.
      const download = document.createElement('a');
      download.href = renderer.domElement.toDataURL('image/png');
      download.download = 'panther-bloom-opening.png';
      download.textContent = 'Download opening frame';
      download.dataset.pantherExport = '';
      download.style.cssText = 'position:absolute;z-index:5;bottom:4.5rem;right:1rem;padding:.65rem;background:#070908;color:#d6b654;font:12px monospace;border:1px solid currentColor';
      container.append(download);
    }
  }).catch((error) => {
    console.warn('Panther study could not load; keeping the matching brooch still.', error);
    dispose();
  });
}

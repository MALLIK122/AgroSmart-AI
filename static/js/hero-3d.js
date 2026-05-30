// AgroSmart AI - Three.js agriculture globe & crop field
(function () {
  const canvas = document.getElementById('hero-3d-canvas');
  if (!canvas || typeof THREE === 'undefined') return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(0, 0.3, 5.5);

  const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance',
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const globeGeo = new THREE.IcosahedronGeometry(1.15, 2);
  const globeMat = new THREE.MeshBasicMaterial({
    color: 0x00ffa3,
    wireframe: true,
    transparent: true,
    opacity: 0.85,
  });
  const globe = new THREE.Mesh(globeGeo, globeMat);
  scene.add(globe);

  const innerGeo = new THREE.SphereGeometry(0.55, 16, 16);
  const innerMat = new THREE.MeshBasicMaterial({
    color: 0x00d4ff,
    transparent: true,
    opacity: 0.12,
  });
  const innerCore = new THREE.Mesh(innerGeo, innerMat);
  scene.add(innerCore);

  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(1.75, 0.03, 12, 80),
    new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.7 })
  );
  ring.rotation.x = Math.PI / 2.2;
  scene.add(ring);

  const ring2 = new THREE.Mesh(
    new THREE.TorusGeometry(2.1, 0.015, 8, 64),
    new THREE.MeshBasicMaterial({ color: 0xfbbf24, transparent: true, opacity: 0.35 })
  );
  ring2.rotation.x = Math.PI / 3;
  ring2.rotation.y = 0.4;
  scene.add(ring2);

  const grid = new THREE.GridHelper(5.5, 14, 0x00ffa3, 0x0a2830);
  grid.position.y = -1.35;
  scene.add(grid);

  const cropPlots = [];
  const plotCount = 10;
  for (let i = 0; i < plotCount; i++) {
    const angle = (i / plotCount) * Math.PI * 2;
    const h = 0.18 + (i % 3) * 0.12;
    const plot = new THREE.Mesh(
      new THREE.BoxGeometry(0.14, h, 0.14),
      new THREE.MeshBasicMaterial({
        color: i % 2 === 0 ? 0xa3e635 : 0x00ffa3,
        transparent: true,
        opacity: 0.9,
      })
    );
    plot.position.set(Math.cos(angle) * 2.15, -1.35 + h / 2, Math.sin(angle) * 2.15);
    plot.userData.baseH = h;
    plot.userData.phase = i * 0.7;
    cropPlots.push(plot);
    scene.add(plot);
  }

  const seedGeo = new THREE.BufferGeometry();
  const seedCount = 120;
  const positions = new Float32Array(seedCount * 3);
  for (let i = 0; i < seedCount; i++) {
    const r = 2.5 + Math.random() * 1.5;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * Math.PI;
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.cos(phi) * 0.6;
    positions[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
  }
  seedGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const seeds = new THREE.Points(
    seedGeo,
    new THREE.PointsMaterial({ color: 0x6ee7b7, size: 0.04, transparent: true, opacity: 0.6 })
  );
  scene.add(seeds);

  let mouseX = 0;
  let mouseY = 0;
  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 0.4;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 0.25;
  });

  function resize() {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (w === 0 || h === 0) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let t = 0;

  function animate() {
    requestAnimationFrame(animate);
    if (!reducedMotion) {
      t += 0.012;
      globe.rotation.y += 0.004;
      globe.rotation.x = Math.sin(t * 0.5) * 0.08;
      ring.rotation.z += 0.006;
      ring2.rotation.z -= 0.003;
      seeds.rotation.y += 0.002;
      cropPlots.forEach((plot) => {
        const s = 1 + Math.sin(t * 2 + plot.userData.phase) * 0.12;
        plot.scale.y = s;
      });
    }
    camera.position.x += (mouseX - camera.position.x) * 0.04;
    camera.position.y += (0.3 + mouseY - camera.position.y) * 0.04;
    camera.lookAt(0, -0.2, 0);
    renderer.render(scene, camera);
  }

  resize();
  window.addEventListener('resize', resize);
  animate();
})();

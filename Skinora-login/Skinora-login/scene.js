/* ═══════════════════════════════════════════════════════════════════
   SKINORA — scene.js
   Three.js r128 — complete 3D background environment
   Palette used:
     #727C6C  Bay Leaf Moss    → fog + clear color
     #979E8D  Laurel Veil      → grid lines
     #F6EFEA  Porcelain Cream  → light ray colour A
     #EFE0C9  Champagne Glow   → light ray colour B
     #E5BDBA  Antique Rose Dust→ caustic colour C
     #F1D4CE  Blushed Rose     → caustic colour D
     #EFE6D8  Parchment Ivory  → dust particles
════════════════════════════════════════════════════════════════════ */
 
(function () {
  'use strict';
 
  /* ── Renderer ──────────────────────────────────────────────────── */
  const canvas   = document.getElementById('bg-canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x727C6C, 1.0); /* Bay Leaf Moss */
 
  /* ── Scene & Fog ───────────────────────────────────────────────── */
  const scene = new THREE.Scene();
  scene.fog   = new THREE.FogExp2(0x727C6C, 0.055); /* Bay Leaf Moss */
 
  /* ── Camera ────────────────────────────────────────────────────── */
  const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200);
  camera.position.set(0, 6, 14);
  camera.lookAt(0, 0, 0);
 
  /* ── Mouse state ───────────────────────────────────────────────── */
  const mouse  = { x: 0, y: 0 };
  const smooth = { x: 0, y: 0 };
 
  document.addEventListener('mousemove', (e) => {
    mouse.x = (e.clientX / window.innerWidth)  * 2.0 - 1.0;
    mouse.y = (e.clientY / window.innerHeight) * 2.0 - 1.0;
  });
 
 
  /* ══════════════════════════════════════════════════════════════════
     1 · PERSPECTIVE WIREFRAME GRID
        Floor-plane LineSegments coloured Laurel Veil #979E8D
  ═══════════════════════════════════════════════════════════════════ */
  (function buildGrid () {
    const gridSize  = 40;
    const divisions = 28;
    const step      = gridSize / divisions;
    const half      = gridSize / 2;
    const positions = [];
 
    for (let i = 0; i <= divisions; i++) {
      const t = -half + i * step;
      /* Lines along Z */
      positions.push(t, 0, -half,   t, 0,  half);
      /* Lines along X */
      positions.push(-half, 0, t,   half, 0, t);
    }
 
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
 
    const mat = new THREE.LineBasicMaterial({
      color:       0x979E8D, /* Laurel Veil */
      transparent: true,
      opacity:     0.38,
    });
 
    const grid = new THREE.LineSegments(geo, mat);
    grid.position.y = -2.5;
    scene.add(grid);
  })();
 
 
  /* ══════════════════════════════════════════════════════════════════
     2 · VOLUMETRIC LIGHT RAYS
        ConeGeometry + custom ShaderMaterial, additive blending.
        Colours: Porcelain Cream #F6EFEA  and  Champagne Glow #EFE0C9
  ═══════════════════════════════════════════════════════════════════ */
 
  const lightRayVertexShader = /* glsl */`
    varying vec2  vUv;
    varying float vY;
 
    void main() {
      vUv         = uv;
      vY          = position.y;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `;
 
  const lightRayFragmentShader = /* glsl */`
    uniform float u_time;
    uniform vec3  u_colorA;   /* Porcelain Cream  #F6EFEA  vec3(0.9647, 0.9373, 0.9176) */
    uniform vec3  u_colorB;   /* Champagne Glow   #EFE0C9  vec3(0.9373, 0.8784, 0.7882) */
 
    varying vec2  vUv;
    varying float vY;
 
    void main() {
      /* Radial fall-off: bright at axis, zero at rim */
      float radial  = 1.0 - smoothstep(0.0, 0.5, vUv.x);
      radial        = pow(radial, 2.2);
 
      /* Axial fall-off: fade to zero at tip */
      float axial   = smoothstep(0.0, 0.35, vUv.y) * (1.0 - smoothstep(0.6, 1.0, vUv.y));
 
      /* Slow shimmer along axis */
      float shimmer = 0.82 + 0.18 * sin(u_time * 1.1 + vUv.y * 6.28318);
 
      float alpha   = radial * axial * shimmer * 0.72;
 
      /* Mix the two warm cream tones by height */
      vec3 col      = mix(u_colorA, u_colorB, vUv.y * 0.7 + 0.15);
 
      gl_FragColor  = vec4(col * alpha, alpha);
    }
  `;
 
  /* [x, z, rotX_offset, rotZ_offset, scale] */
  const rayDefs = [
    { x: -4.5, z: -3.0, rx:  0.08, rz:  0.12, s: 1.10 },
    { x:  0.0, z: -2.0, rx:  0.00, rz:  0.00, s: 1.30 },
    { x:  4.2, z: -3.5, rx: -0.06, rz: -0.10, s: 0.95 },
    { x: -2.0, z:  1.5, rx:  0.05, rz:  0.08, s: 0.75 },
    { x:  2.8, z:  1.0, rx: -0.04, rz: -0.06, s: 0.85 },
  ];
 
  const coneGeo = new THREE.ConeGeometry(1.8, 12.0, 32, 1, true);
 
  const lightRayMeshes   = [];
  const lightRayUniforms = [];
 
  rayDefs.forEach(function (def) {
    const uniforms = {
      u_time:   { value: 0.0 },
      u_colorA: { value: new THREE.Vector3(0.9647, 0.9373, 0.9176) }, /* #F6EFEA */
      u_colorB: { value: new THREE.Vector3(0.9373, 0.8784, 0.7882) }, /* #EFE0C9 */
    };
    lightRayUniforms.push(uniforms);
 
    const mat = new THREE.ShaderMaterial({
      vertexShader:   lightRayVertexShader,
      fragmentShader: lightRayFragmentShader,
      uniforms:       uniforms,
      transparent:    true,
      depthWrite:     false,
      blending:       THREE.AdditiveBlending,
      side:           THREE.DoubleSide,
    });
 
    const mesh = new THREE.Mesh(coneGeo, mat);
    mesh.position.set(def.x, 7.5, def.z);
    /* Flip cone so apex points up, opening faces downward */
    mesh.rotation.set(Math.PI + def.rx, 0, def.rz);
    mesh.scale.setScalar(def.s);
    scene.add(mesh);
    lightRayMeshes.push({ mesh, def });
  });
 
 
  /* ══════════════════════════════════════════════════════════════════
     3 · FLUID LIGHT CAUSTICS
        Full-floor PlaneGeometry + custom fragment shader.
        Classic 2-D Perlin noise + FBM, driven by u_time.
        Tints: Antique Rose Dust #E5BDBA  and  Blushed Rose #F1D4CE
  ═══════════════════════════════════════════════════════════════════ */
 
  const causticVertexShader = /* glsl */`
    varying vec2 vUv;
    varying vec3 vWorldPos;
 
    void main() {
      vUv           = uv;
      vec4 wp       = modelMatrix * vec4(position, 1.0);
      vWorldPos     = wp.xyz;
      gl_Position   = projectionMatrix * viewMatrix * wp;
    }
  `;
 
  const causticFragmentShader = /* glsl */`
    precision highp float;
 
    uniform float u_time;
    uniform vec3  u_colorC;   /* Antique Rose Dust  #E5BDBA  vec3(0.8980, 0.7412, 0.7294) */
    uniform vec3  u_colorD;   /* Blushed Rose       #F1D4CE  vec3(0.9451, 0.8314, 0.8078) */
 
    varying vec2 vUv;
    varying vec3 vWorldPos;
 
    /* ─── Perlin noise helpers ─── */
    vec4 permute(vec4 x) {
      return mod(((x * 34.0) + 1.0) * x, 289.0);
    }
 
    vec4 taylorInvSqrt(vec4 r) {
      return 1.7928429 - 0.8537347 * r;
    }
 
    vec2 fade(vec2 t) {
      return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
    }
 
    /* Classic 2-D Perlin noise */
    float cnoise(vec2 P) {
      vec4 Pi = floor(P.xyxy) + vec4(0.0, 0.0, 1.0, 1.0);
      vec4 Pf = fract(P.xyxy) - vec4(0.0, 0.0, 1.0, 1.0);
      Pi      = mod(Pi, 289.0);
      vec4 ix = Pi.xzxz;
      vec4 iy = Pi.yyww;
      vec4 fx = Pf.xzxz;
      vec4 fy = Pf.yyww;
      vec4 i  = permute(permute(ix) + iy);
      vec4 gx = 2.0 * fract(i * 0.024390243) - 1.0;
      vec4 gy = abs(gx) - 0.5;
      vec4 tx = floor(gx + 0.5);
      gx      = gx - tx;
      vec2 g00 = vec2(gx.x, gy.x);
      vec2 g10 = vec2(gx.y, gy.y);
      vec2 g01 = vec2(gx.z, gy.z);
      vec2 g11 = vec2(gx.w, gy.w);
      vec4 norm = taylorInvSqrt(vec4(
        dot(g00, g00), dot(g01, g01),
        dot(g10, g10), dot(g11, g11)
      ));
      g00 *= norm.x;  g01 *= norm.y;
      g10 *= norm.z;  g11 *= norm.w;
      float n00 = dot(g00, vec2(fx.x, fy.x));
      float n10 = dot(g10, vec2(fx.y, fy.y));
      float n01 = dot(g01, vec2(fx.z, fy.z));
      float n11 = dot(g11, vec2(fx.w, fy.w));
      vec2  fade_xy = fade(Pf.xy);
      vec2  n_x     = mix(vec2(n00, n01), vec2(n10, n11), fade_xy.x);
      return 2.3 * mix(n_x.x, n_x.y, fade_xy.y);
    }
 
    /* Fractal Brownian Motion — 5 octaves */
    float fbm(vec2 p) {
      float v  = 0.0;
      float a  = 0.50;
      vec2  sh = vec2(1.7, 9.2);
      for (int i = 0; i < 5; i++) {
        v += a * cnoise(p);
        p  = p * 2.1 + sh;
        a *= 0.50;
      }
      return v;
    }
 
    void main() {
      vec2  q  = vWorldPos.xz * 0.18;
      float t  = u_time * 0.22;
 
      /* Domain-warped FBM for rich organic flow */
      float n1    = fbm(q + vec2( t * 0.6,  t * 0.4));
      float n2    = fbm(q + vec2(-t * 0.3,  t * 0.7) + vec2(n1 * 1.4, n1 * 0.8));
 
      /* Caustic ridges — thin bright bands */
      float ridge = abs(sin(n2 * 5.5 + t * 0.9));
      ridge       = pow(1.0 - ridge, 5.5);
 
      /* Second finer caustic layer */
      vec2  q2     = vWorldPos.xz * 0.36;
      float n3     = fbm(q2 + vec2(t * 0.4, -t * 0.55));
      float ridge2 = abs(sin(n3 * 7.0 + t * 1.3));
      ridge2       = pow(1.0 - ridge2, 7.0) * 0.55;
 
      float caustic = ridge + ridge2;
 
      /* Colour blend between the two rose tones */
      float blend = clamp(n1 * 0.5 + 0.5, 0.0, 1.0);
      vec3  col   = mix(u_colorC, u_colorD, blend);
 
      /* Radial fade from centre of floor plane */
      vec2  centered = vUv - 0.5;
      float falloff  = 1.0 - smoothstep(0.18, 0.55, length(centered));
 
      float alpha = caustic * falloff * 0.48;
 
      gl_FragColor = vec4(col, alpha);
    }
  `;
 
  const causticUniforms = {
    u_time:   { value: 0.0 },
    u_colorC: { value: new THREE.Vector3(0.8980, 0.7412, 0.7294) }, /* #E5BDBA */
    u_colorD: { value: new THREE.Vector3(0.9451, 0.8314, 0.8078) }, /* #F1D4CE */
  };
 
  const floorGeo = new THREE.PlaneGeometry(44, 44, 1, 1);
  const floorMat = new THREE.ShaderMaterial({
    vertexShader:   causticVertexShader,
    fragmentShader: causticFragmentShader,
    uniforms:       causticUniforms,
    transparent:    true,
    depthWrite:     false,
    blending:       THREE.AdditiveBlending,
    side:           THREE.DoubleSide,
  });
 
  const floorMesh = new THREE.Mesh(floorGeo, floorMat);
  floorMesh.rotation.x = -Math.PI / 2;
  floorMesh.position.y = -2.48;
  scene.add(floorMesh);
 
 
  /* ══════════════════════════════════════════════════════════════════
     4 · AMBIENT PARTICLE DUST
        Small floating specks — Parchment Ivory #EFE6D8
  ═══════════════════════════════════════════════════════════════════ */
  (function buildDust () {
    const count     = 280;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3 + 0] = (Math.random() - 0.5) * 30;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 12 + 2;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 26;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color:       0xEFE6D8, /* Parchment Ivory */
      size:        0.045,
      transparent: true,
      opacity:     0.55,
      depthWrite:  false,
      blending:    THREE.AdditiveBlending,
    });
    scene.add(new THREE.Points(geo, mat));
  })();
 
 
  /* ══════════════════════════════════════════════════════════════════
     5 · ANIMATION LOOP
  ═══════════════════════════════════════════════════════════════════ */
  const clock          = new THREE.Clock();
  const baseCameraPos  = new THREE.Vector3(0, 6, 14);
 
  function animate () {
    requestAnimationFrame(animate);
    const elapsed = clock.getElapsedTime();
 
    /* Smooth mouse tracking */
    smooth.x += (mouse.x - smooth.x) * 0.045;
    smooth.y += (mouse.y - smooth.y) * 0.045;
 
    /* Camera parallax drift */
    camera.position.x = baseCameraPos.x + smooth.x * 2.8;
    camera.position.y = baseCameraPos.y - smooth.y * 1.4;
    camera.lookAt(0, 0, 0);
 
    /* Update shader uniforms */
    causticUniforms.u_time.value = elapsed;
 
    lightRayUniforms.forEach(function (u) {
      u.u_time.value = elapsed;
    });
 
    /* Sway light cones with mouse + sin wave */
    lightRayMeshes.forEach(function (item, idx) {
      const wave  = Math.sin(elapsed * 0.55 + idx * 1.2) * 0.025;
      const swayX = smooth.x * 0.18 + wave;
      const swayZ = smooth.y * 0.12;
      item.mesh.rotation.x = Math.PI + item.def.rx + swayZ;
      item.mesh.rotation.z = item.def.rz + swayX;
    });
 
    renderer.render(scene, camera);
  }
 
  animate();
 
 
  /* ══════════════════════════════════════════════════════════════════
     6 · RESIZE HANDLER
  ═══════════════════════════════════════════════════════════════════ */
  window.addEventListener('resize', function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
 
})();
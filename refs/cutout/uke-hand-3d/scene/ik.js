// IK for the fretting hand. Loaded by run.cjs scripts via `await (await fetch('/h3d/ik.js')).text()` eval.
// Exposes: IK.solveRest(opts) -> pose; IK.solvePress(pose, finger, string, opts) -> pose; IK.report(pose)
(function () {
  const G = geo, FING = ['index', 'middle', 'ring', 'pinky'];
  const D2R = Math.PI / 180;
  // fingertip targets: x = picture px (65 % into the fret space), on string s; `hover` metres above the string top
  const fretX = i => P.frets[i - 1], spaceX = (i, f) => { const a = i === 1 ? P.nut : P.frets[i - 2], b = P.frets[i - 1]; return a + (b - a) * f; };
  const R = {prox: .0082, mid: .0072, dist: .0064};          // finger radii (m) at hs 1
  function zSurf(y) {           // top of the neck's cross-section (board face) and bottom (back), in the board's |y| range
    if (Math.abs(y) > G.halfW) return null;
    const e = Math.sqrt(Math.max(0, 1 - (y / G.halfW) ** 2));
    return {top: 0, bot: -G.boardT - G.neckD * e};
  }
  function clear(p, r) {        // penetration depth of a sphere (p, r) into the neck (approx: vertical + edge distance)
    const s = zSurf(p[1]);
    if (s) { if (p[2] > (s.top + s.bot) / 2) return Math.max(0, r - (p[2] - s.top)); return Math.max(0, r - (s.bot - p[2])); }
    // outside the board's width: distance to the edge corner region (the A or G edge, a vertical side of the board)
    const ey = Math.sign(p[1]) * G.halfW, dy = Math.abs(p[1]) - G.halfW;
    if (p[2] <= 0 && p[2] >= -G.boardT - 2e-3) return Math.max(0, r - dy);
    if (p[2] > 0) return Math.max(0, r - Math.hypot(dy, p[2]));
    return 0;
  }
  const lerp = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
  function vars2pose(v, base) {
    const p = JSON.parse(JSON.stringify(base));
    let i = 0;
    if (base._freeWrist) { p.wrist.p = [v[i++], v[i++], v[i++]]; p.wrist.r = [v[i++], v[i++], v[i++]]; if (!base._noThumb) p.thumb = [v[i++], v[i++], v[i++], v[i++]]; }
    for (const f of base._free) p[f] = [v[i++], v[i++], v[i++], v[i++]];
    return p;
  }
  function pose2vars(p) {
    const v = [];
    if (p._freeWrist) { v.push(...p.wrist.p, ...p.wrist.r); if (!p._noThumb) v.push(...p.thumb); }
    for (const f of p._free) v.push(...p[f]);
    return v;
  }
  function energy(p, T) {
    setPose(p); const J = joints(); let E = 0; const hs = P.hs, terms = {};
    const add = (k, e) => { terms[k] = (terms[k] || 0) + e; E += e; };
    for (const f of FING) {
      const j = J[f];   // [metacarpal, prox(MCP), inter(PIP), distal(DIP), tip]
      const a = p[f];
      // joint priors (rad): MCP flex 0..1.4, abd ±.3, PIP .2..1.8, DIP .1..1.3 ; DIP ~ .55 PIP
      const lim = (x, lo, hi) => (x < lo ? (lo - x) ** 2 : x > hi ? (x - hi) ** 2 : 0);
      add('lim', 40 * (lim(a[0], -.1, 1.45) + lim(a[1], -.14, .14) + lim(a[2], .15, 1.85) + lim(a[3], 0, 1.25)));
      add('dipc', 1.5 * (a[3] - .62 * a[2]) ** 2);
      add('abd', 3 * a[1] ** 2);
      if (T.curl) add('curl', T.curl * ((a[0] - .6) ** 2 + (a[2] - 1.4) ** 2 + 2 * Math.max(0, a[3] - .75) ** 2));
      const t = (T.tips || {})[f];
      if (t) { const d = [j[4][0] - t.p[0], j[4][1] - t.p[1], j[4][2] - t.p[2]]; add('tip', t.w * 1e6 * ((t.xw === undefined ? 1 : t.xw) * d[0] ** 2 + d[1] ** 2 + (t.zw || 1) * d[2] ** 2)); }
      if (t && t.down) {   // distal segment pointing down into the board
        const dd = [j[4][0] - j[3][0], j[4][1] - j[3][1], j[4][2] - j[3][2]], n = Math.hypot(...dd);
        add('down', t.down * Math.max(0, .9 - (-dd[2] / n)) ** 2);
      }
      // collisions: samples along the segments
      const press = t && t.press;
      const segs = [[1, 2, R.prox], [2, 3, R.mid], [3, 4, R.dist]];
      for (const [s0, s1, r] of segs) for (const u of [0, .33, .66, 1]) {
        if (press && s0 === 3 && u > .3) continue;     // the pressing pad may touch
        const q = lerp(j[s0], j[s1], u); const pen = clear(q, r * hs + .0008);
        if (pen > 0) add('col', 4e6 * pen * pen);
        if (press === undefined && s0 === 3 && u === 1 && t) {}  // hovering tip: target handles height
      }
      // fingers must not pass through each other: keep tips apart
    }
    // neighbouring fingers: min distance between same-index samples of adjacent fingers
    for (let k = 0; k < 3; k++) { const A = J[FING[k]], Bj = J[FING[k + 1]];
      for (let s = 2; s <= 4; s++) { const d = Math.hypot(A[s][0] - Bj[s][0], A[s][1] - Bj[s][1], A[s][2] - Bj[s][2]); const m = 2 * R.mid * hs * .92;
        if (d < m) add('sep', 3e6 * (m - d) ** 2); } }
    if (T.thumb) { const th = J.thumb[3], d = [th[0] - T.thumb[0], th[1] - T.thumb[1], th[2] - T.thumb[2]]; add('thumb', 2e4 * (d[0] ** 2 + d[1] ** 2 + d[2] ** 2));
      for (const s of [1, 2, 3]) { const pen = clear(J.thumb[s], .009 * hs); if (pen > 0) add('col', 4e6 * pen * pen); } }
    if (T.mcp) for (const f of FING) { const m = J[f][1], c = T.mcp; const lim = (x, lo, hi) => (x < lo ? (lo - x) ** 2 : x > hi ? (x - hi) ** 2 : 0);
      add('mcp', 1e6 * (lim(m[1], c.y[0], c.y[1]) + lim(m[2], c.z[0], c.z[1])));
      if (c.dx !== undefined && T.tips[f]) add('mcpx', 2e5 * (m[0] - T.tips[f].p[0] - c.dx) ** 2); }
    if (T.wristP) add('wp', T.wristP.w * ((p.wrist.p[0] - T.wristP.p[0]) ** 2 + (p.wrist.p[1] - T.wristP.p[1]) ** 2 + (p.wrist.p[2] - T.wristP.p[2]) ** 2));
    if (T.wristReg) add('wr', T.wristReg * (p.wrist.r[0] ** 2 + p.wrist.r[1] ** 2 + p.wrist.r[2] ** 2));
    if (T.thumbLim && p.thumb) { const a = p.thumb; add('lim', 10 * ((Math.abs(a[1]) > .8 ? (Math.abs(a[1]) - .8) ** 2 : 0) + (a[2] < -.2 ? (a[2] + .2) ** 2 : 0) + (a[3] < -.2 ? (a[3] + .2) ** 2 : 0) + (a[0] < -.6 ? (a[0] + .6) ** 2 : 0) + (a[0] > 1 ? (a[0] - 1) ** 2 : 0))); }
    if (T.extra) add('extra', T.extra(p, J));
    return {E, terms};
  }
  function minimize(base, T, iters, lr) {
    let v = pose2vars(base); const n = v.length, m = new Array(n).fill(0), s = new Array(n).fill(0);
    const scale = v.map((_, i) => base._freeWrist && i < 3 ? .002 : base._freeWrist && i < 6 ? .01 : .02);   // wrist position steps in metres
    let best = {v: v.slice(), E: energy(vars2pose(v, base), T).E};
    for (let it = 1; it <= iters; it++) {
      const E0 = energy(vars2pose(v, base), T).E;
      if (E0 < best.E) best = {v: v.slice(), E: E0};
      const g = new Array(n);
      for (let i = 0; i < n; i++) { const h = scale[i] * .05; const w = v.slice(); w[i] += h; g[i] = (energy(vars2pose(w, base), T).E - E0) / h * scale[i]; }
      for (let i = 0; i < n; i++) { m[i] = .9 * m[i] + .1 * g[i]; s[i] = .999 * s[i] + .001 * g[i] * g[i];
        const mh = m[i] / (1 - .9 ** it), sh = s[i] / (1 - .999 ** it); v[i] -= lr * scale[i] * mh / (Math.sqrt(sh) + 1e-9); }
    }
    const E = energy(vars2pose(v, base), T); if (E.E > best.E) v = best.v;
    const out = vars2pose(v, base); return {pose: out, E: energy(out, T)};
  }
  window.IK = {energy, minimize, spaceX, zSurf, clear,
    tipTarget: (fret, str, frac, lift) => [G.X(spaceX(fret, frac)), G.yS[str], G.strZ + lift]};
})();
// ---- grid IK: per finger, search MCP flex x PIP flex (DIP coupled), then refine with abduction and DIP ----
(function () {
  const G = geo, R = {prox: .0082, mid: .0072, dist: .0064};
  function fingerCost(p, f, t, o) {
    setPose(p); const J = joints()[f], a = p[f], hs = P.hs;
    const d = [J[4][0] - t.p[0], J[4][1] - t.p[1], J[4][2] - t.p[2]];
    let c = 1e6 * ((t.xw ?? .3) * d[0] ** 2 + d[1] ** 2 + (t.zw ?? 1) * d[2] ** 2);
    c += (o.nat ?? 3) * ((a[0] - (o.mcp0 ?? .6)) ** 2 + (a[2] - (o.pip0 ?? 1.4)) ** 2) + 3 * a[1] ** 2 + 2 * (a[3] - .62 * a[2]) ** 2;
    const segs = [[1, 2, R.prox], [2, 3, R.mid], [3, 4, R.dist]];
    for (const [s0, s1, r] of segs) for (const u of [0, .33, .66, 1]) {
      if (t.press && s0 === 3 && u > .3) continue;
      const q = J[s0].map((v, i) => v + (J[s1][i] - v) * u); const pen = IK.clear(q, r * hs + .0008);
      if (pen > 0) c += 4e6 * pen * pen; }
    if (t.down) { const dd = [J[4][0] - J[3][0], J[4][1] - J[3][1], J[4][2] - J[3][2]], n = Math.hypot(...dd); c += t.down * Math.max(0, .85 - (-dd[2] / n)) ** 2; }
    if (o.avoid) for (const g of o.avoid) { const Jg = joints()[g]; for (let s = 2; s <= 4; s++) { const dist = Math.hypot(...[0, 1, 2].map(i => J[s][i] - Jg[s][i])); const m = 2 * R.mid * hs * .9; if (dist < m) c += 3e6 * (m - dist) ** 2; } }
    return c;
  }
  function solveFinger(p, f, t, o = {}) {
    p = JSON.parse(JSON.stringify(p)); let best = null;
    for (let m = -.3; m <= 1.55; m += .05) for (let q = .1; q <= 2.05; q += .05) {
      p[f] = [m, 0, q, .62 * q]; const c = fingerCost(p, f, t, o); if (!best || c < best.c) best = {c, a: p[f].slice()}; }
    // refine: coordinate descent on all four
    let a = best.a, c = best.c, step = [.04, .04, .04, .04];
    for (let it = 0; it < 60; it++) { let imp = false;
      for (let i = 0; i < 4; i++) for (const s of [1, -1]) { const b = a.slice(); b[i] += s * step[i]; b[1] = Math.max(-(o.abdMax ?? .12), Math.min(o.abdMax ?? .12, b[1])); b[3] = Math.max(0, Math.min(o.dipMax ?? 1.1, b[3])); p[f] = b; const cb = fingerCost(p, f, t, o); if (cb < c) { a = b; c = cb; imp = true; } }
      if (!imp) step = step.map(v => v / 2); if (step[0] < .002) break; }
    p[f] = a; return {pose: p, c, a};
  }
  IK.solveFinger = solveFinger; IK.fingerCost = fingerCost;
})();

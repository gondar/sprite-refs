/* Cut-out puppet player: draws a rig (pieces + pivots) in any pose on a 2D canvas. No dependencies.
   A rig: { bones: [{name, img, bbox:[x,y,w,h], pivot:[x,y], parent, at:[x,y], z, flip, scale, rot, hidden}] }
   All coordinates are SHEET pixels: `pivot` is the joint on this piece, `at` is where that joint sits on the
   parent piece. A pose: { boneName: {r (deg), x, y, sx, sy, a (alpha), show} } — everything optional. */
(function (G) {
  function prepare(rig, images) {
    const by = {};
    rig.bones.forEach(b => { by[b.name] = b; b.canvas = images[b.name]; });
    rig.by = by;
    rig.order = rig.bones.slice().sort((a, b) => (a.z || 0) - (b.z || 0));
    return rig;
  }
  function matFor(rig, name, pose, cache) {
    if (cache[name]) return cache[name];
    const b = rig.by[name], p = pose[name] || {};
    let m;
    if (b.parent) {
      const pb = rig.by[b.parent];
      m = matFor(rig, b.parent, pose, cache).translate(b.at[0] - pb.pivot[0], b.at[1] - pb.pivot[1]);
    } else m = new DOMMatrix();
    m = m.translate(p.x || 0, p.y || 0).rotate(((b.rot || 0) + (p.r || 0)))
      .scale((p.sx ?? 1) * (b.scale || 1), (p.sy ?? 1) * (b.scale || 1));
    return (cache[name] = m);
  }
  function draw(ctx, rig, pose, x, y, k, opts) {
    opts = opts || {};
    const cache = {};
    ctx.save(); ctx.translate(x, y); ctx.scale(k * (opts.face || 1), k);
    const base = ctx.getTransform();
    for (const b of rig.order) {
      const p = pose[b.name] || {};
      const show = p.show ?? !b.hidden;
      if (!show || (p.a ?? 1) <= 0) continue;
      const m = matFor(rig, b.name, pose, cache);
      ctx.setTransform(base.multiply(m));
      ctx.globalAlpha = p.a ?? 1;
      const dx = b.bbox[0] - b.pivot[0], dy = b.bbox[1] - b.pivot[1];
      if (b.flip) { ctx.scale(-1, 1); ctx.drawImage(b.canvas, dx, dy, b.bbox[2], b.bbox[3]); }
      else ctx.drawImage(b.canvas, dx, dy, b.bbox[2], b.bbox[3]);
      if (opts.pivots) { ctx.fillStyle = "#e33"; ctx.beginPath(); ctx.arc(0, 0, 6 / k, 0, 7); ctx.fill(); }
    }
    ctx.restore(); ctx.globalAlpha = 1;
  }
  // tiny helpers for writing animations
  const S = Math.sin, TAU = Math.PI * 2;
  const wave = (t, hz, amp, ph) => amp * S(TAU * (hz * t + (ph || 0)));
  const ease = u => u < 0 ? 0 : u > 1 ? 1 : u * u * (3 - 2 * u);
  // a lagging follower: damped pendulum response to a driver, closed form good enough for loops
  const lag = (t, hz, amp, delay) => amp * S(TAU * hz * (t - delay));
  G.Cutout = { prepare, draw, wave, ease, lag, TAU };
})(window);

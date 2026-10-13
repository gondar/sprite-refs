window.__build = (app, K) => {
  const { H, X } = K;
  const P = html => H("p", { innerHTML: html });
  const sec = (title, ...kids) => H("section", {}, H("h2", { textContent: title }), ...kids);
  const byName = n => RIGS.find(r => r.name === n);

  app.append(
    H("h1", { textContent: "Cutout animation — experiment C1" }),
    P('<span class="mute">2026-10-13 · Sówka (owl) and Leoś (fox) · Nano Banana / Nano Banana Pro through APIYI · spent $0.23 (4 sheets) · total so far ≈ $3.67 of $10</span>'),
    P("<b>Verdict: it works, and it is the cheapest route to many actions.</b> One parts sheet ($0.0245) gives a puppet that plays every animation below, plus any you write later, for free, at any size, with no keying or loop seams per action. All the motion here is code: the art is 43–48 KB per character for <i>all</i> actions, against 117 KB for the fox's single 24-frame video idle in the game. The cost is a different kind of work: someone (an agent) has to set ~2 numbers per piece (pivot + where it attaches) and write the motion. Motion is stiffer than video: limbs are rigid, the body never turns, no cloth or fur moves unless you animate it. Best fit: round, simple characters (the owl is excellent); weaker fit: long-limbed walkers seen from 3/4."),
  );

  const g1 = H("div", { className: "grid" });
  ["owl-pro", "owl-flash", "fox-grid"].forEach(n => g1.append(K.rigCard(byName(n), byName(n)._imgs)));
  app.append(sec("Option A — rigid cutout puppets (pieces from one generated sheet)",
    P("Click the actions. <b>pivots</b> shows the joints; <b>game size</b> draws it as small as in the game. Blinks, the happy face, the open beak and the fox's open mouth are spare pieces swapped in on top of the face."), g1));

  const g2 = H("div", { className: "grid" });
  g2.append(K.meshCard("Owl — one image, mesh warp", "the existing reference image only · $0 extra · 0 pieces", X.owlWhole,
    "Breathing, sway, squash and a hop by bending a 14×14 grid laid over the whole picture. Nothing to cut, nothing to rig. Good for idles and reactions; it cannot move a wing or a leg on its own, and a strong bend smears the detail."));
  g2.append(K.meshCard("Fox — one image, mesh warp", "the existing reference image only · $0 extra · 0 pieces", X.foxWhole,
    "Same trick on the fox: the tail and the hat move with the body, so it reads as the whole picture wobbling. Fine as a stand-in conductor idle, not for walking."));
  app.append(sec("Option B — no pieces at all: warp the single picture", P("The cheapest trick in the set, shown for comparison: it uses the character reference we already have."), g2));

  const g3 = H("div", { className: "grid" });
  g3.append(K.stripCard("Fox — H3 video idle (shipped in the game)", "24 frames · 117 KB · $0.12 clip", X.foxVideo, 24, 5.7,
    "The baseline: real fur and body motion, the head turns in 3D. One action per strip, and each action is a paid clip plus keying and loop work."));
  g3.append(K.stripCard("Owl — H3 video idle", "24 frames · 119 KB webp · $0.12 clip", X.owlVideo, 24, 5.7,
    "Softer and more alive than any puppet above, but it is only this one action."));
  app.append(sec("Baseline — the video route from the earlier experiments", g3));

  app.append(sec("The sheets",
    P("Same prompt for each character, one reference image (the character design). <b>Exploded view</b> = the character taken apart with gaps, every piece near its natural place; <b>grid</b> = asset-sheet layout with a named list."),
    H("div", { className: "sheets" },
      ...[["owlProSheet", "Owl · exploded · Pro $0.09 — drew joint tabs by itself"], ["owlFlashSheet", "Owl · exploded · Nano Banana $0.0245"],
        ["foxGridSheet", "Fox · grid · Nano Banana $0.0245 — used"], ["foxProSheet", "Fox · exploded · Pro $0.09 — not rigged: arms bent, head with open mouth, no anatomical layout"]]
        .map(([k, c]) => H("figure", {}, H("img", { className: "sheet", src: EXTRA[k], alt: c }), H("figcaption", { textContent: c })))),
    P('<span class="mute">A fifth job (fox exploded on Nano Banana) failed with HTTP 502 at 30 s and was logged at $0; not retried.</span>')));

  app.append(sec("What I learned",
    H("div", { className: "wide" }, H("table", { innerHTML: `
<tr><th>Question</th><th>Answer</th></tr>
<tr><td>Can Nano Banana draw a character as separate pieces?</td><td>Yes, first try, on both models, in the character's own style and colours. The prompt line that matters: <i>"extend each piece with a plain rounded tab past the joint, so pieces can rotate without showing a hole"</i> — both models drew the hidden overlap.</td></tr>
<tr><td>Exploded view or grid?</td><td>Exploded view for round characters (scale and placement come for free; the rest pose is nearly the layout itself). Grid for the fox also held scale. Pro ignored the exploded layout for the fox.</td></tr>
<tr><td>Flash or Pro?</td><td>Flash is enough. Pro's owl is a little cleaner and added joint tabs on its own; not worth 3.7× for this.</td></tr>
<tr><td>Body plan</td><td>Owl (head, body, 2 wings, 2 feet, hat, pompom): excellent — most of its life is head tilt, wing flap, squash, blink. Fox (biped): walk reads well at game size; up close, legs are rigid blobs with no knees and the body cannot turn.</td></tr>
<tr><td>Face swaps</td><td>Owl spares came as clean face pieces (drop-in). Fox spares came as square patches of fur — feathered into ovals they work at game size. Ask for "a whole head with eyes closed" instead of a patch.</td></tr>
<tr><td>Draw order</td><td>Fixed per piece. The fox's near arm cannot wave without covering his face, so the wave uses the far arm, raised forward. A rig for a skill needs per-action layer order (or both arms drawn twice).</td></tr>
<tr><td>Work per character</td><td>Cutting is automatic (<code>pieces.py</code>). Rigging was by eye: ~2 points per piece, 2–3 tuning passes per character. That is the step to automate in a skill.</td></tr>
<tr><td>Size</td><td>All actions: 43–48 KB of pieces at half resolution. Video idle alone: 117 KB.</td></tr>`
    }))));

  app.append(sec("Other animation tricks worth considering",
    H("div", { className: "wide" }, H("table", { innerHTML: `
<tr><th>Trick</th><th>What it is</th><th>Cost</th><th>Good for</th></tr>
<tr><td><b>Mesh warp of one image</b> (shown above)</td><td>Bend a grid over the finished picture</td><td>$0</td><td>Idles, reactions, "alive" props and mascots — the default for anything that only needs to breathe</td></tr>
<tr><td><b>Rig → H3 mannequin</b></td><td>Render the puppet's motion to a short clip and feed it to H3 as the reference video, with the character image. The cutout sets exact timing and poses; H3 adds the life (fur, squash, turning)</td><td>$0.12 / clip</td><td>Fixing "run reads as walk" and timing drift in the video route; each character gets a mannequin of its own shape</td></tr>
<tr><td><b>Swap overlays on video</b></td><td>Keep the video sprite, add blink / mouth pieces on top from a parts sheet</td><td>$0.0245</td><td>Singing or talking characters without a clip per mouth shape</td></tr>
<tr><td><b>Frame interpolation</b></td><td>Generate 4–8 keyframes in one image, fill the in-betweens with an interpolation model (RIFE / FILM)</td><td>image + local compute</td><td>Smoothing drawn cycles (the 8-frame image route) — not tested here, needs a model we do not have in this sandbox</td></tr>
<tr><td><b>Procedural secondary motion</b></td><td>Springs on tails, ears, hats, pompoms driven by the body's motion (the pompom here lags the head)</td><td>$0</td><td>Adding life to any route, including video sprites with a separate tail piece</td></tr>
<tr><td><b>Bake to strips</b></td><td>Render the puppet to frames once</td><td>$0</td><td>Engines with no puppet runtime, pixel-art downscaling, or mixing with video strips</td></tr>`
    }))),
    P("<b>Recommendation.</b> If you want the skill: build it around the owl result — exploded-view parts sheet on Nano Banana → <code>pieces.py</code> → rig JSON with pivots → a small player (<code>cutout.js</code>, 2 KB) with procedural actions. The step to make reliable is rigging: ask the model for joint tabs in a marker colour (Pro drew them unasked) and detect them, so pivots come out automatically. Worth one more cheap round ($0.05–0.10) to test that before writing the skill."));
};

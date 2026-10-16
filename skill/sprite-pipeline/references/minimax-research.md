# MiniMax-H3 and the Mountain King: why the clips came out badly and what to try next

Research only, 2026-10-16. No paid calls were made. Sources: the saved H3 doc, `findings.md`, `SKILL.md`, `jobs/jobs.jsonl`, the prompts, and measurements of the raw clips (scratch scripts, not committed). The web was only partly reachable. `docs.apiyi.com` and `api.apiyi.com/api/pricing` loaded. platform.minimax.io, fal.ai, tessl.io, segmind.com and runwayml.com did not resolve in the sandbox (`ENOTFOUND` / HTTP 000), so everything from community guides below comes from search-result summaries. Treat it as secondary.

## 0. What the clips show (measured)

768×768, 24 fps, 107 frames per clip. The measurement scripts compared each frame with frame 0 and with the reference `king-ref-headroom-v2.png`.

| Clip | Mode | Frame 0 vs reference (MAE) | Background over time (RGB of the corner) |
|---|---|---|---|
| poses4-a `20261016-141519` | reference image only | 9.0 (figure brightness 86 → 79) | magenta until 0.5 s, then (198,14,201) at 0.75 s, (75,50,102) at 1.25 s, dark teal (33,60,80) at 2.5 s plus a grassy floor, back toward purple at 4 s |
| poses4-a-v3 `20261016-144255` | reference image only | 8.7 | magenta until 0.25 s, then sky blue (84,156,210) from 1.0 s to 3.5 s, then lavender |
| poses4-b `20261016-141524` | reference image only | — | magenta, then pale green (≈130,205,110) from 1.25 to 3 s, back to magenta at 4.4 s |
| seated v2 `20261015-215628` | reference image + mannequin video | 10.6 (figure brightness 86 → 74) | magenta until 0.5 s, then teal (90,146,164) from 1.75 to 2.75 s, then lavender |
| fox E2a `20261012-195024` | first + last frame | **5.0** | full hue rotation: magenta, red, orange, yellow, green, cyan, blue, about one step every 0.5 s |
| fox E2d `20261012-201304` | first + last frame | **4.6** | magenta, then cyan (0,235,246) from 0.5 s to the end |

Frame-by-frame look (`scratchpad/cmp.png`: reference / 0 s / 0.5 s / 2 s / 3.5 s of poses4-a):

- **Frame 0 of a reference-mode clip is not the picture.** It is a repaint: darker, with different moss patches and a different rim light. The high-pass (fine texture) difference between the reference and frame 0 is 2.3–2.4 grey levels over the static throne and legs.
- At **0.5 s the mouth is open, fangs showing**, during the "DEEP BREATH". The same happens in poses4-a-v3 at 0.25–0.75 s.
- At 2 s the background is dark teal with grass, and the stone has taken a cold blue rim light.
- The beard-stroke clip `20261016-135318` came back framed tighter from the first frame (feet cropped), then zoomed out at 3–4 s while turning purple.
- **"Boiling" measured** over the throne, legs and feet (the bottom 30 % of the figure):
  - Frame-to-frame change in fine texture is small: 0.03–0.6 grey levels per frame, with one 1.4 spike.
  - Measured against frame 0, the change builds to 1.5–3.0 in texture and 2.5–4.4 in colour, following the background drift.
  - So most of what looks like boiling is slow relighting plus repainting, not per-frame noise. On top of that comes a **visible jump wherever `gestures.py` crossfades into the shipped home frame**, because that home frame is not what the clip started from.

## 1. Ranked causes

### 1. Reference mode is a subject reference, not a frame to keep (biggest cause)
- The doc lists `first_frame` / `last_frame` and `reference_image` as separate roles. Reference mode is the "<Picture 1> dances with the moves from <Video 1>" mode: `"Text + reference_image / reference_video / reference_audio → reference video"`.
- Third-party H3 guides say the same: an image that is literally the first or last frame belongs in first/last-frame mode, while a reference keeps a face, product or character.
- Measured: frame 0 differs from the picture (MAE 8.7–10.6), but first-frame mode reproduces it (4.6–5.0, about the H.264 floor).
- Because no frame is pinned in reference mode, H3 may:
  - reframe the shot (2 of 5 single-gesture clips zoomed in);
  - relight the character;
  - never come back home. There is no end anchor, which is why the gesture ends did not land on the clock.
- This mode cannot "animate exactly this picture".

### 2. The flat saturated #FF00FF background is out of distribution, and the model "fixes" it
- Every Mountain King clip in both modes drifted. It started at 0.25–0.75 s, earlier than the "1.5–2 s" the log records.
- The drift ends on what a video model expects behind a character: a desaturated studio sweep (sky blue, teal, lavender, dark teal with a vignette and floor) or a light show (E2a's rainbow).
- The character is relit by the new background (cold rim, darker stone). That is the "colours of the king change too" complaint.
- Note `findings.md`: the owl on **green** held its background (B2), and every text-to-video mannequin on green came out clean.

### 3. The prompts work against the model
- They run 1,780–1,880 characters, and about 60 % is constraints. The **background paragraph names magenta and lists the colours it must not become** ("never turns purple or lavender, never gets brighter or darker"). The drift then went to exactly purple and lavender.
- Third-party H3 guides: in image-to-video the frame already fixes subject, light and palette, so the prompt should say what MOVES. Describing what is already visible pushes toward a static clip. Use negatives sparingly; long lists dilute the action. Prefer positive phrasing ("X remains …").
- "a DEEP BREATH" plus mandatory audio: the doc says H3 always makes a stereo track ("music and sound effects follow the prompt; there is no switch to turn it off"). A breath is a sound, and the model voiced it with an open mouth.
- "MOUTH CLOSED IN EVERY FRAME / never speaks, sings, growls, yawns" names four mouth-opening actions.
- `0.0–1.0 s` timing is followed loosely, as expected. Guides say Hailuo reads prompts as an ordered sequence ("first … then …"), not a clock.

### 4. Conflicting backgrounds between references (seated v1/v2)
The mannequin clip's background is green (40,176,15), and the King reference is magenta. With two references disagreeing, H3 blended them: v2 went to teal (90,146,164).

### 5. Throne and static parts are regenerated
- Reference mode repaints everything every frame, including the throne. Nothing in the API can freeze a region: the only parameters are `model, content, resolution, duration, ratio`, and undocumented fields are rejected.
- The fix has to happen in post (§5).

## 2. API facts relevant to the questions

- **H3 via APIYI**: `768P` only, duration 4–15, ratio including `adaptive`. That is the whole surface: **no `prompt_optimizer`, no seed, no negative prompt, no camera parameter.** The overview says undocumented fields such as `seed` are rejected. $0.03/s, so a 4 s clip costs $0.12.
- `first_frame` + `last_frame` cannot be mixed with `reference_*`. The two frames must be within 2 % in aspect ratio. A single image without a role is treated as the first frame.
- **Camera tags.** MiniMax's older Director / Hailuo-02 / 2.3 models take bracketed commands in the prompt, up to three: `[Static shot]`, `[Pan left]`, `[Push in]`, `[Zoom out]` and so on. An H3 guide says the official H3 examples use bracketed tags like `[static]`, but no full list is published. Use `[Static shot]` **plus** a plain sentence ("the camera stays locked off"). It costs nothing; it is not guaranteed.
- **`prompt_optimizer`** is a MiniMax-native flag on the older models (default `true`). APIYI's H3 route does not expose it, so it cannot be turned off here. Oxygen's equivalent, `prompt_enhance`, can be set to `none`.

## 3. Which mode

**First frame + last frame = the same home picture.** It is the only mode that:
- reproduces the picture (MAE about 5);
- pins the end pose, so the loop closes by construction;
- gives the framing two anchors, so reframing should mostly disappear.

The old rule "first+last repaints the background" was confounded:
- both tests (E2a, E2d) used **saturated magenta**;
- both named the colour in the prompt, and E2d shouted it ("never changes hue, brightness or saturation, never fades, never flashes");
- the fox test was also a whole-body idle with tail and ears.

It was never tested with a different background or a prompt that leaves the background alone. Reference mode has drifted on the King every time too, so its "background stays magenta" advantage did not carry over from the fox.

## 4. Which background

There are no published tests of background stability. Our own log is the only evidence:

- **Magenta**: 100 % drift on the King, in both modes.
- **Green**: held in the owl clip, and clean in 4+ text-to-video mannequins.
- **Drift destinations** were desaturated blue/teal sweeps. That is a hint that a blue backdrop is "natural" to the model.

The King has no blue at all (neutral grey stone, olive moss, amber), so **blue** keys best for this character. **Green** has the better track record but sits near the moss; the excess G − max(R,B) on the moss is about 20, below key lo=40, so it is workable. **Mid-grey is a bad idea for a grey stone troll**: no chroma contrast, and difference keying fails at the silhouette. **White** relights as a bright studio sweep and loses the pale crystal glow. A real cave scene is in-distribution and may be the most stable, but then cut-out depends on the known home alpha plus a difference against the scene plate. Keep it as the fallback if both chroma colours drift.

Proposal: test **blue (#2F6BD8, a medium chroma blue)** against **green (#22B24C, film-chroma green)**, both medium saturation (not neon) and both flat.

## 5. Boiling: model side and post side

- **Model side**:
  - first+last mode (frame 0 = the picture);
  - motion words only for the parts that move;
  - "everything else stays perfectly still";
  - 4 s (the minimum);
  - small, slow gestures.

  1080P is not available on this route (`768P` only).
- **Post side ("static lock")**, replacing the crossfade-to-shipped-home approach:
  1. Home frame = the prepared first-frame image itself (clean alpha from keying the still once, not from video).
  2. Register each frame to home. It should be near identity in first+last mode; keep the `--static` fit as a check.
  3. Paint, once on the home frame, a **rigid mask** (throne, legs, feet, the throne's arms where the hands do not touch) and **per-gesture allowed masks**:
     - head and face box: glance, look down, smile, tilt;
     - chest and shoulders: breath, sway;
     - right arm plus beard: stroke;
     - left hand: drum.
  4. Per frame, the motion mask is the allowed mask ∩ (|frame − home| after a brightness match > ~12), with 2-frame temporal hysteresis, dilated 6 px and feathered 8 px. Output = home everywhere outside the mask, the frame inside it.
  5. Inside the mask, colour-match with per-channel gains measured on a 10 px ring of body just outside the mask. That undoes any relight.
  6. Alpha: home alpha outside the mask. Inside the mask, key against the known flat background colour; only the silhouette edge of the sway or tilt needs it.

  Result: the throne and legs are pixel-identical in every frame, and only real motion survives.

## 6. Other models via APIYI (pricing from api.apiyi.com/api/pricing and the docs)

| Model | First+last frame | Price, 4–5 s | Notes |
|---|---|---|---|
| MiniMax-H3 | yes | $0.12 (4 s) | 768P only, audio always on, no optimizer, seed or negative prompt |
| oxygen-1.0 (AZ8) | yes, `input_reference` JSON `{"images":[first],"last_image":last}` | **$0.08 (4 s)** | 480p/768p same price; `prompt_enhance: "none"`; `quality: high`; pass `size` (768p 1:1 via envelope) |
| Seedance 2.0 mini / fast / std, 2.5 | yes | 480p 4 s ≈ $0.17 (mini); 720p 4 s ≈ $0.58 (fast); 720p 5 s $0.91 (std); 2.5 720p 5 s $1.37 | seed, `generate_audio`; no `camera_fixed` on 2.x; separate token group |
| Wan2.7-i2v | first frame only | 720P $0.084/s → 4 s $0.34 | `negative_prompt`, `prompt_extend:false`, seed, 1080P $0.14/s |
| Veo 3.1 Official (fast / std) | no (official channel) | $0.30 / $1.20 per request | 4/6/8 s; the reverse `-fl` channel is paused |
| Kling, Hailuo-02 | not listed on APIYI | — | Kling 3.0 "upcoming" |

Worth one cheap clip: **Oxygen** with first+last frame and `prompt_enhance: none`. Wan has a negative prompt and no last frame. Seedance is 1.5–5× the price.

## 7. Proposed experiment (cost ≈ $0.56, with re-tries ≤ $0.80)

**Reference prep**:
- Key `king-ref-headroom-v2.png` once (magenta, with despill or un-mixing of the edge; there must be no pink fringe left to animate).
- Composite on flat **#2F6BD8** (`king-home-blue-768.png`) and flat **#22B24C** (`king-home-green-768.png`).
- Scale to exactly **768×768**, with the King about 64 % of the height:
  - about 14 % headroom above the crown;
  - at least 10 % margin each side for the sway and tilt;
  - about 8 % below the feet.
- PNG, a new filename, unversioned jsDelivr URL.
- The same file is both `first_frame` and `last_frame`, so the 2 % ratio rule is met.

**Request body (H3)**:
```json
{"model":"MiniMax-H3","resolution":"768P","duration":4,"ratio":"adaptive",
 "content":[
  {"type":"text","text":"<PROMPT A or B>"},
  {"type":"image_url","image_url":{"url":"https://cdn.jsdelivr.net/gh/gondar/sprite-refs/refs/mountain-king/king-home-blue-768.png"},"role":"first_frame"},
  {"type":"image_url","image_url":{"url":"https://cdn.jsdelivr.net/gh/gondar/sprite-refs/refs/mountain-king/king-home-blue-768.png"},"role":"last_frame"}]}
```

**Prompt A** (breath, glance, look down, smile), 132 words:
> [Static shot] A painted cartoon stone troll king sits on his rock throne, facing us. The camera stays locked off; the framing and lighting never change. He makes four small, slow, calm movements, resting in his starting pose between each one. First, a quiet breath through his nose: his chest and shoulders lift slightly and settle. Then his eyes and head glance briefly to his left and come back to the front. Then he lowers his gaze to the ground in front of his feet and raises it again. Last, his eyes narrow into a warm, contented smile with his lips pressed together, and his face relaxes. He ends exactly in his starting pose. His throne, legs, feet and the plain backdrop stay completely still. Sound: a soft, low cave ambience only.

**Prompt B** (beard stroke, finger drum, head tilt, sway), 140 words:
> [Static shot] A painted cartoon stone troll king sits on his rock throne, facing us. The camera stays locked off; the framing and lighting never change. He makes four small, slow, calm movements, resting in his starting pose between each one. First, he lifts his right hand from the throne's arm, strokes his mossy beard once, and puts the hand back where it was. Then the fingers of his left hand tap lightly on the throne's arm, then lie still. Then he tilts his head slightly to one side, curious, and straightens it. Last, his upper body sways gently to one side and back to centre. He ends exactly in his starting pose, lips pressed together throughout. His throne, legs, feet and the plain backdrop stay completely still. Sound: a soft, low cave ambience only.

The background colour is never named, there is no clock syntax, no "never" list, and nothing that makes a vocal sound.

**Runs**:
1. Prompt A, blue: $0.12.
2. Prompt A, green: $0.12.
3. Prompt B on the better background (or both colours if neither is clearly ahead: +$0.12).
4. Optional: Oxygen-1.0, Prompt A, the better background, 768p 1:1, `prompt_enhance:"none"`: $0.08.

Base about **$0.44–0.56**; one re-try per clip puts the ceiling at about **$0.80**.

**Judge on**:
- the background colour curve, measuring the corner RGB per frame;
- frame 0 and the last frame against the picture (MAE about 5 is expected);
- whether each gesture is visible at all. The risk of first+last at 4 s is too little motion;
- whether the mouth stays closed;
- the framing (the bottom of the throne must not move).

Then run the static-lock post (§5).

# Native GIF generation — the API as tested

## Round 2 findings (2026-11-06) — read first

- **The GIF is drawn as one sheet.** 8 frames at 1024×1024 → HTTP 400 in 3 s: "No supported sheet fits 8 GIF
  frames at size '1024x1024'. Invalid size '4096x2048'. The longest edge must be less than or equal to 3840."
  8 frames fit at 960×960 (4×2), 12 at 768×768 (4×3). Output tokens scale with the sheet: 512 px low 555,
  960 px low 1,260, medium 2,228, high 2,700; 12 × 768 medium 3,238.
- **`/v1/images/edits` returns GIFs** (contrary to the docs this skill started from): multipart, `image[]` = the
  reference, plus `output_format=gif`, `frame_count`, `frame_duration_ms`, `size`, `quality`, `background`.
  The reference costs image-input tokens (1536×1024 sheet → 1,536).
- **`background: "transparent"`** works: palette transparency on every frame (echoed in the response).
- **`complexity: "low"` degrades the result** (E10 vs E8, same request otherwise). Leave the field out.
- **Responses API image tool**: `Unknown parameter: 'tools[0].frame_count'` (400, 5.6 s). No GIF that way.
- **Sunburst, quality high, 960 px, with a reference**: HTTP 502 "upstream request failed" at 30.6 s on both
  `api.apiyi.com` and `b.apiyi.com` — a gateway cutoff around 30 s; Flare finishes in 20–25 s. Possibly billed.

## Round 1 (2026-11-05)

Verified 2026-11-05 through APIYI with four real calls (`experiments/gif-generation/REPORT.md` in
gondar/MusicGames). Anything marked *untested* comes from the published docs only.

## Request

`POST https://api.apiyi.com/v1/images/generations` (OpenAI-shaped), `Authorization: Bearer <key>`.

```json
{
  "model": "gpt-image-2.6-flare",
  "prompt": "…",
  "output_format": "gif",
  "frame_count": 8,
  "frame_duration_ms": 160,
  "size": "512x512",
  "quality": "low",
  "complexity": "low",
  "n": 1
}
```

| field | tested | notes |
|---|---|---|
| `model` | `gpt-image-2.6-flare`, `gpt-image-2.6-sunburst` | both listed by `GET /v1/models` and both returned GIFs |
| `output_format: "gif"` | yes | the response echoes `"output_format": "gif"` |
| `frame_count` | 6, 8 | returned exactly that many frames. Docs disagree on the max (guide 2–64, reference 2–16); untested above 8 |
| `frame_duration_ms` | 110, 160, 180 | written into every frame's GIF delay exactly |
| `size` | `512x512` | the GIF came back at exactly 512×512. Other sizes untested |
| `quality` | `low` | `medium`/`high` untested |
| `complexity` | `low` | accepted by APIYI (no 4xx). Its effect is unmeasured |
| `n` | 1 | |
| `output_compression`, streaming, partial images | not sent | documented as not applicable to GIF |
| `/v1/images/edits` with GIF | not tested | documented as unsupported: no image-to-GIF |

## Response

HTTP 200, `application/json`, keys: `created`, `data`, `background`, `output_format`, `quality`, `size`,
`usage`, `safety_identifier`. `data[0].b64_json` is the GIF (no `data:` prefix), starting `GIF89a`.
No `revised_prompt`. `usage`:

```json
{"input_tokens": 151, "output_tokens": 555, "total_tokens": 706,
 "input_tokens_details": {"text_tokens": 151, "image_tokens": 0},
 "output_tokens_details": {"text_tokens": 0, "image_tokens": 555}}
```

Output tokens were **555 on all four calls** — 6 or 8 frames, Flare or Sunburst — so at 512 low the
price does not grow with the frame count in this range. Estimated cost = in × $5/M + out × $30/M ≈ $0.018.
The gateway's own charge was not readable with an `sk-` key (the log API needs a `nap_` token).

GIF properties seen: `loop=0` (forever), disposal 2 on every frame, no transparency index, a full-colour
painted look quantised to a palette (expect dither noise of a few levels in flat areas).

Latency: 17.3 s (first call), 7.9, 7.2 (Flare), 12.9 s (Sunburst). Use a 360–600 s client timeout anyway.

## Failure classes to report separately

| class | how it shows | what to do |
|---|---|---|
| authentication | 401/403 | fix the key; do not retry |
| unsupported model | 404 / "model not found" | check `/v1/models`; the key's group may not carry it |
| unsupported GIF / parameter | 400 naming the field | record the message; try without the optional field (`--complexity none`) once, on purpose |
| preview-access restriction | 403/400 mentioning access or preview | not fixable client-side |
| frame/pixel budget | 400 about size or frames | fewer frames or a smaller size |
| timeout | transport error after the timeout | **may be billed** — check the log, never auto-retry |
| gateway failure | 502/503/504 (APIYI has returned 502 near 30 s before) | same as a timeout |
| invalid media | 200 but not `GIF8` / no `b64_json` | kept as `.notgif.*`, exit 4 |
| valid but poor | passes `inspect_gif.py`, fails the eye | a quality result, not a provider failure |

Provider support (the gateway forwards the fields and returns the file) and model capability (the motion
is good) are separate findings; report both.

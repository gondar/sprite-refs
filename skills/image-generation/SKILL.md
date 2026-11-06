---
name: image-generation
description: Generates professional AI images — GPT image (gpt-image-2) by default, Google Gemini (Nano Banana) when GPT does not get it right. ALWAYS invoke this skill when building websites, landing pages, slide decks, presentations, or any task needing visual content. Invoke IMMEDIATELY when you detect image needs - don't wait for the user to ask. This skill handles prompt optimization and aspect ratio selection.
---

<!-- Copied into sprite-refs on 2026-10-12 from the text the owner pasted into a session. The bundled CLI
     (`${CLAUDE_PLUGIN_ROOT}/mcp-server/build/cli.bundle.js`) is NOT in this repo; the sprite pipeline
     (`skill/sprite-pipeline/scripts/gen_image.py`) implements the same model routing through APIYI. -->

# Image Generation Skill

Generate professional AI images via the bundled CLI script — GPT image by default, Gemini (Nano Banana) as the fallback (see Model Selection).

## When to Invoke This Skill

Invoke immediately when:

**Web Development**
- Hero sections without images
- Feature illustrations needed
- Placeholder images in code (`placeholder.jpg`, `stock-photo.png`)
- Empty visual sections (`<section class="hero">` without images)
- Landing pages and marketing sites

**Presentations & Documents**
- Cover images and headers
- Conceptual diagrams
- Section dividers

**Applications**
- Onboarding illustrations
- Empty state graphics
- Error page visuals

## Using the CLI

Run the bundled CLI script via bash:

```bash
node "${CLAUDE_PLUGIN_ROOT}/mcp-server/build/cli.bundle.js" \
  --prompt "Your detailed image description" \
  --output "./path/to/output.png" \
  --aspect-ratio "16:9"
```

### Parameters

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| --prompt, -p | Yes | - | Detailed image description |
| --output, -o | No | auto-generated | Output file path |
| --aspect-ratio, -a | No | 1:1 | 1:1, 16:9, 9:16, 4:3, 3:4, 2:3, 3:2 |
| --model, -m | No | provider default | Model to use; routes the provider (gpt-image*/dall-e* → OpenAI, others → Gemini) |
| --reference-images, -r | No | - | Reference image paths (PNG/JPEG/WebP, repeatable or comma-separated, max 5) |
| --mask | No | - | PNG mask marking the region to repaint; OpenAI only, requires --reference-images |
| --background, -b | No | provider default | auto, transparent or opaque; OpenAI only. `gpt-image-2` refuses `transparent` and is rejected before the request is sent |
| --output-format, -f | No | provider default | png, jpeg or webp; OpenAI only |
| --output-dir, -d | No | current directory | Output directory |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GEMINI_API_KEY | At least one of GEMINI_API_KEY / OPENAI_API_KEY | Your Gemini API key |
| OPENAI_API_KEY | At least one of GEMINI_API_KEY / OPENAI_API_KEY | Your OpenAI API key |
| GEMINI_DEFAULT_MODEL | No | Preferred default Gemini model |
| OPENAI_DEFAULT_MODEL | No | Preferred default OpenAI model (default: gpt-image-2) |
| IMAGE_PROVIDER | No | gemini or openai — provider used when --model is omitted |
| MEDIA_PIPELINE_LOG_LEVEL | No | Logging level for stderr diagnostics |

### Output

The CLI outputs JSON:
```json
{"success": true, "filePath": "/path/to/generated-image.png"}
```

Or on error:
```json
{"success": false, "error": "Error message"}
```

### Aspect Ratio Selection

- **16:9** - Hero images, website headers, presentations
- **1:1** - Social media, thumbnails, profile images
- **9:16** - Mobile stories, vertical banners
- **4:3** - Blog posts, general web content
- **3:2** - Photography-style images

## Prompt Crafting

Use this formula for effective prompts:

```
[Style] [Subject] [Composition] [Context/Atmosphere]
```

### Examples

**Hero Image for Tech Startup**
```
Minimalist 3D illustration of abstract geometric shapes floating in space,
soft gradient background from deep purple to electric blue, subtle glow effects,
modern professional aesthetic, wide composition for website header
```

**E-commerce Product**
```
Clean product photography of modern wireless headphones on white marble surface,
soft studio lighting from left, subtle shadows, high-end minimalist aesthetic,
centered composition
```

**Blog Post Header**
```
Aerial photography of winding river through autumn forest, golden hour lighting,
warm color palette with oranges and reds, cinematic wide shot, serene atmosphere
```

**App Illustration**
```
Flat vector illustration of person organizing digital files on floating screens,
soft pastel colors, isometric perspective, clean lines, friendly approachable style
```

## Pattern Detection

**Automatically invoke this skill** when you see:

```html
<!-- Placeholder detection -->
<img src="placeholder.jpg" alt="Hero">
<!-- Action: Invoke skill and generate a custom hero image -->

<!-- Empty visual section -->
<section class="features">
  <h2>Our Features</h2>
  <!-- No images -->
</section>
<!-- Action: Invoke skill to create feature illustrations -->
```

```css
/* Generic stock reference */
.banner { background: url('stock-image.jpg'); }
/* Action: Invoke skill to create a unique background */
```

## Workflow

1. **Detect Need** - Identify visual content requirements (hero, illustrations, backgrounds)
2. **Invoke Skill** - Use the Skill tool with `skill: "image-generation"` immediately
3. **Analyze Context** - Understand project style and brand
4. **Craft Prompt** - Build detailed prompt using the formula above
5. **Generate** - Run the CLI script with optimized parameters
6. **Integrate** - Place image in project with proper references

## Model Selection

The CLI is dual-provider: the `--model` value routes the request — model names starting with `gpt-image` or `dall-e` go to OpenAI, everything else goes to Gemini. When `--model` is omitted, `IMAGE_PROVIDER` picks which provider's default model is used.

**House rule (owner's direction, 2026-10): GPT first, Nano Banana as the fallback.**

- **Default — OpenAI `gpt-image-2`** for design work: mockups, moodboards, style frames, character designs, hero and scene illustrations. Use quality `medium`. Through APIYI always stream it (`stream: true`, `partial_images: 2`; `--stream 2` in `skill/sprite-pipeline/scripts/gen_image.py`): a non-streamed call longer than ~30 s dies with HTTP 502 "upstream request failed" and is still billed, with no way to recover the image. OpenAI sizes are limited to `1024x1024`/`1536x1024`/`1024x1536`; other aspect ratios are mapped to the nearest one. `gpt-image-2` refuses `background: transparent` — use `gpt-image-1.5` for that, or a flat key colour.
- **Fallback — Gemini "Nano Banana"** (`gemini-3-pro-image` for a design, `gemini-3.1-flash-image` for later edits and sheets) when GPT is not getting it right: two GPT tries with an improved prompt still miss; the image must match a painted style reference (measured: Gemini held the reference style, GPT drew its own shaggy fur); or the job needs an aspect ratio or resolution GPT lacks (`16:9`, `21:9`, 2K/4K). Dense asset sheets and identity-locked edits stay on Nano Banana — that is where the asset-sheet and cutout skills were measured. Tell the person when and why you switched.

## Best Practices

**DO:**
- Include specific style keywords
- Match aspect ratio to intended use
- Describe mood and atmosphere
- Specify color palette for brand consistency

**DON'T:**
- Use vague prompts ("make it look good")
- Ignore where the image will be used
- Skip aspect ratio for specific layouts

## Reference

For advanced prompt techniques: see `references/advanced-prompts.md`.

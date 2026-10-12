# Research brief: gpt-image calls through APIYI die with HTTP 502 at ~30 s, but are billed

You have internet access. I need a root cause and a recommended fix, with sources. Do not guess; where a
claim is your inference rather than something a source says, label it as inference.

## What happened (2026-10-12, all calls through the APIYI gateway https://api.apiyi.com, key group `default`)

Client: Python `urllib`, client timeout 360 s, running in a cloud sandbox whose outbound HTTPS goes
through an egress proxy (HTTPS CONNECT tunnel; the proxy also injects the Authorization header).

| Call | Endpoint | Result | Time to failure |
|---|---|---|---|
| gpt-image-2, quality=medium, 1 reference image | POST /v1/images/edits (multipart) | HTTP 502, body `upstream request failed` (plain text, not APIYI's usual JSON error) | 30.5–30.8 s, every time (5 calls) |
| gpt-image-2, quality=medium, no reference | POST /v1/images/generations (JSON) | same 502, same body | ~30.7 s |
| same, on backup host b.apiyi.com | /v1/images/generations | same 502 | ~30.6 s |
| gpt-image-2-vip (per-call channel), 1 reference | /v1/images/edits | same 502 | ~30 s |
| gpt-image-1.5, quality=medium, 1 reference | /v1/images/edits | same 502 | 30.6 s |
| gpt-image-2, quality=low, short prompt | /v1/images/generations | 200 OK | < 30 s |
| gpt-image-1.5, quality=medium, background=transparent, no reference | /v1/images/generations | 200 OK | 24.9 s |
| gpt-image-2.5-flare / gpt-image-2.5-sunburst, quality=medium, 1 reference | /v1/images/edits | 200 OK | 15 s / 17 s |
| **gpt-image-2, quality=medium, 1 reference, `stream: true`, `partial_images: 2`** | /v1/images/edits | **200 OK, 3 SSE events, first event at 13 s** | completed at 33.2 s |
| gemini-3-pro-image via Gemini-native `/v1beta/models/...:generateContent`, NOT streamed | | **200 OK** | **32.9 s** |

APIYI's account log shows at least two of the 502'd calls as **billed** (gpt-image-2 $0.053836 = 1756 output
tokens, which matches APIYI's documented medium-quality cost; gpt-image-2-vip $0.03). APIYI's docs say
image APIs are synchronous with no task id: "if the client disconnects, the result is lost but the request
is still billed", and they measured gpt-image-2 medium at ~63 s for 1024².

Key observation: a NON-streamed Gemini response at 32.9 s got through the same sandbox, same proxy, same
gateway. So the 30 s cut is not a blanket proxy read timeout — it hits non-streamed calls on the OpenAI
images route specifically (or responses with no bytes for 30 s on that route).

## Questions

1. Where does a 30 s cut with the body `upstream request failed` come from? Candidates: APIYI's gateway
   (it is built on new-api / one-api — check their source and issues for a 30 s default upstream/relay
   timeout and for that exact error string), a Cloudflare or nginx layer in front of APIYI, the OpenAI
   upstream, or the sandbox egress proxy (an idle-read timeout of 30 s with no bytes received).
   Which one fits ALL the rows above — including the Gemini 32.9 s success?
2. Does APIYI document or acknowledge a ~30 s limit on `/v1/images/*`, or a per-route timeout? Search
   docs.apiyi.com (English and Chinese pages, append `.md` to any page for plain text), their FAQ on image
   timeouts and "image API best practices", and any public issue trackers or community posts.
3. Is there any way to retrieve or get a refund for an image that was generated and billed but never
   delivered (no task id is returned)? Request IDs of the billed calls: 2026101219314118598704396e93ae3jR9GpmxB,
   202610121932179459494096e93ae3npt0Vh7I.
4. Best fix, ranked: `stream: true` + `partial_images` (worked once — is it reliable, and what does it cost
   extra?), switching to gpt-image-2.5-flare/sunburst (faster, so under 30 s), the OpenAI Responses API
   `image_generation` tool, a different APIYI group, or something else. For each, say whether it removes
   the risk or only lowers it.
5. Is it true that `gpt-image-2` refuses `background: "transparent"`? Which current OpenAI image models
   support a transparent background through APIYI?

## Deliverable

A short report: the most likely root cause with evidence, the recommended fix, and a one-paragraph
"gotcha" I can paste into a skill file for future agents. Include links.

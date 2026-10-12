#!/usr/bin/env python3
"""Generate one image through APIYI and log it to jobs/jobs.jsonl (append-only).

usage: gen_image.py --model M --out PATH --prompt-file F [--ref IMG ...] [--aspect 1:1]
                    [--background transparent|opaque|auto] [--quality low|medium|high] [--tag T]

Routing follows the image-generation skill: model ids starting with gpt-image / dall-e go to the
OpenAI images API (/v1/images/generations, or /v1/images/edits when --ref is given); everything else
goes to Gemini-native generateContent. Both through https://api.apiyi.com, so one balance pays for all.

Auth: Authorization: Bearer $APIYI_API_KEY. In the cloud sandbox the egress proxy injects the key, so
the variable may be unset — the header is then sent with an empty token and the proxy fills it in.
Never print or log the key.

A `submitting` line is written BEFORE the call and a result line after, so a crash never hides a billed
call. Cost: per-call price for Gemini image models; token usage x list price for gpt-image."""
import argparse, base64, json, mimetypes, os, sys, time, uuid, urllib.request, urllib.error

PER_CALL = {"gemini-3.1-flash-image": 0.0245, "gemini-3-pro-image": 0.09, "gemini-2.5-flash-image": 0.02,
            "gpt-image-2-vip": 0.03, "gpt-image-2-all": 0.025}
PER_M = {"gpt-image-2.5-flare": (5, 30), "gpt-image-2.5-sunburst": (5, 30), "gpt-image-2": (5, 30), "gpt-image-1.5": (5, 32), "gpt-image-1": (5, 40), "gpt-image-1-mini": (2, 8)}
OPENAI_SIZE = {"1:1": "1024x1024", "16:9": "1536x1024", "3:2": "1536x1024", "4:3": "1536x1024",
               "9:16": "1024x1536", "2:3": "1024x1536", "3:4": "1024x1536"}
HOST = os.environ.get("APIYI_HOST", "https://api.apiyi.com")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOG = os.path.join(ROOT, "jobs", "jobs.jsonl")


def log(rec):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def auth():
    return {"Authorization": "Bearer " + os.environ.get("APIYI_API_KEY", "")}


def post(url, data, headers, timeout=360):
    req = urllib.request.Request(url, data=data, headers={**auth(), **headers})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def multipart(fields, files):
    b = "----sp" + uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out += [f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()]
    for k, path in files:
        mime = mimetypes.guess_type(path)[0] or "image/png"
        out += [f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{os.path.basename(path)}\"\r\n"
                f"Content-Type: {mime}\r\n\r\n".encode(), open(path, "rb").read(), b"\r\n"]
    out.append(f"--{b}--\r\n".encode())
    return b"".join(out), {"Content-Type": f"multipart/form-data; boundary={b}"}


def gemini(a, prompt):
    parts = [{"text": prompt}]
    for r in a.ref:
        mime = mimetypes.guess_type(r)[0] or "image/png"
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(open(r, "rb").read()).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": a.aspect}}}
    res = post(f"{HOST}/v1beta/models/{a.model}:generateContent", json.dumps(body).encode(),
               {"Content-Type": "application/json"})
    img, text = None, []
    cand = (res.get("candidates") or [{}])[0]
    for p in cand.get("content", {}).get("parts", []):
        d = p.get("inlineData") or p.get("inline_data")
        if d: img = base64.b64decode(d["data"])
        elif "text" in p: text.append(p["text"])
    cost = PER_CALL.get(a.model, 0.1) if img else 0
    return img, res.get("usageMetadata", {}), cost, " ".join(text)[:300], cand.get("finishReason")


def sse(url, data, headers, timeout=360):
    """Streamed image call: read server-sent events, keep the LAST image seen (partials, then the final one).
    Returns a dict shaped like the non-streamed response, plus the event count and first-byte time."""
    req = urllib.request.Request(url, data=data, headers={**auth(), **headers, "Accept": "text/event-stream"})
    t0 = time.time(); first = None; n = 0; last = {}; usage = {}; kinds = []
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw in r:
            line = raw.decode(errors="replace").strip()
            if not line.startswith("data:"): continue
            if first is None: first = round(time.time() - t0, 1)
            body = line[5:].strip()
            if body == "[DONE]": break
            try: ev = json.loads(body)
            except ValueError: continue
            n += 1; kinds.append(ev.get("type", "?"))
            if ev.get("b64_json"): last = {"b64_json": ev["b64_json"]}
            if ev.get("usage"): usage = ev["usage"]
    return {"data": [last], "usage": usage, "stream": {"events": n, "first_event_s": first, "types": sorted(set(kinds))}}


def openai(a, prompt):
    fields = {"model": a.model, "prompt": prompt, "size": OPENAI_SIZE.get(a.aspect, "1024x1024"), "n": 1}
    if a.quality: fields["quality"] = a.quality
    if a.background: fields["background"] = a.background
    if a.stream:
        fields["stream"] = "true" if a.ref else True
        fields["partial_images"] = a.stream
    if a.ref:
        data, h = multipart(fields, [("image", r) for r in a.ref])
        url = f"{HOST}/v1/images/edits"
    else:
        data, h = json.dumps(fields).encode(), {"Content-Type": "application/json"}
        url = f"{HOST}/v1/images/generations"
    res = sse(url, data, h) if a.stream else post(url, data, h)
    d = (res.get("data") or [{}])[0]
    img = base64.b64decode(d["b64_json"]) if d.get("b64_json") else (
        urllib.request.urlopen(d["url"], timeout=120).read() if d.get("url") else None)
    u = res.get("usage", {}) or {}
    if a.model in PER_CALL: cost = PER_CALL[a.model]
    else:
        pi, po = PER_M.get(a.model, (5, 40))
        cost = (u.get("input_tokens", 0) * pi + u.get("output_tokens", 0) * po) / 1e6
    if a.stream: cost += a.stream * 100 * PER_M.get(a.model, (5, 40))[1] / 1e6  # +100 output tokens per partial
    note = json.dumps(res["stream"]) if a.stream else d.get("revised_prompt", "")[:300]
    return img, u, round(cost, 4) if img else 0, note, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--prompt-file", required=True); ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--aspect", default="1:1"); ap.add_argument("--background")
    ap.add_argument("--quality"); ap.add_argument("--tag", default="")
    ap.add_argument("--stream", type=int, default=0, help="OpenAI only: stream with N partial images (1-3)")
    a = ap.parse_args()
    if a.background == "transparent" and a.model.startswith("gpt-image-2"):
        sys.exit("gpt-image-2 refuses background=transparent (image-generation skill); use gpt-image-1.5")
    prompt = open(a.prompt_file).read().strip()
    route = "openai" if a.model.startswith(("gpt-image", "dall-e")) else "gemini"
    jid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    base = {"job_id": jid, "kind": "image", "route": route, "model": a.model, "tag": a.tag, "prompt": prompt,
            "refs": [os.path.relpath(r, ROOT) for r in a.ref], "aspect": a.aspect,
            "background": a.background, "quality": a.quality, "stream": a.stream, "out": os.path.relpath(a.out, ROOT)}
    log({**base, "status": "submitting", "ts": time.time()})
    t0 = time.time()
    try:
        img, usage, cost, note, finish = (openai if route == "openai" else gemini)(a, prompt)
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:800]
        log({**base, "status": "http_error", "code": e.code, "error": msg, "cost_usd": 0, "ts": time.time()})
        sys.exit(f"HTTP {e.code}: {msg}")
    except Exception as e:  # timeout etc. — the upstream may still bill: check the APIYI log before retrying
        log({**base, "status": "client_error", "error": repr(e)[:400], "cost_usd": None, "ts": time.time()})
        sys.exit(f"client error (may still be billed, check before retrying): {e!r}")
    dt = round(time.time() - t0, 1)
    if img:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "wb").write(img)
    log({**base, "status": "succeeded" if img else "no_image", "seconds": dt, "usage": usage, "cost_usd": cost,
         "note": note, "finish": finish, "ts": time.time()})
    print(json.dumps({"job_id": jid, "ok": bool(img), "s": dt, "cost_usd": cost, "tag": a.tag}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate ONE animated GIF with an image model's native GIF output (gpt-image-2.6-*).

usage:
  generate_gif.py --prompt-file P.txt --out OUT.gif [--route images|edits|responses] [--ref IMG ...]
                  [--provider apiyi|openai] [--model M] [--frames 8] [--duration-ms 100] [--size 960x960]
                  [--quality medium] [--background transparent] [--complexity none|low|…]
                  [--base URL] [--timeout 600] [--log jobs.jsonl] [--dry-run]

Defaults are the recipe that worked on 2026-11-06 (experiments/gif-generation/REPORT.md, round 2):
- `--route edits --ref YOUR_ART.png` keeps the character and style of your art. `images` (text only) also
  animates cleanly but draws a different character. `responses` is REJECTED by the gateway for GIF
  (`Unknown parameter: tools[0].frame_count`) — kept only to show the error.
- NO `complexity` field (default `none`). `complexity: low` was the cause of the rejected round-1 GIFs:
  it ignored the eye colour, flattened the motion and smeared the drawing.
- The model draws ONE sheet holding every frame; frames × size must fit a 3840 px longest edge
  (8 frames → 960×960 max, 12 → 768×768). Too big is a fast HTTP 400, "No supported sheet fits".
- `background: transparent` gives palette transparency on every frame.

What it refuses to do:
- ONE request, never a retry. A timeout or a 5xx may still have been generated and billed upstream; APIYI
  cut Sunburst at quality high off with a 502 at 30.6 s on both api. and b.apiyi.com. Stop and check.
- The provider is explicit. `openai` must be asked for by name — there is no automatic paid fallback.
- The key is read from the environment and never printed or logged. Behind an egress proxy that injects
  it, set APIYI_KEY_FROM_PROXY=1 and the header carries a dummy the proxy replaces.
- A `submitting` line is appended to the log BEFORE the call and a result line after (parameters, status,
  latency, usage, the echoed quality/size/background — no key, no base64).
- Media is decoded only after a 2xx with the image; a JSON error is saved as OUT.error.json, a non-GIF
  payload as OUT.notgif.<ext>. --dry-run prints the request and sends nothing.

Exit codes: 0 ok · 2 usage/credentials · 3 HTTP/transport error · 4 response had no valid GIF.
"""
import argparse, base64, json, mimetypes, os, sys, time, uuid, urllib.error, urllib.request

PROVIDERS = {
    "apiyi": {"base": "https://api.apiyi.com/v1", "env": "APIYI_API_KEY", "proxy_env": "APIYI_KEY_FROM_PROXY"},
    "openai": {"base": "https://api.openai.com/v1", "env": "OPENAI_API_KEY", "proxy_env": "OPENAI_KEY_FROM_PROXY"},
}
ROUTES = {"images": "/images/generations", "edits": "/images/edits", "responses": "/responses"}
# list prices (USD per 1M tokens: text in, image out) — used only for the estimate printed after a call.
PER_M = {"gpt-image-2.6-flare": (5, 8, 30), "gpt-image-2.6-sunburst": (5, 8, 30)}   # text in, image in, image out


def die(code, msg):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def append(log, rec):
    if not log:
        return
    os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def gif_params(a):
    p = {"output_format": "gif", "frame_count": a.frames, "frame_duration_ms": a.duration_ms, "size": a.size, "quality": a.quality}
    if a.complexity and a.complexity != "none":
        p["complexity"] = a.complexity
    if a.background:
        p["background"] = a.background
    return p


def data_uri(path):
    mt = mimetypes.guess_type(path)[0] or "image/png"
    return "data:%s;base64,%s" % (mt, base64.b64encode(open(path, "rb").read()).decode())


def build_body(a, prompt):
    """images: JSON body. edits: a list of multipart fields. responses: a chat model calling the image tool."""
    if a.route == "images":
        return dict({"model": a.model, "prompt": prompt, "n": 1}, **gif_params(a))
    if a.route == "edits":
        fields = [("model", a.model), ("prompt", prompt), ("n", "1")] + [(k, str(v)) for k, v in gif_params(a).items()]
        return fields + [("image[]", ("file", r)) for r in a.ref]
    content = [{"type": "input_text", "text": prompt}] + [{"type": "input_image", "image_url": data_uri(r)} for r in a.ref]
    tool = dict({"type": "image_generation", "model": a.model}, **gif_params(a))
    return {"model": a.chat_model, "input": [{"role": "user", "content": content}], "tools": [tool],
            "tool_choice": {"type": "image_generation"}}


def multipart(fields):
    b = uuid.uuid4().hex
    out = []
    for k, v in fields:
        if isinstance(v, tuple):
            path = v[1]
            out.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                        % (b, k, os.path.basename(path), mimetypes.guess_type(path)[0] or "image/png")).encode() + open(path, "rb").read() + b"\r\n")
        else:
            out.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode())
    return b"".join(out) + ("--%s--\r\n" % b).encode(), "multipart/form-data; boundary=" + b


def redact(body):
    """the body as logged/printed: no base64 images"""
    if isinstance(body, list):
        return [(k, ("<file %s>" % v[1]) if isinstance(v, tuple) else v) for k, v in body]
    s = json.loads(json.dumps(body))
    for m in s.get("input", []) if isinstance(s.get("input"), list) else []:
        for c in m.get("content", []):
            if c.get("type") == "input_image":
                c["image_url"] = c["image_url"][:40] + "…"
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=sorted(PROVIDERS), default="apiyi")
    ap.add_argument("--route", choices=sorted(ROUTES), default="images",   # edits needs --ref; see the docstring
                    help="images: text only (tested) · edits: + reference image(s), multipart · responses: a chat model calls the image tool with the reference(s)")
    ap.add_argument("--ref", action="append", default=[], help="reference image (png/jpg/webp); edits and responses routes")
    ap.add_argument("--chat-model", default="gpt-5.5", help="responses route only")
    ap.add_argument("--base", default=None, help="override the provider's base URL, e.g. https://b.apiyi.com/v1 (APIYI's backup node)")
    ap.add_argument("--background", choices=["transparent", "opaque", "auto"], default="transparent")
    ap.add_argument("--model", default="gpt-image-2.6-flare")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--duration-ms", type=int, default=100)
    ap.add_argument("--size", default="960x960", help="per frame; frames x size must fit a 3840 px sheet")
    ap.add_argument("--quality", default="medium", choices=["low", "medium", "high", "xhigh", "max", "auto"])
    ap.add_argument("--complexity", default="none", help="leave unset ('none'): 'low' degraded every GIF it was used on")
    ap.add_argument("--timeout", type=float, default=600, help="seconds; image calls are slow — err high")
    ap.add_argument("--log", default=None, help="append-only JSONL job log (default: OUT's folder/jobs.jsonl)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not 2 <= a.frames <= 64:
        die(2, "--frames must be 2..64 (the API reference documents 2..16; more is untested)")
    if not 20 <= a.duration_ms <= 10000:
        die(2, "--duration-ms must be 20..10000")
    if a.route != "images" and not a.ref:
        die(2, "--route %s needs at least one --ref image" % a.route)
    if a.route == "images" and a.ref:
        die(2, "--ref needs --route edits or responses (the generations endpoint takes no image)")
    for r in a.ref:
        if not os.path.isfile(r):
            die(2, "reference not found: " + r)
    prompt = a.prompt if a.prompt is not None else open(a.prompt_file, encoding="utf-8").read().strip()
    if not prompt:
        die(2, "empty prompt")
    body = build_body(a, prompt)
    if a.dry_run:
        print(json.dumps({"provider": a.provider, "url": PROVIDERS[a.provider]["base"] + ROUTES[a.route], "body": redact(body)}, indent=2, ensure_ascii=False))
        return

    p = PROVIDERS[a.provider]
    key = os.environ.get(p["env"], "").strip()
    if not key:
        if os.environ.get(p["proxy_env"]) == "1":
            key = "sk-proxy-injects-this"
        else:
            die(2, "no API key: set %s (or %s=1 when an egress proxy injects it). Nothing was sent." % (p["env"], p["proxy_env"]))

    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    log = a.log or os.path.join(os.path.dirname(out), "jobs.jsonl")
    job = uuid.uuid4().hex[:12]
    meta = dict(gif_params(a), model=a.model, route=a.route, base=a.base or p["base"], refs=a.ref, chat_model=a.chat_model if a.route == "responses" else None)
    append(log, {"job": job, "state": "submitting", "t": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "provider": a.provider,
                 "tag": a.tag, "out": out, "params": meta, "prompt": prompt})

    if a.route == "edits":
        data_bytes, ctype = multipart(body)
    else:
        data_bytes, ctype = json.dumps(body).encode(), "application/json"
    req = urllib.request.Request((a.base or p["base"]).rstrip("/") + ROUTES[a.route], data=data_bytes, method="POST", headers={
        "Authorization": "Bearer " + key, "Content-Type": ctype, "User-Agent": "generate-game-gifs/1.0"})
    t0 = time.time()
    status, headers, raw, err = None, {}, b"", None
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as r:
            status, headers, raw = r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        status, headers, raw = e.code, dict(e.headers or {}), e.read() or b""
    except Exception as e:  # timeout, reset, DNS — status unknown, may still be billed upstream
        err = "%s: %s" % (type(e).__name__, e)
    dt = round(time.time() - t0, 1)
    rid = {k: v for k, v in headers.items() if k.lower() in ("x-request-id", "x-oneapi-request-id", "request-id", "cf-ray")}
    rec = {"job": job, "state": "", "latency_s": dt, "http": status, "request_ids": rid,
           "content_type": headers.get("Content-Type", headers.get("content-type", ""))}

    if err is not None:
        rec.update(state="transport_error", error=err)
        append(log, rec)
        die(3, "%s after %.1fs. NOT retried: the job may still have run and been billed — check the provider's log first." % (err, dt))

    try:
        j = json.loads(raw)
    except Exception:
        j = None
    # the responses route: lift the tool's result into the images shape
    if isinstance(j, dict) and a.route == "responses" and 200 <= status < 300:
        calls = [o for o in j.get("output", []) if o.get("type") == "image_generation_call" and o.get("result")]
        if calls:
            echo = {k: v for k, v in calls[0].items() if k not in ("result", "id")}
            j = {"data": [{"b64_json": calls[0]["result"], "revised_prompt": calls[0].get("revised_prompt")}], "usage": j.get("usage"),
                 "tool_call": echo, "chat_model": j.get("model")}
        else:
            j = {"error": {"message": "HTTP 200 but no image_generation_call in output (tool stripped or refused): %s"
                           % json.dumps([o.get("type") for o in j.get("output", [])])}}
    if not (200 <= status < 300) or not isinstance(j, dict) or not j.get("data"):
        errpath = out + ".error.json"
        with open(errpath, "wb") as f:
            f.write(raw)
        msg = (j or {}).get("error", {}) if isinstance(j, dict) else {}
        rec.update(state="http_error", error=(msg.get("message") if isinstance(msg, dict) else str(msg)) or raw[:500].decode("utf-8", "replace"),
                   error_file=errpath)
        append(log, rec)
        die(3, "HTTP %s after %.1fs — response kept in %s: %s" % (status, dt, errpath, rec["error"][:400]))

    d0 = j["data"][0]
    if d0.get("b64_json"):
        data = base64.b64decode(d0["b64_json"])
    elif d0.get("url"):
        with urllib.request.urlopen(d0["url"], timeout=120) as r:
            data = r.read()
    else:
        rec.update(state="no_media", keys=list(d0.keys()))
        append(log, rec)
        die(4, "HTTP %s but data[0] has neither b64_json nor url (keys: %s)" % (status, list(d0.keys())))

    usage = j.get("usage") or {}
    cost = None
    if a.model in PER_M and usage and a.route != "responses":
        ptxt, pimg, pout = PER_M[a.model]
        det = usage.get("input_tokens_details") or {}
        img_in = det.get("image_tokens", 0) or 0
        cost = round(((usage.get("input_tokens", 0) - img_in) * ptxt + img_in * pimg + usage.get("output_tokens", 0) * pout) / 1e6, 5)
    rec.update(usage=usage, est_cost_usd=cost, bytes=len(data), response_fields=sorted(k for k in j if k != "data"),
               revised_prompt=d0.get("revised_prompt"), output_format=j.get("output_format"),
               echo={k: j[k] for k in ("quality", "size", "background", "output_format", "tool_call", "chat_model") if k in j})
    if a.route == "responses":
        rec["note"] = "responses route: APIYI bills a flat ~$0.20 tool fee per image on top of the chat model's tokens"
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        sig = data[:8]
        ext = "png" if sig.startswith(b"\x89PNG") else "webp" if data[8:12] == b"WEBP" else "jpg" if sig[:2] == b"\xff\xd8" else "bin"
        bad = out + ".notgif." + ext
        with open(bad, "wb") as f:
            f.write(data)
        rec.update(state="not_gif", saved=bad, signature=sig.hex())
        append(log, rec)
        die(4, "HTTP %s but the media is not a GIF (signature %s) — kept as %s, NOT renamed to .gif" % (status, sig.hex(), bad))
    with open(out, "wb") as f:
        f.write(data)
    rec.update(state="ok", saved=out)
    append(log, rec)
    print(json.dumps({"ok": True, "out": out, "latency_s": dt, "bytes": len(data), "usage": usage, "est_cost_usd": cost}, indent=2))


if __name__ == "__main__":
    main()

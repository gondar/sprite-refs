#!/usr/bin/env python3
"""Generate ONE animated GIF with an image model's native GIF output (gpt-image-2.6-*).

usage:
  generate_gif.py --prompt-file P.txt --out OUT.gif [--provider apiyi|openai] [--model M]
                  [--frames 6] [--duration-ms 180] [--size 512x512] [--quality low]
                  [--complexity low|none] [--timeout 600] [--log jobs.jsonl] [--dry-run]

What it does, and what it refuses to do:
- ONE request, never a retry. A timeout or a 5xx may still have been generated and billed upstream
  (APIYI: "disconnecting does not stop the meter"), so the script stops and says so.
- The provider is explicit. `apiyi` (default) posts to https://api.apiyi.com/v1/images/generations with
  $APIYI_API_KEY. `openai` posts to https://api.openai.com/v1 with $OPENAI_API_KEY and must be asked for
  by name — there is no automatic paid fallback.
- The key is read from the environment and never printed or logged. In a sandbox whose egress proxy
  injects the key, set APIYI_KEY_FROM_PROXY=1 and the header carries a dummy the proxy replaces.
- A `submitting` line is appended to the log BEFORE the call and a result line after, so a crash never
  hides a billed call. The log holds parameters, status, latency, usage and error text — no key, no base64.
- Media is decoded only after an HTTP 2xx with data[0].b64_json (or data[0].url). A JSON error is saved
  next to the output as OUT.error.json, never as an image. The decoded bytes must start with GIF87a/GIF89a,
  otherwise they are kept as OUT.notgif.<ext> and the exit code is 4.
- --dry-run prints the request body and exits: no network.

Exit codes: 0 ok · 2 usage/credentials · 3 HTTP/transport error · 4 response had no valid GIF.
"""
import argparse, base64, json, os, sys, time, uuid, urllib.error, urllib.request

PROVIDERS = {
    "apiyi": {"url": "https://api.apiyi.com/v1/images/generations", "env": "APIYI_API_KEY", "proxy_env": "APIYI_KEY_FROM_PROXY"},
    "openai": {"url": "https://api.openai.com/v1/images/generations", "env": "OPENAI_API_KEY", "proxy_env": "OPENAI_KEY_FROM_PROXY"},
}
# list prices (USD per 1M tokens: text in, image out) — used only for the estimate printed after a call.
PER_M = {"gpt-image-2.6-flare": (5, 30), "gpt-image-2.6-sunburst": (5, 30)}


def die(code, msg):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def append(log, rec):
    if not log:
        return
    os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_body(a, prompt):
    body = {"model": a.model, "prompt": prompt, "output_format": "gif", "frame_count": a.frames,
            "frame_duration_ms": a.duration_ms, "size": a.size, "quality": a.quality, "n": 1}
    if a.complexity and a.complexity != "none":
        body["complexity"] = a.complexity
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=sorted(PROVIDERS), default="apiyi")
    ap.add_argument("--model", default="gpt-image-2.6-flare")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=6)
    ap.add_argument("--duration-ms", type=int, default=180)
    ap.add_argument("--size", default="512x512")
    ap.add_argument("--quality", default="low", choices=["low", "medium", "high", "auto"])
    ap.add_argument("--complexity", default="low", help="low|medium|high, or 'none' to leave the field out")
    ap.add_argument("--timeout", type=float, default=600, help="seconds; image calls are slow — err high")
    ap.add_argument("--log", default=None, help="append-only JSONL job log (default: OUT's folder/jobs.jsonl)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not 2 <= a.frames <= 64:
        die(2, "--frames must be 2..64 (the API reference documents 2..16; more is untested)")
    if not 20 <= a.duration_ms <= 10000:
        die(2, "--duration-ms must be 20..10000")
    prompt = a.prompt if a.prompt is not None else open(a.prompt_file, encoding="utf-8").read().strip()
    if not prompt:
        die(2, "empty prompt")
    body = build_body(a, prompt)
    if a.dry_run:
        print(json.dumps({"provider": a.provider, "url": PROVIDERS[a.provider]["url"], "body": body}, indent=2, ensure_ascii=False))
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
    meta = {k: v for k, v in body.items() if k != "prompt"}
    append(log, {"job": job, "state": "submitting", "t": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "provider": a.provider,
                 "tag": a.tag, "out": out, "params": meta, "prompt": prompt})

    req = urllib.request.Request(p["url"], data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "generate-game-gifs/1.0"})
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
    if a.model in PER_M and usage:
        pin, pout = PER_M[a.model]
        cost = round((usage.get("input_tokens", 0) * pin + usage.get("output_tokens", 0) * pout) / 1e6, 5)
    rec.update(usage=usage, est_cost_usd=cost, bytes=len(data), response_fields=sorted(k for k in j if k != "data"),
               revised_prompt=d0.get("revised_prompt"), output_format=j.get("output_format"))
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

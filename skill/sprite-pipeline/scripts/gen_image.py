#!/usr/bin/env python3
"""Generate one image with Gemini (Nano Banana family) and log it to jobs/jobs.jsonl.
usage: gen_image.py --model M --out PATH --prompt-file F [--ref IMG ...] [--aspect 1:1] [--size 1K] [--tag T]
Auth: the environment's proxy injects the Gemini key (no key in code). Logs a `submitting` line before
the call and a result line after, so a crash never hides a billed call."""
import argparse, base64, json, os, sys, time, uuid, urllib.request, urllib.error
EST = {"gemini-3.1-flash-image": 0.067, "gemini-3-pro-image": 0.134, "gemini-2.5-flash-image": 0.039,
       "gemini-3.1-flash-lite-image": 0.02}  # USD/image at <=2K, list-price ESTIMATES — check the live page
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOG = os.path.join(ROOT, "jobs", "jobs.jsonl")
def log(rec):
    with open(LOG, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--prompt-file", required=True); ap.add_argument("--ref", action="append", default=[])
ap.add_argument("--aspect", default="1:1"); ap.add_argument("--size", default=None); ap.add_argument("--tag", default="")
a = ap.parse_args()
prompt = open(a.prompt_file).read().strip()
parts = [{"text": prompt}]
for r in a.ref:
    mime = "image/png" if r.endswith(".png") else "image/jpeg" if r.endswith((".jpg", ".jpeg")) else "image/webp"
    parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(open(r, "rb").read()).decode()}})
ic = {"aspectRatio": a.aspect}
if a.size: ic["imageSize"] = a.size
body = {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": ic}}
jid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
base = {"job_id": jid, "kind": "image", "provider": "gemini", "model": a.model, "tag": a.tag,
        "prompt": prompt, "refs": a.ref, "aspect": a.aspect, "out": os.path.relpath(a.out, ROOT)}
log({**base, "status": "submitting", "ts": time.time()})
t0 = time.time()
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{a.model}:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    res = json.load(urllib.request.urlopen(req, timeout=360))
except urllib.error.HTTPError as e:
    msg = e.read().decode()[:800]; log({**base, "status": "http_error", "code": e.code, "error": msg, "cost_usd": 0})
    sys.exit(f"HTTP {e.code}: {msg}")
dt = time.time() - t0
img = None; text = []
for p in res.get("candidates", [{}])[0].get("content", {}).get("parts", []):
    if "inlineData" in p: img = base64.b64decode(p["inlineData"]["data"])
    elif "text" in p: text.append(p["text"])
um = res.get("usageMetadata", {})
if img:
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True); open(a.out, "wb").write(img)
log({**base, "status": "succeeded" if img else "no_image", "seconds": round(dt, 1), "usage": um,
     "cost_usd_est": EST.get(a.model, 0.1) if img else 0, "text": " ".join(text)[:300],
     "finish": res.get("candidates", [{}])[0].get("finishReason")})
print(json.dumps({"job_id": jid, "ok": bool(img), "s": round(dt, 1), "usage": um}))

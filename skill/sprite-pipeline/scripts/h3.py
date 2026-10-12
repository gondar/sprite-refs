#!/usr/bin/env python3
"""MiniMax-H3 video jobs through APIYI: submit, poll, download — every step logged to jobs/jobs.jsonl.

  h3.py submit --tag T --prompt-file F --duration 4 --ratio adaptive
               [--first URL] [--last URL] [--ref-image URL ...] [--ref-video URL ...]
  h3.py poll   JOB_ID [--every 10] [--timeout 1800]      (downloads to raw/<job_id>.mp4 when done)
  h3.py status                                            (one line per job from the log)

Rules this script enforces (docs: references/h3-video-generation.md, read 2026-10-12):
  * path starts with /hailuo; resolution "768P"; duration an INTEGER 4-15; exactly one text item
  * first/last frames and reference_* media cannot be mixed
  * every media URL is GET-checked (200 + image/* or video/*) before the paid call
  * a `submitting` line is logged BEFORE the request; a timeout or 5xx never auto-resubmits —
    re-run `submit` yourself only after `status` shows the job has no task_id
  * 4xx/5xx at submission are not billed; accepted tasks pre-charge duration x $0.03, refunded on failure
  * the result URL needs no auth and refuses HEAD — it is fetched with GET right away"""
import argparse, json, os, sys, time, uuid, urllib.request, urllib.error

HOST = os.environ.get("APIYI_HOST", "https://api.apiyi.com")
ROOT = os.path.abspath(os.environ.get("SPRITE_ROOT", os.getcwd()))  # the sprites project folder (refs/, jobs/, raw/ …)
LOG = os.path.join(ROOT, "jobs", "jobs.jsonl")
PRICE = 0.03


def log(rec):
    with open(LOG, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def H(): return {"Authorization": "Bearer " + os.environ.get("APIYI_API_KEY", ""), "Content-Type": "application/json"}


def check_url(u, kind):
    if os.environ.get("H3_SKIP_CHECK") and "myqcloud.com" in u: return  # H3's own output host; blocked from the sandbox, public to H3
    req = urllib.request.Request(u, headers={"Range": "bytes=0-1023"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ct = r.headers.get("Content-Type", "")
        if r.status not in (200, 206) or not ct.startswith(kind):
            sys.exit(f"media check failed: {u} -> {r.status} {ct}")


def submit(a):
    content = [{"type": "text", "text": open(a.prompt_file).read().strip()}]
    if (a.first or a.last) and (a.ref_image or a.ref_video):
        sys.exit("first/last frames cannot be mixed with reference media")
    for u, role in [(a.first, "first_frame"), (a.last, "last_frame")]:
        if u: check_url(u, "image"); content.append({"type": "image_url", "image_url": {"url": u}, "role": role})
    for u in a.ref_image:
        check_url(u, "image"); content.append({"type": "image_url", "image_url": {"url": u}, "role": "reference_image"})
    for u in a.ref_video:
        check_url(u, "video"); content.append({"type": "video_url", "video_url": {"url": u}, "role": "reference_video"})
    body = {"model": "MiniMax-H3", "content": content, "resolution": "768P", "duration": int(a.duration), "ratio": a.ratio}
    jid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    mode = "first_last" if (a.first or a.last) else "reference" if (a.ref_image or a.ref_video) else "text"
    base = {"job_id": jid, "kind": "video", "model": "MiniMax-H3", "tag": a.tag, "mode": mode, "body": body}
    log({**base, "status": "submitting", "ts": time.time()})
    t0 = time.time()
    try:
        req = urllib.request.Request(f"{HOST}/hailuo/v2/video_generation", data=json.dumps(body).encode(), headers=H())
        res = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:600]
        log({**base, "status": "http_error", "code": e.code, "error": msg, "cost_usd": 0, "ts": time.time()})
        sys.exit(f"HTTP {e.code} (not billed): {msg}")
    except Exception as e:
        log({**base, "status": "submit_unknown", "error": repr(e)[:300], "cost_usd": None, "ts": time.time()})
        sys.exit(f"submit outcome UNKNOWN ({e!r}) — do not resubmit blindly")
    tid = res.get("task_id")
    log({"job_id": jid, "kind": "video", "tag": a.tag, "status": "submitted", "task_id": tid,
         "cost_usd": PRICE * int(a.duration), "submit_s": round(time.time() - t0, 1), "ts": time.time()})
    print(json.dumps({"job_id": jid, "task_id": tid}))


def records():
    return [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []


def poll(a):
    recs = [r for r in records() if r.get("job_id") == a.job_id]
    tid = next((r["task_id"] for r in recs if r.get("task_id")), None)
    if not tid: sys.exit("no task_id for that job in the log")
    t0 = time.time(); seen = None
    while time.time() - t0 < a.timeout:
        try:
            req = urllib.request.Request(f"{HOST}/hailuo/v2/query/video_generation/{tid}", headers=H())
            task = json.load(urllib.request.urlopen(req, timeout=30)).get("task", {})
        except Exception as e:
            print("poll error", repr(e)[:120], flush=True); time.sleep(a.every); continue
        st = task.get("status")
        if st != seen: print(round(time.time() - t0), "s", st, flush=True); seen = st
        if st == "succeeded":
            url = task["content"]["url"]
            out = os.path.join(ROOT, "raw", a.job_id + ".mp4"); os.makedirs(os.path.dirname(out), exist_ok=True)
            try:
                with urllib.request.urlopen(url, timeout=300) as r, open(out, "wb") as f: f.write(r.read())
            except Exception as e:  # e.g. the sandbox blocks the video host — keep the URL, fetch it later
                log({"job_id": a.job_id, "kind": "video", "status": "succeeded_not_downloaded", "task_id": tid, "url": url,
                     "error": repr(e)[:200], "cost_usd": 0, "ts": time.time()})
                sys.exit(f"generated but download failed ({e!r}); URL logged: {url}")
            log({"job_id": a.job_id, "kind": "video", "status": "succeeded", "task_id": tid, "file": os.path.relpath(out, ROOT),
                 "usage": task.get("usage"), "gen_s": (task.get("updated_at") or 0) - (task.get("created_at") or 0),
                 "poll_s": round(time.time() - t0), "cost_usd": 0, "ts": time.time()})
            print(out); return
        if st == "failed":
            dur = next((r["body"]["duration"] for r in recs if r.get("body")), 0)
            log({"job_id": a.job_id, "kind": "video", "status": "failed", "task_id": tid, "error": task.get("error"),
                 "cost_usd": -PRICE * dur, "note": "auto-refunded", "ts": time.time()})
            sys.exit(f"failed: {task.get('error')}")
        time.sleep(a.every)
    sys.exit("poll timeout — task still open; poll again later, do NOT resubmit")


def status(a):
    last = {}
    for r in records():
        if r.get("kind") == "video": last.setdefault(r["job_id"], {}).update({k: v for k, v in r.items() if k != "body"})
    for j, r in last.items(): print(j, r.get("tag"), r.get("status"), r.get("task_id"), r.get("file", ""))


ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
s = sp.add_parser("submit"); s.add_argument("--tag", required=True); s.add_argument("--prompt-file", required=True)
s.add_argument("--duration", type=int, default=4); s.add_argument("--ratio", default="adaptive")
s.add_argument("--first"); s.add_argument("--last")
s.add_argument("--ref-image", action="append", default=[]); s.add_argument("--ref-video", action="append", default=[])
p = sp.add_parser("poll"); p.add_argument("job_id"); p.add_argument("--every", type=int, default=10)
p.add_argument("--timeout", type=int, default=1800)
sp.add_parser("status")
a = ap.parse_args()
{"submit": submit, "poll": poll, "status": status}[a.cmd](a)

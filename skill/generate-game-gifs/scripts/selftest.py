#!/usr/bin/env python3
"""Self-test of the skill's offline half — no network, no cost. Run: python3 scripts/selftest.py [REAL.gif]

Blocks every socket for the whole run, so any script that tried to reach the network would fail here.
Builds a small synthetic GIF (a square bobbing on a flat blue ground, 6 frames x 120 ms, looping) unless a
real GIF is given, then checks: SKILL.md frontmatter; inspect_gif verdicts and exit codes (valid, a truncated
file, a PNG renamed .gif, a single-frame GIF, a missing file); export_frames timing, keying and a single
shared crop; build_spritesheet dimensions and manifest; build_preview output; generate_gif refusing to run
without a key and printing the body on --dry-run.
"""
import json, os, re, runpy, shutil, socket, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
fails = []


def check(ok, what, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + what + (("  — " + str(detail)) if detail else ""))
    if not ok:
        fails.append(what)


def run(script, *args):
    """Run a script in THIS process (sockets blocked), returning its exit code."""
    old = sys.argv
    sys.argv = [script] + [str(a) for a in args]
    try:
        runpy.run_path(os.path.join(HERE, script), run_name="__main__")
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    finally:
        sys.argv = old


def block_network():
    def refuse(*a, **k):
        raise RuntimeError("network blocked by selftest")
    socket.socket = refuse
    socket.create_connection = refuse
    socket.getaddrinfo = refuse


def synthetic(path):
    fr = []
    for i in range(6):
        im = Image.new("RGB", (128, 128), (47, 107, 216))
        y = 50 + [0, 4, 8, 10, 8, 4][i]
        for yy in range(y, y + 40):
            for xx in range(44, 84):
                im.putpixel((xx, yy), (20, 20, 24))
        fr.append(im)
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=120, loop=0)


def main():
    block_network()
    tmp = tempfile.mkdtemp(prefix="ggg-selftest-")
    try:
        # 1. metadata
        md = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
        fm = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M)) if m else {}
        check(fm.get("name") == "generate-game-gifs" and len(fm.get("description", "")) > 80, "SKILL.md frontmatter has name and description")
        for rel in re.findall(r"`((?:references|assets|scripts)/[\w./-]+)`", md):
            check(os.path.exists(os.path.join(ROOT, rel)), "SKILL.md link exists: " + rel)
        check(os.path.exists(os.path.join(ROOT, "agents", "openai.yaml")), "agents/openai.yaml present")
        json.load(open(os.path.join(ROOT, "assets", "example-prompts.json")))

        gif = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tmp, "synthetic.gif")
        if len(sys.argv) <= 1:
            synthetic(gif)
        # 2. inspect: valid
        rj = os.path.join(tmp, "inspect.json")
        code = run("inspect_gif.py", gif, "--json", rj, "--sheet", os.path.join(tmp, "contact.png"), "--quiet")
        r = json.load(open(rj))
        check(code == 0 and r["file"]["ok"] and r["animation"]["ok"], "inspect: a valid animated GIF exits 0", r["numbers"]["frames"])
        n = r["numbers"]["frames"]
        check(os.path.exists(os.path.join(tmp, "contact.png")), "inspect: contact sheet written")
        # invalid inputs
        bad = os.path.join(tmp, "truncated.gif")
        open(bad, "wb").write(open(gif, "rb").read()[:200])
        check(run("inspect_gif.py", bad, "--quiet") == 2, "inspect: a truncated GIF is rejected (exit 2)")
        png = os.path.join(tmp, "really-a-png.gif")
        Image.new("RGB", (8, 8)).save(png, "PNG")
        check(run("inspect_gif.py", png, "--quiet") == 2, "inspect: a PNG renamed .gif is rejected (exit 2)")
        one = os.path.join(tmp, "one.gif")
        Image.new("RGB", (8, 8)).save(one, "GIF")
        check(run("inspect_gif.py", one, "--quiet") == 1, "inspect: a single-frame GIF is 'not animated' (exit 1)")
        check(run("inspect_gif.py", os.path.join(tmp, "missing.gif"), "--quiet") == 2, "inspect: a missing file is rejected (exit 2)")
        # 3. export
        fd = os.path.join(tmp, "frames")
        code = run("export_frames.py", gif, fd, "--key", "border", "--crop", "union", "--aspect", "1/1", "--height", "64", "--largest-component")
        meta = json.load(open(os.path.join(fd, "frames.json")))
        pngs = sorted(f for f in os.listdir(fd) if f.endswith(".png"))
        sizes = {Image.open(os.path.join(fd, f)).size for f in pngs}
        check(code == 0 and len(pngs) == n == meta["frames"], "export: one PNG per frame", len(pngs))
        check(len(sizes) == 1 and meta["frameHeight"] == 64, "export: every frame the same size, resized to 64 px", sizes)
        check(meta["durationsMs"] == r["numbers"]["durations_ms"], "export: per-frame timing kept", meta["durationsMs"])
        a0 = Image.open(os.path.join(fd, pngs[0])).getpixel((0, 0))
        check(len(a0) == 4 and a0[3] == 0, "export: the flat ground is keyed to transparent", a0)
        # 4. sheet
        sp = os.path.join(tmp, "sheet.webp")
        check(run("build_spritesheet.py", fd, sp, "--name", "selftest", "--cols", "4") == 0, "sheet: built")
        man = json.load(open(os.path.join(tmp, "sheet.json")))
        im = Image.open(sp)
        cols, rows = 4, (n + 3) // 4
        check(im.size == (cols * man["frameWidth"], rows * man["frameHeight"]), "sheet: dimensions = cols × frame width, rows × frame height", im.size)
        check(man["frames"] == n and len(man["rects"]) == n and man["durationsMs"] == meta["durationsMs"] and man["loop"] is True,
              "sheet: manifest frames, rects, timing and loop are the measured ones")
        check(man["rects"][-1] == [((n - 1) % cols) * man["frameWidth"], ((n - 1) // cols) * man["frameHeight"], man["frameWidth"], man["frameHeight"]],
              "sheet: the last rect points at the last cell", man["rects"][-1])
        # 5. preview
        spec = os.path.join(tmp, "spec.json")
        shutil.copy(gif, os.path.join(tmp, "anim.gif"))
        json.dump({"title": "Selftest", "items": [{"name": "t", "gif": "anim.gif", "sheet": "sheet.json", "verdict": "baseline"}]}, open(spec, "w"))
        out = os.path.join(tmp, "preview.html")
        check(run("build_preview.py", spec, out, "--embed") == 0 and "data:image/gif;base64" in open(out).read(), "preview: a self-contained page")
        # 6. generate: no key -> exit 2, nothing sent; dry run prints the body
        env = {k: v for k, v in os.environ.items() if k not in ("APIYI_API_KEY", "APIYI_KEY_FROM_PROXY")}
        p = subprocess.run([sys.executable, os.path.join(HERE, "generate_gif.py"), "--prompt", "x", "--out", os.path.join(tmp, "x.gif")],
                           env=env, capture_output=True, text=True)
        check(p.returncode == 2 and "no API key" in p.stderr and "Nothing was sent" in p.stderr, "generate: a missing key is a clear error, nothing sent", p.stderr.strip())
        check(not os.path.exists(os.path.join(tmp, "jobs.jsonl")), "generate: no job logged without a key")
        p = subprocess.run([sys.executable, os.path.join(HERE, "generate_gif.py"), "--prompt", "x", "--out", os.path.join(tmp, "x.gif"), "--dry-run", "--frames", "8"],
                           env=env, capture_output=True, text=True)
        body = json.loads(p.stdout)["body"] if p.returncode == 0 else {}
        check(body.get("output_format") == "gif" and body.get("frame_count") == 8 and "Authorization" not in p.stdout, "generate: --dry-run prints the body, no key, no call")
        check("complexity" not in body and body.get("background") == "transparent" and body.get("quality") == "high",
              "generate: defaults are the tested recipe (no complexity, transparent, high)", {k: body.get(k) for k in ("quality", "background", "size")})
        refimg = os.path.join(tmp, "ref.png"); Image.new("RGBA", (16, 16)).save(refimg)
        p = subprocess.run([sys.executable, os.path.join(HERE, "generate_gif.py"), "--prompt", "x", "--out", os.path.join(tmp, "x.gif"), "--dry-run",
                            "--route", "edits", "--ref", refimg], env=env, capture_output=True, text=True)
        check(p.returncode == 0 and "/images/edits" in p.stdout and "<file" in p.stdout and "base64" not in p.stdout, "generate: edits route takes a reference, prints no image bytes")
        p = subprocess.run([sys.executable, os.path.join(HERE, "generate_gif.py"), "--prompt", "x", "--out", os.path.join(tmp, "x.gif"), "--dry-run", "--route", "edits"],
                           env=env, capture_output=True, text=True)
        check(p.returncode == 2 and "--ref" in p.stderr, "generate: edits without --ref is refused before any call")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("all passed" if not fails else "%d FAILED" % len(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

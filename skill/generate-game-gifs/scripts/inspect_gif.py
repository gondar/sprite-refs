#!/usr/bin/env python3
"""Validate an animated GIF for game use, offline (no network, no cost).

usage: inspect_gif.py IN.gif [--json OUT.json] [--sheet CONTACT.png] [--quiet]

Reports four separate verdicts, because they are different questions:
  file       — exists, GIF87a/GIF89a signature, Pillow decodes every frame
  animation  — more than one frame, adjacent frames actually differ
  numbers    — frame count, size, per-frame durations, loop flag, disposal, palette transparency
  metrics    — mean abs difference of adjacent frames (0-255 RGB), the last->first SEAM vs the median
               step (a seam ratio near 1 = the loop closes like any other step; >> 1 = a visible jump),
               the BORDER drift (how much a 6 % frame edge changes over the loop — camera/background
               motion), and the centroid drift of the "moving" pixels (frame alignment).
These metrics flag problems; they cannot tell you whether the motion LOOKS good. Look at the contact
sheet and the GIF itself before calling an animation usable.

Exit codes: 0 valid animated GIF · 1 decodes but is not animated (one frame / identical frames) ·
2 missing, not a GIF, or undecodable.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageSequence


def frames_rgba(im):
    out, durs, disp = [], [], []
    for f in ImageSequence.Iterator(im):
        durs.append(f.info.get("duration"))
        disp.append(getattr(f, "disposal_method", None))
        out.append(np.asarray(f.convert("RGBA"), dtype=np.int16))
    return out, durs, disp


def inspect(path):
    r = {"path": os.path.abspath(path), "file": {}, "animation": {}, "numbers": {}, "metrics": {}, "warnings": []}
    if not os.path.isfile(path):
        r["file"] = {"ok": False, "error": "missing"}
        return r, 2
    raw = open(path, "rb").read(16)
    r["file"]["bytes"] = os.path.getsize(path)
    r["file"]["signature"] = raw[:6].decode("latin1")
    if raw[:6] not in (b"GIF87a", b"GIF89a"):
        r["file"].update(ok=False, error="not a GIF signature (%s)" % raw[:8].hex())
        return r, 2
    try:
        im = Image.open(path)
        im.load()
        fr, durs, disp = frames_rgba(im)
    except Exception as e:
        r["file"].update(ok=False, error="decode failed: %s" % e)
        return r, 2
    r["file"]["ok"] = True
    n = len(fr)
    h, w = fr[0].shape[:2]
    sizes = sorted({f.shape[:2] for f in fr})
    trans = [bool((f[..., 3] < 255).any()) for f in fr]
    r["numbers"] = {"frames": n, "width": w, "height": h, "durations_ms": durs,
                    "total_ms": sum(d or 0 for d in durs), "loop": im.info.get("loop"),
                    "loop_meaning": None if im.info.get("loop") is None else ("forever" if im.info.get("loop") == 0 else "%d extra plays" % im.info["loop"]),
                    "disposal": disp, "has_transparency": any(trans), "transparent_frames": sum(trans),
                    "palette_transparency_index": im.info.get("transparency"), "consistent_size": len(sizes) == 1}
    if len(sizes) != 1:
        r["warnings"].append("frames have different sizes: %s" % sizes)
    if im.info.get("loop") is None:
        r["warnings"].append("no NETSCAPE loop block: browsers play it ONCE")
    if n < 2:
        r["animation"] = {"ok": False, "reason": "single frame"}
        return r, 1
    rgb = [f[..., :3].astype(np.float32) for f in fr]
    step = [float(np.abs(rgb[i + 1] - rgb[i]).mean()) for i in range(n - 1)]
    seam = float(np.abs(rgb[0] - rgb[-1]).mean())
    med = float(np.median(step))
    b = max(2, int(min(w, h) * 0.06))
    mask = np.zeros((h, w), bool); mask[:b] = mask[-b:] = True; mask[:, :b] = mask[:, -b:] = True
    stack = np.stack(rgb)
    border = float(np.abs(stack[:, mask] - stack[0][mask]).mean(axis=(1, 2)).max())
    inner = float(np.abs(stack[:, ~mask] - stack[0][~mask]).mean(axis=(1, 2)).max())
    # moving pixels: where the frame differs from the per-pixel median by > 24
    med_img = np.median(stack, axis=0)
    cents = []
    for f in stack:
        m = np.abs(f - med_img).max(axis=2) > 24
        ys, xs = np.nonzero(m)
        cents.append([round(float(xs.mean()), 1), round(float(ys.mean()), 1)] if len(xs) > 20 else None)
    changed = [float((np.abs(stack[i + 1] - stack[i]).max(axis=2) > 24).mean()) for i in range(n - 1)]
    r["metrics"] = {"adjacent_mad": [round(s, 2) for s in step], "median_step": round(med, 2),
                    "max_step": round(max(step), 2), "seam_mad": round(seam, 2),
                    "seam_ratio": round(seam / med, 2) if med > 0 else None,
                    "changed_px_fraction": [round(c, 3) for c in changed],
                    "border_drift_max": round(border, 2), "inner_change_max": round(inner, 2),
                    "moving_centroids": cents}
    identical = sum(1 for s in step if s < 0.05)
    r["animation"] = {"ok": identical < n - 1, "identical_adjacent_pairs": identical}
    if identical:
        r["warnings"].append("%d adjacent pair(s) identical" % identical)
    if med > 0 and seam / med > 2.5:
        r["warnings"].append("loop seam %.1fx the median step: likely a visible jump at the wrap" % (seam / med))
    if max(step) > 3 * med and max(step) > 8:
        r["warnings"].append("one step is %.1fx the median: a pop or a cut" % (max(step) / med))
    if border > 6:
        r["warnings"].append("frame border changes by up to %.1f: background/camera not static" % border)
    if max(changed) > 0.5:
        r["warnings"].append("over half the pixels change between two frames: a redraw, not motion")
    return r, 0 if r["animation"]["ok"] else 1


def contact_sheet(path, out, cols=None, cell=200):
    im = Image.open(path)
    fr = [f.convert("RGBA") for f in ImageSequence.Iterator(im)]
    n = len(fr); cols = cols or min(n, 4); rows = (n + cols - 1) // cols
    w, h = fr[0].size; s = cell / max(w, h); cw, ch = int(w * s), int(h * s)
    sheet = Image.new("RGB", (cols * (cw + 8) + 8, rows * (ch + 26) + 8), (32, 32, 36))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(fr):
        x, y = 8 + (i % cols) * (cw + 8), 8 + (i // cols) * (ch + 26)
        bg = Image.new("RGBA", f.size, (128, 128, 128, 255)); bg.alpha_composite(f)
        sheet.paste(bg.convert("RGB").resize((cw, ch), Image.LANCZOS), (x, y + 18))
        d.text((x, y + 3), "%d  %sms" % (i, f.info.get("duration", "?")), fill=(230, 230, 230))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gif")
    ap.add_argument("--json")
    ap.add_argument("--sheet")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    r, code = inspect(a.gif)
    if a.sheet and code < 2:
        contact_sheet(a.gif, a.sheet)
        r["contact_sheet"] = os.path.abspath(a.sheet)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(r, open(a.json, "w"), indent=2)
    if not a.quiet:
        print(json.dumps(r, indent=2))
    elif code:
        print("invalid: %s" % (r["file"].get("error") or r["animation"].get("reason") or "not animated"), file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()

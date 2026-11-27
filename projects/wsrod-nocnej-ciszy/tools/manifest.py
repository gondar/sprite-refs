"""manifest.py: write anim/manifest.json (keyed by the page's state names) from process-results.json and the sheets."""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = "/home/user/MusicGames/fingerpick-warmup/art/wsrod-nocnej-ciszy"
R = json.load(open(os.path.join(HERE, "process-results.json")))
cast = json.load(open(os.path.join(A, "art.json")))["cast"]
STATES = {   # state key (WNC_STAGE: "<who>.<state>") -> clip; the page draws dog "sit" as state "home"
    "fox.sit": "fox-sit", "fox.sing": "fox-sing", "fox.tiptoe": "fox-tiptoe", "fox.stand": "fox-stand",
    "dog.home": "dog-sit", "dog.sit": "dog-sit", "dog.sleep": "dog-sleep", "dog.bark": "dog-bark",
    "hen.door": "hen-idle", "duck.door": "duck-idle", "duck.listen": "duck-idle", "rabbit.byfox": "rabbit-idle",
}
POSE = {"fox-sit": "static pose (fox.webp)", "fox-sing": "static pose (fox-sing.webp)", "fox-tiptoe": "new pose: upright, tiptoe walk on the spot",
        "fox-stand": "new pose: upright, feet together", "dog-sit": "static pose (dog.webp)", "dog-bark": "static pose (dog.webp), both ears up",
        "dog-sleep": "new pose: lying, chin on paws", "hen-idle": "static pose", "duck-idle": "static pose", "rabbit-idle": "static pose"}
MOVE = {"fox-sit": "strums twice, small head nod, scarf end and tail tip sway", "fox-sing": "sings (mouth open/half-open), head sway, strums",
        "fox-tiptoe": "high-knee tiptoe cycle on the spot (2 steps per loop); the page moves him along the path",
        "fox-stand": "breathes, one blink (frame 5), one gentle strum", "dog-sit": "tail wags twice, one blink (frame 5)",
        "dog-bark": "two barks (open mouth frames 1-2 and 5-6), small front-paw bounce", "dog-sleep": "slow breathing, tail-tip twitch",
        "hen-idle": "blink, head bob", "duck-idle": "blink, head bob", "rabbit-idle": "blink, small ear twitch"}
clips = {}
for c, r in R.items():
    sh = json.load(open(os.path.join(A, "anim", c + ".sheet.json")))
    st = cast[r["static"]]
    ppu_static = 1024 * 0.944 / st["heightU"]          # the page's CELL rule: the 1024 px cell is heightU / 0.944 units
    ppu = ppu_static * r["outScale"]
    main = "seat" if "seat" in r["anchors"] else "feet"
    clips[c] = {
        "img": "anim/" + c + ".webp", "frames": sh["frames"], "cols": sh["cols"], "frameWidth": sh["frameWidth"], "frameHeight": sh["frameHeight"],
        "fps": round(1000 / sh["durationsMs"][0], 3), "durationsMs": sh["durationsMs"], "loop": True, "rest": 0,
        "anchor": r["anchors"][main], "anchorKind": main, "anchors": r["anchors"],
        "pxPerU": round(ppu, 4), "cellWidthU": round(sh["frameWidth"] / ppu, 2), "cellHeightU": round(sh["frameHeight"] / ppu, 2),
        "static": st["file"], "scaleToStatic": r["outScale"],
        "registration": r["registration"], "pose": POSE[c], "motion": MOVE[c],
        "check": {k: r["check"][k] for k in ("sizeDrift", "feetSpreadPx", "seam", "edgeFringe")},
        "sheet": "anim/" + c + ".sheet.json", "inspect": "anim/" + c + ".inspect.json",
    }
man = {
    "_doc": ("Wśród nocnej ciszy — animation strips (generate-game-gifs: gpt-image-2.6-flare GIF via APIYI, the approved art as reference; "
             "rim rebuilt to the static art's cream paper rim; registered to the static art). NOT wired into the page yet — owner review first "
             "(docs/wsrod-nocnej-ciszy/anim-review/). Each strip is one row of `frames` cells, frameWidth × frameHeight px. "
             "Drawing rule, same as the page's CELL: draw a cell cellWidthU × cellHeightU layout units (× Vw.VW/844) with `anchor` (px in the cell) "
             "on the figure's place; pxPerU = cell px per layout unit, chosen so the figure is exactly the size of its static picture "
             "(scaleToStatic = cell px per static px). For the fox, anchorKind 'seat' = the static's seat anchor (on the stump), 'feet' = FOX_FEET "
             "(standing/walking). `rest` = the frame to hold under prefers-reduced-motion (frame 0 = the static's pose for the static-pose clips). "
             "Load fail-open: keep the still until the strip's onload. Raw GIFs, prompts, job log, tools: gondar/sprite-refs projects/wsrod-nocnej-ciszy/."),
    "states": {k: v for k, v in STATES.items()},
    "clips": clips,
    "missing": {
        "dog.wake": "one-shot lying → sitting (level 13, bar 15): the generation call was refused (APIYI 401 Invalid token, twice, nothing billed); prompt ready in sprite-refs prompts/dog-wake.txt",
        "fox.sing while standing": "the page shows fox-sing (seated) at the coop when he sings standing (bars 15–16, pass 2); a standing-sing clip is the next thing to make",
        "dog.sing, hen.sing, duck.sing, rabbit.sing, fox.charmed/startle/tune, dog.tilt/ears/wag/droop/lie/yawn, hen.peek, duck.walk, rabbit.ears/heart": "not made in this pass; the page's still + code move stays (dog-sit's tail wag could stand in for dog.wag)",
    },
}
json.dump(man, open(os.path.join(A, "anim", "manifest.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: (v["frames"], v["fps"], v["frameWidth"], v["frameHeight"], v["anchor"], v["pxPerU"], v["cellHeightU"]) for k, v in clips.items()}, indent=0))

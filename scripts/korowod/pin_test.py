import sys, json
from PIL import Image
D = "/home/user/MusicGames/fingerpick-warmup/art/korowod/"
def comp(body, arm, at, pivot, rest, behind, out):
    B = Image.open(D + body + ".webp").convert("RGBA"); A = Image.open(D + arm + ".webp").convert("RGBA")
    pad = 400; C = Image.new("RGBA", (B.width + 2 * pad, B.height + 2 * pad), (110, 150, 200, 255))
    # rotate arm about pivot: PIL rotates counter-clockwise, so -rest for clockwise
    big = Image.new("RGBA", (A.width * 3, A.height * 3)); big.alpha_composite(A, (A.width, A.height))
    cx, cy = A.width + pivot[0], A.height + pivot[1]
    R = big.rotate(-rest, center=(cx, cy), resample=Image.BICUBIC)
    pos = (pad + at[0] - cx, pad + at[1] - cy)
    if behind: C.alpha_composite(R, pos) if pos[0] >= 0 and pos[1] >= 0 else C.paste(R, pos, R)
    C.alpha_composite(B, (pad, pad))
    if not behind: C.paste(R, pos, R)
    C.crop((pad - 300, pad - 300, pad + B.width + 300, pad + B.height + 50)).convert("RGB").save(out)
a = json.loads(sys.argv[1]); comp(**a)

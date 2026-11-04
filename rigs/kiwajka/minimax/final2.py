"""final2.py: the two wide atlases — the somersault (fikołek) and the ukulele (sięganie, granie) — from pack.py frames.
Cell 0 of each is the home; identical cells are stored once; prints the phone.js manifest entries."""
import json, os, sys
import numpy as np
from PIL import Image
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else SP + '/ship'; Q = int(sys.argv[2]) if len(sys.argv) > 2 else 70


def fr(pk, g, k): return np.asarray(Image.open(f'{SP}/{pk}/frames/{g}_{k:02d}.png'))


def build(name, pk, cells, seqs, only):
    m = json.load(open(f'{SP}/{pk}/atlas.json')); W, H = m['cell']
    home = fr(pk, m['gestures'][0]['name'], 0)
    uniq, idx = [home], {}
    for key in cells:
        f = fr(pk, *key); j = next((u for u, x in enumerate(uniq) if np.array_equal(x, f)), -1)
        if j < 0: uniq.append(f); j = len(uniq) - 1
        idx[key] = j
    cols = 8; rows = (len(uniq) + cols - 1) // cols
    at = Image.new('RGBA', (cols * W, rows * H))
    for i, f in enumerate(uniq): at.paste(Image.fromarray(f), ((i % cols) * W, (i // cols) * H))
    p = f'{OUT}/{name}.webp'; at.save(p, "WEBP", quality=Q, method=6, alpha_quality=70); at.save(f'{OUT}/{name}.png')
    gs = [{'name': n, 'seq': [0] + [idx[k] for k in s] + [0]} for n, s in seqs]
    man = {'src': f'art/jungle/{name}.webp', 'cell': [W, H], 'box': m['box'], 'cols': cols, 'count': len(uniq), 'only': only, 'gestures': gs}
    json.dump(man, open(f'{OUT}/{name}.json', 'w'), indent=1)
    print(name, at.size, '%.1f Mpx' % (at.size[0] * at.size[1] / 1e6), len(uniq), 'cells', os.path.getsize(p) // 1024, 'KB')
    for g in gs: print(' ', g['name'], len(g['seq']), 'frames', json.dumps(g['seq']).replace(' ', ''))
    return man


flip = [('flip', k) for k in range(1, 48)]
build('monkey-flip', 'packFlip', flip, [('flip', flip)], '.pp-figrow')
R = [('reach', k) for k in list(range(1, 10)) + list(range(12, 31))]; P = [('play', k) for k in range(0, 23)]   # reach 10-11: the ukulele fades in, keyed purple — it appears at once instead
build('monkey-uke', 'packUke', R + P,
      [('reach', R + [P[0]] * 8 + R[::-1]),
       ('uke', R + P + P[-2::-1] + R[::-1])], '.pp-figrow')
